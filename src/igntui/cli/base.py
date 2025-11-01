#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import logging
import sys
from typing import List, Optional

from .. import __version__, get_version_string
from ..core.api import GitIgnoreAPI
from ..core.config import Config

logger = logging.getLogger(__name__)


class BaseCLI:
    def __init__(self):
        self.config = Config()
        self.api = GitIgnoreAPI()

    def setup_logging(self, verbose: bool = False):
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    def check_terminal_requirements(self) -> bool:
        try:
            import curses

            stdscr = curses.initscr()
            curses.endwin()
            return True
        except ImportError:
            print("Error: curses module not available.")
            print("On Windows, install: pip install windows-curses")
            return False
        except Exception as e:
            print(f"Error: Terminal not compatible with curses: {e}")
            return False

    def handle_api_error(self, error: Exception) -> None:
        if "connection" in str(error).lower() or "timeout" in str(error).lower():
            print("Error: Cannot connect to gitignore.io API")
            print("Please check your internet connection and try again.")
        elif "not found" in str(error).lower() or "404" in str(error):
            print("Error: Template not found")
            print("Use 'igntui list' to see available templates.")
        else:
            print(f"Error: {error}")

        logger.error(f"API error: {error}")


class CLICommand:
    def __init__(self, cli: BaseCLI):
        self.cli = cli

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        raise NotImplementedError

    def execute(self, args: argparse.Namespace) -> int:
        raise NotImplementedError


def create_base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="igntui",
        description="Interactive TUI for generating .gitignore files from gitignore.io templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  igntui                    # Launch interactive TUI
  igntui list               # List available templates  
  igntui generate python    # Generate .gitignore for Python
  igntui test               # Test API connection
  
For more information, visit: https://github.com/toptal/gitignore.io
        """,
    )

    parser.add_argument("--version", action="version", version=get_version_string())

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )

    return parser


def safe_exit(code: int = 0) -> None:
    try:
        import curses

        curses.endwin()
    except:
        pass

    sys.exit(code)
