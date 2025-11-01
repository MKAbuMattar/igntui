#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
from datetime import datetime

from ..base import CLICommand


class CacheCommand(CLICommand):
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        subparsers = parser.add_subparsers(dest="cache_action", help="Cache action")

        clear_parser = subparsers.add_parser("clear", help="Clear cache")
        clear_parser.add_argument(
            "--force", action="store_true", help="Skip confirmation prompt"
        )

        subparsers.add_parser("stats", help="Show cache statistics")
        subparsers.add_parser("info", help="Show cache information")

    def execute(self, args: argparse.Namespace) -> int:
        try:
            from ...core.cache import CacheManager
            from ...core.config import config

            cache_dir = config.get_cache_dir()
            cache = CacheManager(cache_dir=str(cache_dir))

            if not args.cache_action or args.cache_action == "info":
                return self._show_info(cache)
            elif args.cache_action == "stats":
                return self._show_stats(cache)
            elif args.cache_action == "clear":
                return self._clear_cache(
                    cache, args.force if hasattr(args, "force") else False
                )
            else:
                print(f"Unknown cache action: {args.cache_action}")
                return 1

        except Exception as e:
            print(f"Error managing cache: {e}")
            if hasattr(args, "verbose") and args.verbose:
                import traceback

                traceback.print_exc()
            return 1

    def _show_info(self, cache: "CacheManager") -> int:
        print("Cache Information:")
        print(f"  Location: {cache.cache_dir}")
        print(f"  TTL: {cache.default_ttl} seconds")

        try:
            from pathlib import Path

            template_cache_file = Path(cache.cache_dir) / "templates.json"
            if template_cache_file.exists():
                import json

                with open(template_cache_file, "r") as f:
                    data = json.load(f)
                    templates = data.get("templates", [])
                    print(f"  Template cache: Valid")
                    print(f"  Templates cached: {len(templates)}")
            else:
                print(f"  Template cache: Not found")
        except Exception as e:
            print(f"  Template cache: Error reading ({e})")

        return 0

    def _show_stats(self, cache: "CacheManager") -> int:
        stats = cache.get_stats()

        print("Cache Statistics:")
        for key, value in stats.items():
            if isinstance(value, datetime):
                value = value.strftime("%Y-%m-%d %H:%M:%S")
            print(f"  {key}: {value}")

        return 0

    def _clear_cache(self, cache: "CacheManager", force: bool = False) -> int:
        if not force:
            response = input("Clear cache? This will remove all cached data. (y/N): ")
            if response.lower() not in ["y", "yes"]:
                print("Cache clear cancelled")
                return 1

        cache.clear_all()
        print("Cache cleared successfully")
        return 0
