#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

from ..core.config import config


def setup_logging(verbose: bool = False, log_level: Optional[str] = None) -> None:
    if log_level:
        level = getattr(logging, log_level.upper(), logging.INFO)
    elif verbose:
        level = logging.DEBUG
    else:
        log_config = config.logging_config
        level = getattr(logging, log_config["level"].upper(), logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handlers = []

    log_config = config.logging_config
    if log_config["file_enabled"]:
        try:
            log_file = config.get_log_file()
            log_file.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=log_config["max_file_size"],
                backupCount=log_config["backup_count"],
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            handlers.append(file_handler)

        except (OSError, PermissionError) as e:
            print(f"Warning: Could not set up file logging: {e}")

    if log_config["console_enabled"] or not handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        handlers.append(console_handler)

    logging.basicConfig(level=level, handlers=handlers, force=True)

    logger = logging.getLogger(__name__)
    logger.debug(f"Logging configured at {logging.getLevelName(level)} level")


def check_curses_availability() -> bool:
    try:
        import curses

        return True
    except ImportError:
        return False


def print_curses_error() -> None:
    print("Error: curses module not available.")
    print("On Windows, install: pip install windows-curses")
    print("On Linux/Mac, curses should be included with Python.")
