#!/usr/bin/env python3


import argparse
import logging
import sys
from pathlib import Path

from ..core.api import GitIgnoreAPI
from ..core.config import Config
from ..core.repo_config import find_repo_config

logger = logging.getLogger(__name__)


class BaseCLI:
    def __init__(
        self,
        config_path: Path | None = None,
        no_cache: bool = False,
    ):
        repo_path = find_repo_config()
        self.config = Config(
            config_path=config_path,
            repo_config_path=repo_path,
        )
        self.repo_config_path = repo_path
        self.no_cache = no_cache
        self.api = GitIgnoreAPI()
        self.api.force_refresh_default = no_cache

    def setup_logging(self, verbose: bool = False):
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    def check_terminal_requirements(self) -> bool:
        try:
            import curses
            curses.initscr()
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


def safe_exit(code: int = 0) -> None:
    # Note: Don't call curses.endwin() here as curses.wrapper handles cleanup
    # Calling it multiple times causes "endwin() returned ERR" errors
    sys.exit(code)
