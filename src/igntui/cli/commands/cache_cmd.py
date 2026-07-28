#!/usr/bin/env python3


import argparse
from datetime import datetime
from typing import TYPE_CHECKING

from ..base import CLICommand

if TYPE_CHECKING:
    from ...core.cache import CacheManager


class CacheCommand(CLICommand):
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        subparsers = parser.add_subparsers(dest="cache_action", help="Cache action")

        clear_parser = subparsers.add_parser("clear", help="Clear cache")
        clear_parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
        clear_parser.add_argument(
            "--expired",
            action="store_true",
            help="Remove only entries past their TTL, keeping everything still valid",
        )

        subparsers.add_parser("stats", help="Show cache statistics")
        subparsers.add_parser("info", help="Show cache information")

    def execute(self, args: argparse.Namespace) -> int:
        try:
            # The manager the rest of the session uses. Constructing a fresh one
            # here reported the default TTL rather than the configured
            # `api.cache_ttl`, and re-read every cache file to do it.
            cache = self.cli.api.cache_manager

            if not args.cache_action or args.cache_action == "info":
                return self._show_info(cache)
            elif args.cache_action == "stats":
                return self._show_stats(cache)
            elif args.cache_action == "clear":
                if getattr(args, "expired", False):
                    return self._clear_expired(cache)
                return self._clear_cache(cache, args.force)
            else:
                print(f"Unknown cache action: {args.cache_action}")
                return 1

        except Exception as e:
            print(f"Error managing cache: {e}")
            if args.verbose:
                import traceback

                traceback.print_exc()
            return 1

    def _show_info(self, cache: "CacheManager") -> int:
        from datetime import datetime

        print("Cache Information:")
        print(f"  Location: {cache.cache_dir}")
        print(f"  TTL: {cache.default_ttl} seconds")

        cache_files = sorted(cache.cache_dir.glob("*.cache"))
        if not cache_files:
            print("  Cached entries: 0")
            return 0

        total_bytes = sum(f.stat().st_size for f in cache_files)
        mtimes = [f.stat().st_mtime for f in cache_files]
        oldest = datetime.fromtimestamp(min(mtimes)).strftime("%Y-%m-%d %H:%M:%S")
        newest = datetime.fromtimestamp(max(mtimes)).strftime("%Y-%m-%d %H:%M:%S")

        list_count = sum(1 for f in cache_files if f.stem == "gitignore_templates_list")
        content_count = sum(1 for f in cache_files if f.stem.startswith("gitignore_content_"))

        print(f"  Cached entries: {len(cache_files)}")
        print(f"    template list: {list_count}")
        print(f"    content blobs: {content_count}")
        print(f"  Total size: {total_bytes:,} bytes")
        print(f"  Oldest entry: {oldest}")
        print(f"  Newest entry: {newest}")
        return 0

    def _show_stats(self, cache: "CacheManager") -> int:
        stats = cache.get_stats()

        print("Cache Statistics:")
        for key, value in stats.items():
            if isinstance(value, datetime):
                value = value.strftime("%Y-%m-%d %H:%M:%S")
            print(f"  {key}: {value}")

        return 0

    def _clear_expired(self, cache: "CacheManager") -> int:
        """Sweep only what is past its TTL.

        Nothing prunes expired files on its own any more: reading every entry at
        startup to find them cost every command ~19 ms over a realistic cache.
        Re-requesting a template set overwrites its stale entry in place, so this
        is for sets that were cached once and never asked for again.
        """
        removed = cache.cleanup_expired()
        if removed:
            print(f"Removed {removed} expired {'entry' if removed == 1 else 'entries'}")
        else:
            print("No expired entries")
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
