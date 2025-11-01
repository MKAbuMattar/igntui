#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import sys

from ..base import CLICommand


class TestCommand(CLICommand):
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--timeout",
            type=int,
            default=10,
            help="Connection timeout in seconds (default: 10)",
        )

    def execute(self, args: argparse.Namespace) -> int:
        try:
            from ...core.api import GitIgnoreAPI

            print("Testing connection to gitignore.io API...")
            print(f"Timeout: {args.timeout} seconds")
            print()

            api = GitIgnoreAPI()

            print("Attempting to connect...", end="", flush=True)
            response = api.test_connection()

            if not response.success:
                print(" FAILED")
                print(f"Error: {response.error_message}")
                return 1

            print(" SUCCESS")
            print()

            print("API Response:")
            response_time = (
                response.response_time if response.response_time is not None else 0.0
            )
            print(f"  Response time: {response_time:.3f}s")
            print(f"  From cache: {'Yes' if response.from_cache else 'No'}")
            print(
                f"  Status code: {response.status_code if response.status_code else 'N/A'}"
            )

            print()
            print("✓ API is working correctly")
            return 0

        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user")
            return 1
        except Exception as e:
            print(f"\n\nError testing API: {e}")
            if hasattr(args, "verbose") and args.verbose:
                import traceback

                traceback.print_exc()
            return 1
