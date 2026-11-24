"""Make classic/Extended Subconverter output conform to the one canonical Mihomo design.

Standard backend emits static nodes. Extended backend emits named remote providers.
The converter cannot encode all Mihomo provider selection semantics; after conversion
this tool restores the canonical 24 groups and preserves only converter-produced nodes
or provider URLs. Fails visibly rather than silently changing policy.
"""
import argparse
import copy
import re
import os
import secrets
from pathlib import Path
import yaml
from .build_templates import ROOT, Dumper, stylize
from .providers import extract_providers, provider_entries


def read_yaml(path):
    out = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(out, dict):
        raise ValueError('Expected Mihomo YAML mapping (check converter URL/target)')
    return out


def prepare(converter_output, backend, source=None):
    base = copy.deepcopy(read_yaml(ROOT/'mihomo-native.yaml'))
    base['secret']=secrets.token_urlsafe(32)
    if source is not None:
        source_data=read_yaml(Path(source))
        original_secret=source_data.get('secret')
        if isinstance(original_secret,str) and original_secret:
            base['secret']=original_secret

    if backend == 'standard':
        nodes=converter_output.get('proxies')
        if not isinstance(nodes,list) or not nodes:
            raise ValueError('Standard output has no static proxies. Is target=clash and subscription valid?')
        names=[]
        for p in nodes:
            if not isinstance(p,dict) or not isinstance(p.get('name'),str):
                raise ValueError('Malformed converter proxy entry')
            names.append(p['name'])
        if len(set(names))!=len(names):
            raise ValueError('Duplicate proxy names in converted subscription; fix converter rename rules')
        group_names={group['name'] for group in base['proxy-groups']}
        if group_names.intersection(names):
            raise ValueError('Node name collides with policy group name')
        base.pop('proxy-providers',None)
        base['proxies']=nodes
        for group in base['proxy-groups']:
            if group.pop('include-all-providers',False):
                flt=group.pop('filter',None)
                exclude=group.pop('exclude-filter',None)
                if flt:
                    compiled=re.compile(flt)
                    matched=[name for name in names if compiled.search(name)]
                elif exclude:
                    compiled=re.compile(exclude)
                    matched=[name for name in names if not compiled.search(name)]
                else:
                    matched=list(names)
                if group['name']=='🚀 PROXY':
                    # Keep 13 grouped choices + DIRECT before raw nodes.
                    group['proxies']=list(group['proxies'])+[n for n in matched if n not in group['proxies']]
                else:
                    # Empty provider-derived groups cannot work as url-test/select.
                    group['proxies']=matched if matched else ['DIRECT']
    elif backend == 'extended':
        providers=converter_output.get('proxy-providers')
        if not isinstance(providers,dict):
            raise ValueError('Extended output does not contain proxy-providers. Supply provider:NAME,URL inputs.')
        base['proxy-providers']=provider_entries(extract_providers(converter_output))
        base.pop('proxies',None)
    else:
        raise ValueError('Invalid backend '+backend)
    return base


def save(path, data):
    if path.exists():
        raise FileExistsError('Refusing to overwrite existing output: '+str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            f.write('# PRIVATE converted Mihomo v3.2 profile; verify on target client.\n')
            yaml.dump(stylize(data),f,Dumper=Dumper,allow_unicode=True,sort_keys=False,width=10**7)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    assert read_yaml(path)==data


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--backend',choices=['standard','extended'],required=True)
    ap.add_argument('--input',required=True,help='Raw YAML returned by the selected Subconverter')
    ap.add_argument('--output',required=True,help='Final Mihomo config path (must not exist)')
    ap.add_argument('--source',help='Optional existing local YAML to preserve its controller secret')
    args=ap.parse_args(argv)
    input_path=Path(args.input).expanduser().resolve()
    output_path=Path(args.output).expanduser().resolve()
    if input_path==output_path:ap.error('Input/output must be different')
    data=prepare(read_yaml(input_path),args.backend,args.source)
    save(output_path,data)
    print('Converted Mihomo config created:',output_path)
    print('24 groups,',len(data.get('proxies',[])),'static nodes,',len(data.get('proxy-providers',{})),'remote providers')
    print('This file is private: do not publish subscription data or node passwords.')
