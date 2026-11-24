#!/usr/bin/env python3
"""Single command entry point for Mihomo templates and conversion."""

import sys

from lib import build_templates, convert_once, finalize_converted, providers, verify_delivery

USAGE = """Usage: python3 mihomo.py <command> [options]

Commands:
  build     Generate converter-base.yaml and both Subconverter INIs
  check     Check generated templates for drift without writing
  providers Import subscription providers from a YAML file or interactive input
  convert   Call a self-hosted Subconverter and finalize its output
  finalize  Finalize YAML already downloaded from a Subconverter
  verify    Run offline configuration and conversion checks

Use `python3 mihomo.py <command> --help` for command options.
"""


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ('-h', '--help'):
        print(USAGE, end='')
        return 0 if args else 2

    command, *options = args
    if command == 'build':
        build_templates.main(options)
    elif command == 'check':
        build_templates.main(['--check', *options])
    elif command == 'providers':
        providers.main(options)
    elif command == 'convert':
        convert_once.main(options)
    elif command == 'finalize':
        finalize_converted.main(options)
    elif command == 'verify':
        verify_delivery.main(options)
    else:
        raise SystemExit(f'Unknown command: {command}\n\n{USAGE}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
