#!/usr/bin/env python3


import argparse

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
            print("Testing connection to gitignore.io API...")
            print(f"Timeout: {args.timeout} seconds")
            print()

            # The CLI's own API handle, not a fresh one: building a second
            # GitIgnoreAPI here ignored `--config` and `--no-cache`, so the
            # command tested a different configuration than the one in use.
            print("Attempting to connect...", end="", flush=True)
            response = self.cli.api.test_connection()

            if not response.success:
                print(" FAILED")
                print(f"Error: {response.error_message}")
                return 1

            print(" SUCCESS")
            print()

            # test_connection() reports the probe's timing inside `data`, not on
            # the wrapper it returns — reading the wrapper printed 0.000s / N/A
            # every time, which made the one command whose job is diagnosing
            # latency useless.
            details = response.data if isinstance(response.data, dict) else {}
            response_time = details.get("response_time") or 0.0
            cache_stats = details.get("cache_stats") or {}

            print("API Response:")
            print(f"  Response time: {response_time:.3f}s")
            print(f"  Endpoint: {details.get('api_url', 'unknown')}")
            print(f"  From cache: {'Yes' if response.from_cache else 'No'}")
            print(f"  Cached entries: {cache_stats.get('disk_entries', 0)}")

            print()
            print("✓ API is working correctly")
            return 0

        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user")
            return 1
        except Exception as e:
            print(f"\n\nError testing API: {e}")
            if args.verbose:
                import traceback

                traceback.print_exc()
            return 1
