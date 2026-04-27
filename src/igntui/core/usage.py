"""Persistent usage tracker for the recently-used templates feature.

`config.behavior.max_recent_templates = 10` is honored here. The tracker
persists `~/.igntui.usage.toml` (TOML) with `[<template>] count, last_used`
and exposes `top(n)` for the Templates panel to pin recents to the top.

For one release window (v0.1.0) the legacy JSON file `~/.igntui_usage.json`
is auto-migrated to the new TOML path on first launch.
"""

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib  # type: ignore[import-not-found, no-redef]

import tomli_w

from .config import config

logger = logging.getLogger(__name__)

USAGE_FILENAME = ".igntui.usage.toml"
LEGACY_USAGE_FILENAME = ".igntui_usage.json"


@dataclass
class _Entry:
    count: int = 0
    last_used: float = 0.0


class UsageTracker:
    def __init__(self, path: Path | None = None):
        self.path = path or config.get_usage_file()
        self._entries: dict[str, _Entry] = {}
        self._migrate_legacy_if_present()
        self._load()

    def record(self, template: str) -> None:
        entry = self._entries.setdefault(template, _Entry())
        entry.count += 1
        entry.last_used = time.time()
        self._save()

    def top(self, n: int) -> list[str]:
        """Return the top-N templates ordered by `(count desc, last_used desc)`."""
        items = sorted(
            self._entries.items(),
            key=lambda kv: (-kv[1].count, -kv[1].last_used),
        )
        return [name for name, _ in items[:n]]

    def _migrate_legacy_if_present(self) -> None:
        """Convert ~/.igntui_usage.json → ~/.igntui.usage.toml (one-shot)."""
        if self.path.exists():
            return
        legacy = self.path.parent / LEGACY_USAGE_FILENAME
        if not legacy.is_file():
            return
        try:
            raw = json.loads(legacy.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Could not read legacy usage data %s: %s", legacy, e)
            return
        try:
            payload = {
                name: {
                    "count": int(p.get("count", 0)),
                    "last_used": float(p.get("last_used", 0.0)),
                }
                for name, p in raw.items()
                if isinstance(p, dict)
            }
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "wb") as f:
                tomli_w.dump(payload, f)
            logger.info(
                "Migrated usage data to %s. The legacy %s is no longer read; "
                "you may delete it.",
                self.path,
                legacy,
            )
        except OSError as e:
            logger.warning("Could not write migrated usage data: %s", e)

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            with open(self.path, "rb") as f:
                raw = tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError) as e:
            logger.warning("Failed to load usage data from %s: %s", self.path, e)
            return
        for name, payload in raw.items():
            if isinstance(payload, dict):
                self._entries[name] = _Entry(
                    count=int(payload.get("count", 0)),
                    last_used=float(payload.get("last_used", 0.0)),
                )

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                name: {"count": e.count, "last_used": e.last_used}
                for name, e in self._entries.items()
            }
            with open(self.path, "wb") as f:
                tomli_w.dump(payload, f)
        except OSError as e:
            logger.warning("Failed to save usage data to %s: %s", self.path, e)
