"""Synchronize 2 Subconverter templates from the canonical Mihomo YAML.

Canonical source of truth: mihomo-native.yaml. This script never reads personal
subscriptions. Run `python3 mihomo.py check` to detect drift.
Requires PyYAML.
"""
import argparse
import copy
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
NATIVE = ROOT / 'mihomo-native.yaml'

class FlowSeq(list): pass
class FlowMap(dict): pass
class BlockSeq(list): pass
class Dumper(yaml.SafeDumper): pass
Dumper.add_representer(FlowSeq, lambda d,x:d.represent_sequence('tag:yaml.org,2002:seq',x,flow_style=True))
Dumper.add_representer(FlowMap, lambda d,x:d.represent_mapping('tag:yaml.org,2002:map',x,flow_style=True))
Dumper.add_representer(BlockSeq, lambda d,x:d.represent_sequence('tag:yaml.org,2002:seq',x,flow_style=False))


def stylize(x, parent=None, key=None):
    if isinstance(x,dict):
        return (FlowMap if parent=='proxy-groups' else dict)((k,stylize(v,parent=k,key=k)) for k,v in x.items())
    if isinstance(x,list):
        cls = BlockSeq if key in ('proxy-groups','rules') else FlowSeq
        return cls(stylize(v,parent=key) for v in x)
    return x


def compact_yaml(data, header=''):
    text=yaml.dump(stylize(data),Dumper=Dumper,allow_unicode=True,sort_keys=False,width=10**7)
    assert yaml.safe_load(text)==data
    return header+text


def as_group_records(profile):
    lines=[]
    for g in profile['proxy-groups']:
        items=['[]'+x for x in g.get('proxies',[])]
        if g.get('include-all-providers'):
            # A converter does not support all Mihomo group flags. Normalization restores them.
            items.append(g.get('filter') or '.*')
        if not items:
            raise ValueError('Empty group '+g['name'])
        name,typ=g['name'],g['type']
        if typ=='url-test':
            url,interval,tol=g['url'],g.get('interval',300),g.get('tolerance',200)
            items += [url, f'{interval},5,{tol}']
        elif typ!='select':
            raise ValueError('Unsupported converter group '+typ)
        lines.append(f'custom_proxy_group={name}`{typ}`'+ '`'.join(items))
    return lines


def outputs_from(profile):
    base=copy.deepcopy(profile)
    for key in ('proxy-providers','proxy-groups','proxies'):
        base.pop(key,None)
    base_text=compact_yaml(base,'''
# Shared Mihomo v3.2 Subconverter base (generated from mihomo-native.yaml).
# Contains DNS, TUN, Rule Providers, rules. Do not edit this directly.
# Both converters reconstruct proxy-groups; mihomo.py convert/finalize restores
# the canonical selector/filter semantics.
'''.lstrip('\n'))
    preamble='''[custom]
; Generated from mihomo-native.yaml. Do not edit separately.
; For self-hosted converter: put INI at base/config/<name>.ini
; and converter-base.yaml at base/converter-base.yaml
; Rules are already in shared base; do not generate or overwrite rules.
enable_rule_generator=false
overwrite_original_rules=false
clash_rule_base=base/converter-base.yaml
'''
    custom='\n'.join(as_group_records(profile))+'\n'
    standard=preamble+'; Standard backend: source subscriptions expanded to static proxies.\n'+custom
    extended=preamble+'; Extended backend: use provider:NAME,URL sources for remote providers.\n'+custom
    return {ROOT/'converter-base.yaml':base_text,
            ROOT/'standard'/'subconverter-standard.ini':standard,
            ROOT/'extended'/'subconverter-extended.ini':extended}


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check',action='store_true',help='Fail if outputs would differ; do not modify any file')
    args=ap.parse_args(argv)
    canonical=yaml.safe_load(NATIVE.read_text(encoding='utf-8'))
    if len(canonical['proxy-groups'])!=24 or 'proxy-providers' in canonical or len(canonical['rule-providers'])!=23:
        raise ValueError('Canonical counts changed; review mihomo-native.yaml before rebuilding')
    expected=outputs_from(canonical)
    for path,content in expected.items():
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8')!=content:
                raise ValueError('Out-of-sync file: '+str(path))
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(content,encoding='utf-8')
        print(('CHECK' if args.check else 'WRITE'),path.relative_to(ROOT))
