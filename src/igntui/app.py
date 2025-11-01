#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import curses
import sys
from typing import Optional


def run_tui(show_splash: bool = True) -> int:
    try:
        from .tui import GitIgnoreTUI

        def main(stdscr):
            tui = GitIgnoreTUI(stdscr, show_splash=show_splash)
            return tui.run()

        exit_code = curses.wrapper(main)
        return exit_code if exit_code is not None else 0

    except ImportError as e:
        if "curses" in str(e):
            print("Error: curses module not available.")
            print("On Windows, install: pip install windows-curses")
            return 1
        else:
            raise
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Error running TUI: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run_tui())
