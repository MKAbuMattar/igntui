#!/usr/bin/env python3
# -*- coding: utf-8 -*-\


import argparse
from pathlib import Path
from typing import Optional

from .. import __description__, __version__, get_version_string


def create_base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="igntui",
        description=__description__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
igntui v{__version__} - Interactive GitIgnore Template User Interface

Examples:
  igntui                    # Launch interactive TUI
  igntui list               # List available templates  
  igntui generate python    # Generate .gitignore for Python
  igntui tui                # Explicitly launch TUI mode
  
For more information, visit: https://github.com/toptal/gitignore.io
        """,
    )

    parser.add_argument(
        "--version", "-v", action="version", version=get_version_string()
    )

    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose/debug output"
    )

    parser.add_argument(
        "--log-level",
        "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set specific logging level",
    )

    parser.add_argument(
        "--config", "-c", type=Path, help="Path to custom configuration file"
    )

    parser.add_argument(
        "--no-cache", action="store_true", help="Disable caching for this session"
    )

    return parser


def create_command_parser(
    base_parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    subparsers = base_parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available commands",
        help="Command to execute",
    )

    tui_parser = subparsers.add_parser(
        "tui",
        help="Launch interactive TUI (default)",
        description="Launch the interactive Terminal User Interface",
    )
    tui_parser.add_argument(
        "--no-splash", action="store_true", help="Skip the splash screen"
    )

    list_parser = subparsers.add_parser(
        "list",
        help="List available templates",
        description="List all available .gitignore templates",
    )
    list_parser.add_argument(
        "--filter", "-f", metavar="PATTERN", help="Filter templates by pattern"
    )
    list_parser.add_argument(
        "--count", "-c", action="store_true", help="Show count only"
    )

    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate .gitignore content",
        description="Generate .gitignore content for specified templates",
    )
    generate_parser.add_argument(
        "templates", nargs="+", help="Template names to generate (space-separated)"
    )
    generate_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        metavar="FILE",
        help="Output file path (default: stdout)",
    )
    generate_parser.add_argument(
        "--append",
        "-a",
        action="store_true",
        help="Append to existing file instead of overwriting",
    )
    generate_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force overwrite without confirmation",
    )

    cache_parser = subparsers.add_parser(
        "cache", help="Manage cache", description="Manage template and API cache"
    )
    cache_subparsers = cache_parser.add_subparsers(
        dest="cache_action", title="cache actions", help="Cache action to perform"
    )

    cache_subparsers.add_parser("clear", help="Clear all cache")
    cache_subparsers.add_parser("stats", help="Show cache statistics")
    cache_subparsers.add_parser("info", help="Show cache information")

    test_parser = subparsers.add_parser(
        "test",
        help="Test API connection",
        description="Test connection to gitignore.io API",
    )
    test_parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Connection timeout in seconds (default: 10)",
    )

    return base_parser


def get_command_instance(command_name: str, cli_instance):
    from .commands import (
        CacheCommand,
        GenerateCommand,
        ListCommand,
        TestCommand,
        TUICommand,
    )

    commands = {
        "list": ListCommand,
        "generate": GenerateCommand,
        "tui": TUICommand,
        "cache": CacheCommand,
        "test": TestCommand,
    }

    command_class = commands.get(command_name)
    if command_class:
        return command_class(cli_instance)

    return None
