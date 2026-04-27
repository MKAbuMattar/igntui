#!/usr/bin/env python3
"""User-level configuration loader.

Loads `~/.igntui.cfg.toml` by default. Honors environment overrides and
optional explicit `config_path`. For one release, also auto-migrates the
v0.0.x JSON file `~/.igntui.json` by reading it and writing TOML in place;
the legacy file is left on disk for the user to delete.
"""

import json
import logging
import os
import tomllib
from pathlib import Path
from typing import Any, TypedDict

import tomli_w

from .. import __version__

logger = logging.getLogger(__name__)

USER_CONFIG_FILENAME = ".igntui.cfg.toml"
LEGACY_USER_CONFIG_FILENAME = ".igntui.json"


class ApiConfig(TypedDict, total=False):
    base_url: str
    timeout: int
    user_agent: str
    cache_ttl: int
    retry_attempts: int


class UiConfig(TypedDict, total=False):
    theme: str
    mouse_support: bool
    auto_save: bool
    panel_layout: str
    show_help: bool
    animation_speed: int


class BehaviorConfig(TypedDict, total=False):
    max_recent_templates: int
    auto_refresh_interval: int
    fuzzy_search_threshold: float
    save_usage_stats: bool
    auto_backup: bool
    max_cache_entries: int


class LoggingConfig(TypedDict, total=False):
    level: str
    file_enabled: bool
    console_enabled: bool
    max_file_size: int
    backup_count: int


class IgntuiConfig(TypedDict, total=False):
    api: ApiConfig
    ui: UiConfig
    behavior: BehaviorConfig
    logging: LoggingConfig


class Config:
    DEFAULT_CONFIG: IgntuiConfig = {
        "api": {
            "base_url": "https://www.toptal.com/developers/gitignore/api",
            "timeout": 10,
            "user_agent": f"igntui/{__version__}",
            "cache_ttl": 3600,
            "retry_attempts": 3,
        },
        "ui": {
            "theme": "default",
            "mouse_support": True,
            "auto_save": False,
            "panel_layout": "four_panel",
            "show_help": True,
            "animation_speed": 150,
        },
        "behavior": {
            "max_recent_templates": 10,
            "auto_refresh_interval": 3600,
            "fuzzy_search_threshold": 0.6,
            "save_usage_stats": True,
            "auto_backup": True,
            "max_cache_entries": 1000,
        },
        "logging": {
            "level": "INFO",
            "file_enabled": True,
            "console_enabled": False,
            "max_file_size": 10485760,
            "backup_count": 5,
        },
    }

    def __init__(
        self,
        config_path: Path | None = None,
        repo_config_path: Path | None = None,
    ):
        self.config_path = config_path or Path.home() / USER_CONFIG_FILENAME
        self.repo_config_path = repo_config_path
        # The on-disk shape is documented by `IgntuiConfig` (above), but the
        # in-memory store is typed as `dict[str, Any]` so the recursive
        # descent in `get`/`set`/`_load_env_overrides` doesn't fight the
        # type checker. The TypedDict serves as documentation + the source
        # of truth for the section names.
        self._config: dict[str, Any] = {**self.DEFAULT_CONFIG}
        self._migrate_legacy_user_config_if_present()
        self._load_user_config()
        self._load_repo_config()
        self._load_env_overrides()

    def _migrate_legacy_user_config_if_present(self) -> None:
        """Convert ~/.igntui.json → ~/.igntui.cfg.toml (one-shot, on first launch)."""
        if self.config_path.exists():
            return
        legacy = Path.home() / LEGACY_USER_CONFIG_FILENAME
        if not legacy.is_file():
            return
        try:
            with open(legacy, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Could not read legacy user config %s: %s", legacy, e)
            return
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "wb") as f:
                tomli_w.dump(data, f)
            logger.info(
                "Migrated user config to %s. The legacy %s is no longer read; "
                "you may delete it.",
                self.config_path,
                legacy,
            )
        except OSError as e:
            logger.warning("Could not write migrated user config: %s", e)

    def _load_user_config(self) -> None:
        if not self.config_path.exists():
            return
        try:
            with open(self.config_path, "rb") as f:
                file_config = tomllib.load(f)
            self._merge_config(file_config)
            logger.info("Loaded configuration from %s", self.config_path)
        except (tomllib.TOMLDecodeError, OSError) as e:
            logger.warning("Failed to load config file: %s", e)

    def _load_repo_config(self) -> None:
        if self.repo_config_path is None:
            return
        try:
            with open(self.repo_config_path, "rb") as f:
                repo_data = tomllib.load(f)
        except (tomllib.TOMLDecodeError, OSError) as e:
            logger.warning("Failed to load repo config %s: %s", self.repo_config_path, e)
            return
        # Only the documented config sections override; [selection] is read by
        # the TUI/CLI separately to seed sidecars.
        for section in ("api", "ui", "behavior", "logging"):
            if section in repo_data and isinstance(repo_data[section], dict):
                self._merge_config({section: repo_data[section]})
        logger.info("Applied repo config from %s", self.repo_config_path)

    def _merge_config(self, new_config: dict[str, Any]) -> None:
        def merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
            result: dict[str, Any] = dict(base)
            for key, value in override.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = merge_dict(result[key], value)
                else:
                    result[key] = value
            return result

        self._config = merge_dict(self._config, new_config)

    def _load_env_overrides(self) -> None:
        env_mappings = {
            "IGNTUI_API_URL": ["api", "base_url"],
            "IGNTUI_API_TIMEOUT": ["api", "timeout"],
            "IGNTUI_CACHE_TTL": ["api", "cache_ttl"],
            "IGNTUI_THEME": ["ui", "theme"],
            "IGNTUI_MOUSE": ["ui", "mouse_support"],
            "IGNTUI_LOG_LEVEL": ["logging", "level"],
            "IGNTUI_MAX_RECENT": ["behavior", "max_recent_templates"],
        }

        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    if value.lower() in ("true", "false"):
                        value = value.lower() == "true"
                    elif value.isdigit():
                        value = int(value)
                    elif value.replace(".", "").isdigit():
                        value = float(value)

                    # Walk into the nested dict structure. Annotated as Any so
                    # the type checker doesn't try to narrow each step of the
                    # arbitrary-depth descent (TypedDict members carry varied types).
                    section: Any = self._config
                    for key in config_path[:-1]:
                        section = section[key]
                    section[config_path[-1]] = value

                    logger.debug(
                        "Set %s = %s from %s",
                        ".".join(config_path),
                        value,
                        env_var,
                    )
                except (ValueError, KeyError) as e:
                    logger.warning("Failed to set config from %s: %s", env_var, e)

    def get(self, *keys: str, default: Any = None) -> Any:
        # `value` is `Any` so the recursive subscript is unconstrained for the
        # type checker; runtime KeyError/TypeError handle missing paths.
        value: Any = self._config
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, *keys: str, value: Any) -> None:
        section: Any = self._config
        for key in keys[:-1]:
            if key not in section:
                section[key] = {}
            section = section[key]
        section[keys[-1]] = value

    def save(self) -> None:
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "wb") as f:
                tomli_w.dump(self._config, f)
            logger.info("Saved configuration to %s", self.config_path)
        except OSError as e:
            logger.error("Failed to save configuration: %s", e)

    def reset_to_defaults(self) -> None:
        self._config = {**self.DEFAULT_CONFIG}
        logger.info("Reset configuration to defaults")

    def get_cache_dir(self) -> Path:
        cache_dir = Path.home() / ".cache" / "igntui"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def get_log_file(self) -> Path:
        return Path.home() / ".igntui.log"

    def get_usage_file(self) -> Path:
        return Path.home() / ".igntui.usage.toml"

    @property
    def api_config(self) -> dict[str, Any]:
        return self._config["api"]

    @property
    def ui_config(self) -> dict[str, Any]:
        return self._config["ui"]

    @property
    def behavior_config(self) -> dict[str, Any]:
        return self._config["behavior"]

    @property
    def logging_config(self) -> dict[str, Any]:
        return self._config["logging"]


config = Config()
