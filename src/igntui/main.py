#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import sys
from typing import Optional

from .cli import (
    BaseCLI,
    create_base_parser,
    create_command_parser,
    get_command_instance,
    safe_exit,
)


def main() -> int:
    cli = BaseCLI()
    parser = create_base_parser()
    parser = create_command_parser(parser)
    args = parser.parse_args()

    if args.verbose:
        cli.setup_logging(verbose=True)

    command = args.command

    if command is None:
        command = "tui"
        args.no_splash = False

    command_instance = get_command_instance(command, cli)
    if command_instance is None:
        print(f"Error: Unknown command '{command}'")
        parser.print_help()
        return 1

    try:
        return command_instance.execute(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def cli_main() -> None:
    try:
        exit_code = main()
        safe_exit(exit_code)
    except Exception as e:
        print(f"Fatal error: {e}")
        safe_exit(1)


def tui_main() -> None:
    try:
        from .app import run_tui

        exit_code = run_tui(show_splash=True)
        safe_exit(exit_code)
    except Exception as e:
        print(f"Fatal error: {e}")
        safe_exit(1)


if __name__ == "__main__":
    cli_main()
