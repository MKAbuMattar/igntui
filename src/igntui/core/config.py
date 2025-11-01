#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .. import __version__

logger = logging.getLogger(__name__)


class Config:
    DEFAULT_CONFIG = {
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

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".igntui.json"
        self._config = self.DEFAULT_CONFIG.copy()
        self._load_config()

    def _load_config(self) -> None:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                self._merge_config(file_config)
                logger.info(f"Loaded configuration from {self.config_path}")
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load config file: {e}")

        self._load_env_overrides()

    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        def merge_dict(base: Dict, override: Dict) -> Dict:
            result = base.copy()
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

                    config_section = self._config
                    for key in config_path[:-1]:
                        config_section = config_section[key]
                    config_section[config_path[-1]] = value

                    logger.debug(
                        f"Set {'.'.join(config_path)} = {value} from {env_var}"
                    )
                except (ValueError, KeyError) as e:
                    logger.warning(f"Failed to set config from {env_var}: {e}")

    def get(self, *keys: str, default: Any = None) -> Any:
        try:
            value = self._config
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, *keys: str, value: Any) -> None:
        config_section = self._config
        for key in keys[:-1]:
            if key not in config_section:
                config_section[key] = {}
            config_section = config_section[key]
        config_section[keys[-1]] = value

    def save(self) -> None:
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, sort_keys=True)
            logger.info(f"Saved configuration to {self.config_path}")
        except OSError as e:
            logger.error(f"Failed to save configuration: {e}")

    def reset_to_defaults(self) -> None:
        self._config = self.DEFAULT_CONFIG.copy()
        logger.info("Reset configuration to defaults")

    def get_cache_dir(self) -> Path:
        cache_dir = Path.home() / ".cache" / "igntui"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def get_log_file(self) -> Path:
        return Path.home() / ".igntui.log"

    def get_usage_file(self) -> Path:
        return Path.home() / ".igntui_usage.json"

    @property
    def api_config(self) -> Dict[str, Any]:
        return self._config["api"]

    @property
    def ui_config(self) -> Dict[str, Any]:
        return self._config["ui"]

    @property
    def behavior_config(self) -> Dict[str, Any]:
        return self._config["behavior"]

    @property
    def logging_config(self) -> Dict[str, Any]:
        return self._config["logging"]


config = Config()
