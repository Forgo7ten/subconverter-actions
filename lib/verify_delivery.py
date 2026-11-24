"""Offline QA for the v3.2 delivery. No subscription access or network calls.

Tests canonical YAML, template drift, flow formatting, routing references,
provider selection, and both converter post-processing formats.
"""
import argparse
import copy
from pathlib import Path
import re
import tempfile
import yaml

from .build_templates import ROOT, outputs_from
from .providers import extract_providers, provider_entries, read_interactive, render_config, write_output
from .finalize_converted import prepare, save

ROOT_GROUPS=24
PROVIDERS=('00_personal','10_hneko','20_poke','30_mojie')


def check(c,condition,name):
    c.append((name,bool(condition)))
    if not condition:
        raise AssertionError(name)


def main(argv=None):
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    results=[]
    canonical=yaml.safe_load((ROOT/'mihomo-native.yaml').read_text(encoding='utf-8'))
    names=[g['name'] for g in canonical['proxy-groups']]
    check(results,len(names)==ROOT_GROUPS and len(names)==len(set(names)), '24 unique canonical groups')
    check(results,'proxy-providers' not in canonical,'canonical has no active subscription providers')
    check(results,list(canonical).index('rules') < list(canonical).index('rule-providers'),'rule providers follow rules')
    check(results,len(canonical['rule-providers'])==23 and len(canonical['rules'])==31,'23 rule providers and 31 rules')
    check(results,not any('pr0xy' in n.lower() for n in names),'no legacy pr0xy policy names')
    for row in canonical['rules']:
        bits=row.split(',')
        if bits[0]=='RULE-SET':
            check(results,bits[1] in canonical['rule-providers'],'rule provider reference '+bits[1])
            check(results,bits[2] in names or bits[2] in ('DIRECT','REJECT'),'rule group reference '+bits[2])
        if bits[0]=='GEOIP':
            check(results,bits[2] in names or bits[2] in ('DIRECT','REJECT'),'GEOIP route group '+bits[2])
        if bits[0]=='MATCH':
            check(results,bits[1] in names,'MATCH group')
    for g in canonical['proxy-groups']:
        for ref in g.get('proxies',[]):
            check(results,ref in names or ref in ('DIRECT','REJECT'),'group reference '+g['name'])
        if g.get('filter'): re.compile(g['filter'])
        if g.get('exclude-filter'): re.compile(g['exclude-filter'])
    group={g['name']:g for g in canonical['proxy-groups']}
    common=[g for g in names if g in ('🍎 苹果服务','🎮 游戏平台','🌐 国外可直连','🌐 宽泛PROXY')]
    check(results,all(len(group[g]['proxies'])==14 for g in common),'14 candidates in common business groups')
    check(results,len(group['🤖 AI 服务']['proxies'])==15,'15 candidates in AI group')
    check(results,group['🌐 宽泛PROXY']['proxies'][:2]==['🌍 国外流量','🎯 国内流量'],'broad proxy candidate order')
    check(results,group['🛑 广告拦截']['proxies']==['REJECT','DIRECT','🎯 国内流量','🌍 国外流量'],'advertising group candidate order')
    check(results,group['🐟 漏网之鱼']['proxies']==['DIRECT','🌍 国外流量','🎯 国内流量'],'MATCH group candidate order')
    check(results,group['🎯 国内流量']['proxies'][0]=='DIRECT','CN group defaults DIRECT')
    check(results,group['🌍 国外流量']['proxies'][0]=='🚀 PROXY','foreign group defaults total entry')
    check(results,[g['type'] for g in canonical['proxy-groups']]==['select']*16+['url-test']*8,'url-test groups follow selectors')
    check(results,len(group['♻️ 全局自动']['proxies'])==6 and len(group['🤖 AI 自动']['proxies'])==5,'nested AUTO group sizes')
    check(results,not any('香港' in x for x in group['🤖 AI 自动']['proxies']),'AI automatic excludes HK')
    check(results,group['🚀 PROXY']['include-all-providers'] is True,'total includes all providers')
    dns=canonical['dns']
    check(results,'+.cn' in dns['nameserver-policy'] and 'geosite:cn' in dns['nameserver-policy'],'CN DNS policy clauses')
    check(results,len(dns['nameserver'])>=2 and all('#🚀 PROXY' in str(u) for u in dns['nameserver']),'at least 2 foreign DoH use total group')
    check(results,'fallback' not in dns and 'direct-nameserver' not in dns,'no DNS fallback or direct-nameserver')
    check(results,len(dns['fake-ip-filter'])==96,'96 fake-IP exclusions retained')
    rows=canonical['rules']
    check(results,rows.index('RULE-SET,game_download,🎯 国内流量') < rows.index('RULE-SET,steam_cn,🎯 国内流量') < next(i for i,s in enumerate(rows) if s.startswith('RULE-SET,game,')),'GameDownload/SteamCN/Game order')
    check(results,'GEOIP,CN,🎯 国内流量,no-resolve' in rows,'CN GEOIP no-resolve')
    text=(ROOT/'mihomo-native.yaml').read_text(encoding='utf-8')
    gp=[line for line in text.splitlines() if line.startswith('- {name:')]
    check(results,sum(line.strip()=='interval: 86400' for line in text.splitlines())==23 and 'interval: 172800\n' not in text,'23 daily rule-provider refresh intervals')
    check(results,'# proxy-providers:\n' in text and '#     interval: 86400\n' in text,'commented provider template exists')
    check(results,len(gp)==24 and all(line.rstrip().endswith('}') for line in gp),'24 single-line group maps')
    ff=[l for l in text.splitlines() if 'fake-ip-filter:' in l and 'fake-ip-filter-mode' not in l]
    check(results,len(ff)==1 and ff[0].lstrip().startswith('fake-ip-filter: [') and ff[0].rstrip().endswith(']'),'fake-ip-filter array is single-line')
    # Verify converter base and both INIs are derived from the canonical profile.
    for path,expected in outputs_from(canonical).items():
        check(results,path.read_text(encoding='utf-8')==expected,'template sync '+path.name)
    # Build a test-only source with fake URLs. Never use a user's real URLs in QA.
    with tempfile.TemporaryDirectory(prefix='mihomo-v32-qa-') as td:
        target=Path(td)
        urls={name:'https://example.net/'+name+'/subscription' for name in PROVIDERS}
        old=copy.deepcopy(canonical)
        old['proxy-providers']=provider_entries(urls)
        old['secret']='test-only-secret'
        check(results,extract_providers(old)==urls,'source provider names and URLs extracted')
        answers=iter(['alpha','https://example.net/a','beta','https://example.net/b',''])
        check(results,read_interactive(lambda _prompt: next(answers))=={'alpha':'https://example.net/a','beta':'https://example.net/b'},'interactive provider pairs')
        source_path=target/'source.yaml'; source_path.write_text(yaml.safe_dump(old,allow_unicode=True))
        private_path=target/'native.yaml'
        write_output(private_path,render_config(urls))
        private=yaml.safe_load(private_path.read_text())
        check(results,(private_path.stat().st_mode&0o777)==0o600 and private['proxy-providers']==provider_entries(urls),'provider output mode and template')
        check(results,{k:v for k,v in private.items() if k!='proxy-providers'}==canonical,'provider output preserves canonical configuration')
        try:
            write_output(private_path,render_config(urls))
        except FileExistsError:
            check(results,True,'provider output cannot overwrite')
        else:
            check(results,False,'provider output cannot overwrite')
        static_nodes=[{'name':'🇺🇸 US Los Angeles 01','type':'socks5','server':'127.0.0.1','port':9801},
                      {'name':'🇭🇰 HK 01','type':'socks5','server':'127.0.0.1','port':9802},
                      {'name':'Australia 01','type':'socks5','server':'127.0.0.1','port':9803}]
        standard=prepare({'proxies':static_nodes},'standard',str(source_path))
        gs={g['name']:g for g in standard['proxy-groups']}
        check(results, len(standard['proxies'])==3 and 'proxy-providers' not in standard,'standard output static nodes only')
        check(results, gs['🇺🇸 美国 手动']['proxies']==['🇺🇸 US Los Angeles 01'],'standard regional matching')
        check(results, gs['🌐 其它地区 手动']['proxies']==['Australia 01'],'standard other-region exclusion')
        check(results, len(gs['🚀 PROXY']['proxies'])==17,'standard total group includes all static nodes')
        check(results, gs['🇹🇼 台湾 自动']['proxies']==['DIRECT'],'standard empty-region fallback')
        output=target/'standard.yaml';save(output,standard)
        check(results, yaml.safe_load(output.read_text())==standard,'standard output YAML roundtrip')
        converted_urls={n:'https://example.net/'+n+'/source' for n in PROVIDERS}
        extended=prepare({'proxy-providers':{n:{'url':u} for n,u in converted_urls.items()}},'extended',str(source_path))
        check(results,extended['proxy-providers']==provider_entries(converted_urls) and 'proxies' not in extended,'extended output dynamic providers')
        check(results,extended['proxy-groups']==canonical['proxy-groups'],'extended retains canonical provider selectors')
        custom=prepare({'proxy-providers':{'custom':{'url':'https://example.net/custom'}}},'extended')
        check(results,list(custom['proxy-providers'])==['custom'],'extended accepts source provider names')
        out=target/'extended.yaml';save(out,extended)
        check(results,yaml.safe_load(out.read_text())==extended,'extended output YAML roundtrip')
    print('Offline checks:',sum(ok for _,ok in results),'/',len(results),'PASS')
    print('Checked native structure, rule references, DNS separation, table invariants, compact formatting,')
    print('standard static-node normalization and extended provider-mode normalization.')
    print('NOT tested here: actual Subconverter engine compatibility, Mihomo core -t, real remote DNS / proxy network.')
