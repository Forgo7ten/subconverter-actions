"""Import subscription provider names and URLs into the native Mihomo template."""

import argparse
import os
from pathlib import Path
from urllib.parse import urlsplit

import yaml

from .build_templates import NATIVE

EXCLUDE_FILTER = '套餐到期|节点超时|必看官网|尽快更换|失联|使用教程|剩余流量'
START_MARKER = '# BEGIN PROXY PROVIDER TEMPLATE\n'
END_MARKER = '# END PROXY PROVIDER TEMPLATE\n'


def read_yaml(path):
    try:
        config = yaml.safe_load(Path(path).read_text(encoding='utf-8'))
    except yaml.YAMLError:
        raise ValueError('Source YAML could not be parsed') from None
    if not isinstance(config, dict):
        raise ValueError('Source YAML root must be a mapping')
    return config


def validate_pair(name, url):
    if (not isinstance(name, str) or not name or not name[0].isalnum()
            or any(not (ch.isalnum() or ch in '._-') for ch in name)):
        raise ValueError('Provider name must use letters, digits, dots, underscores or hyphens')
    if not isinstance(url, str) or any(ch.isspace() for ch in url):
        raise ValueError('Provider URL must be a valid HTTP or HTTPS URL')
    try:
        parts = urlsplit(url)
    except ValueError:
        raise ValueError('Provider URL must be a valid HTTP or HTTPS URL') from None
    if parts.scheme not in ('http', 'https') or not parts.netloc:
        raise ValueError('Provider URL must be a valid HTTP or HTTPS URL')
    return name, url


def extract_providers(config):
    providers = config.get('proxy-providers')
    if not isinstance(providers, dict) or not providers:
        raise ValueError('Source YAML has no proxy-providers')
    pairs = {}
    for name, item in providers.items():
        if not isinstance(item, dict):
            raise ValueError('Provider entry must be a mapping')
        name, url = validate_pair(name, item.get('url'))
        pairs[name] = url
    return pairs


def read_interactive(input_fn=input):
    pairs = {}
    while True:
        try:
            name = input_fn('Provider 名称（空行结束）: ').strip()
        except EOFError:
            break
        if not name:
            break
        if name in pairs:
            raise ValueError('Duplicate provider name: ' + name)
        try:
            url = input_fn('订阅 URL: ').strip()
        except EOFError:
            raise ValueError('Missing URL for provider: ' + name) from None
        name, url = validate_pair(name, url)
        pairs[name] = url
    if not pairs:
        raise ValueError('No providers entered')
    return pairs


def provider_entries(pairs):
    return {
        name: {
            'type': 'http',
            'url': url,
            'interval': 86400,
            'path': f'./proxy_providers/{name}.yaml',
            'health-check': {
                'enable': True,
                'interval': 100,
                'lazy': True,
                'url': 'https://www.gstatic.com/generate_204',
            },
            'exclude-filter': EXCLUDE_FILTER,
        }
        for name, url in (validate_pair(name, url) for name, url in pairs.items())
    }


def render_config(pairs, template=None):
    text = NATIVE.read_text(encoding='utf-8') if template is None else template
    if text.count(START_MARKER) != 1 or text.count(END_MARKER) != 1:
        raise ValueError('Native provider template markers are missing or duplicated')
    start = text.index(START_MARKER)
    end = text.index(END_MARKER, start) + len(END_MARKER)
    entries = provider_entries(pairs)
    block = yaml.safe_dump(
        {'proxy-providers': entries},
        allow_unicode=True,
        sort_keys=False,
        width=10**7,
    )
    rendered = text[:start] + block + text[end:]
    parsed = yaml.safe_load(rendered)
    if not isinstance(parsed, dict) or parsed.get('proxy-providers') != entries:
        raise ValueError('Generated provider block did not parse correctly')
    return rendered


def write_output(path, content):
    if path.exists():
        raise FileExistsError('Output already exists: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(content)
    except Exception:
        path.unlink(missing_ok=True)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sourcefile', help='Mihomo YAML whose provider names and URLs will be imported')
    parser.add_argument('--output', required=True, help='New complete Mihomo YAML path')
    args = parser.parse_args(argv)
    try:
        pairs = extract_providers(read_yaml(Path(args.sourcefile).expanduser())) if args.sourcefile else read_interactive()
        output = Path(args.output).expanduser().resolve()
        write_output(output, render_config(pairs))
    except (ValueError, FileNotFoundError, FileExistsError) as error:
        parser.error(str(error))
    print('Created Mihomo config:', output)
    print('Imported', len(pairs), 'providers. The output contains subscription URLs.')
