"""One command to call a self-hosted Subconverter and finalize its Mihomo YAML.

Requires PyYAML. The converter must be running and configured using the INI/base
files in this package. Subscription URLs are only sent to the specified converter.
"""
import argparse
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import build_opener, ProxyHandler
from .providers import read_yaml, extract_providers
from .finalize_converted import prepare, save
import yaml

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--backend',choices=['standard','extended'],required=True)
    ap.add_argument('--source',required=True,help='Existing Mihomo YAML with proxy-providers')
    ap.add_argument('--endpoint',default='http://127.0.0.1:25500',help='Self-hosted converter URL; do not use public services for private subscriptions')
    ap.add_argument('--output',required=True)
    args=ap.parse_args(argv)
    source=read_yaml(Path(args.source).expanduser())
    urls=extract_providers(source)
    if args.backend=='extended':
        url_items=['provider:'+name+','+url for name,url in urls.items()]
    else:
        url_items=list(urls.values())
    cfg='config/subconverter-'+args.backend+'.ini'
    base=args.endpoint.rstrip('/')+'/sub'
    target=base+'?'+urlencode({'target':'clash','url':'|'.join(url_items),'config':cfg})
    if urlsplit(args.endpoint).hostname not in ('127.0.0.1','localhost','::1'):
        print('WARNING: converter endpoint is not localhost; it will receive private subscription URLs.')
    opener=build_opener(ProxyHandler({}))
    try:
        with opener.open(target,timeout=120) as r:
            raw=r.read(35_000_000)
    except Exception as e:
        raise RuntimeError('Converter request failed. Check local server and installed INI/base files. '+str(e).split('?')[0]) from None
    result=yaml.safe_load(raw)
    if not isinstance(result,dict):
        raise ValueError('Converter did not return YAML. Check converter logs (do not share URLs).')
    data=prepare(result,args.backend,args.source)
    out=Path(args.output).expanduser().resolve()
    save(out,data)
    print('Success:',out)
    print('Generated',len(data.get('proxies',[])),'static nodes and',len(data.get('proxy-providers',{})),'providers.')
    print('Conversion complete. This private output contains subscription information.')
