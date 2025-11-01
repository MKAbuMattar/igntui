#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import platform
import sys

__version__ = "0.0.0"
__author__ = "Mohammad Abu Mattar"
__email__ = "info@mkabumattar.com"
__description__ = """A professional TUI application for generating .gitignore files from templates
provided by gitignore.io with advanced search, caching, and performance features.
"""


def get_version_string() -> str:
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    os_name = platform.system()
    os_version = platform.release()
    return f"igntui/{__version__} Python/{python_version} {os_name}/{os_version}"


from .core.api import GitIgnoreAPI, APIResponse
from .core.config import config
from .core.search import SearchManager, SearchMode
from .core.cache import CacheManager, TemplateCache

from .main import cli_main, tui_main

try:
    from .app import run_tui

    TUI_AVAILABLE = True
except ImportError:
    run_tui = None
    TUI_AVAILABLE = False

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__description__",
    "get_version_string",
    "GitIgnoreAPI",
    "APIResponse",
    "config",
    "SearchManager",
    "SearchMode",
    "CacheManager",
    "TemplateCache",
    "cli_main",
    "tui_main",
    "run_tui",
    "TUI_AVAILABLE",
]
