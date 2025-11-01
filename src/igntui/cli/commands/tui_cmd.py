#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse

from ..base import CLICommand


class TUICommand(CLICommand):
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--no-splash", action="store_true", help="Skip splash screen on startup"
        )

    def execute(self, args: argparse.Namespace) -> int:
        if not self.cli.check_terminal_requirements():
            return 1

        try:
            from ...app import run_tui

            return run_tui(show_splash=not args.no_splash)

        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return 1
        except Exception as e:
            print(f"Error launching TUI: {e}")
            if hasattr(args, "verbose") and args.verbose:
                import traceback

                traceback.print_exc()
            return 1
