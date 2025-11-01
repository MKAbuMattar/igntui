#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse

from ..base import CLICommand


class ListCommand(CLICommand):
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--filter", "-f", metavar="PATTERN", help="Filter templates by pattern"
        )
        parser.add_argument(
            "--count", "-c", action="store_true", help="Show count only"
        )

    def execute(self, args: argparse.Namespace) -> int:
        try:
            if hasattr(args, "verbose") and args.verbose:
                print("Fetching templates from gitignore.io...")

            response = self.cli.api.list_templates()

            if not response.success:
                print(f"Error: {response.error_message}")
                return 1

            templates = response.data

            if hasattr(args, "filter") and args.filter:
                pattern = args.filter.lower()
                templates = [t for t in templates if pattern in t.lower()]

            if hasattr(args, "count") and args.count:
                print(f"Found {len(templates)} templates")
                return 0

            if not templates:
                if hasattr(args, "filter") and args.filter:
                    print(f"No templates found matching '{args.filter}'")
                else:
                    print("No templates found")
                return 1

            print(f"Available templates ({len(templates)}):")
            print()

            max_width = 80
            col_width = max(len(t) for t in templates) + 2
            cols = max(1, max_width // col_width)

            for i, template in enumerate(templates):
                print(f"{template:<{col_width}}", end="")
                if (i + 1) % cols == 0:
                    print()

            if len(templates) % cols != 0:
                print()

            return 0

        except Exception as e:
            self.cli.handle_api_error(e)
            return 1
