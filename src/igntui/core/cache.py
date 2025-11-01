#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    data: Any
    timestamp: float
    ttl: int
    access_count: int = 0
    last_access: Optional[float] = None

    def is_expired(self) -> bool:
        return time.time() > (self.timestamp + self.ttl)

    def touch(self) -> None:
        self.access_count += 1
        self.last_access = time.time()


class CacheManager:
    def __init__(self, cache_dir: str, default_ttl: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._lock = RLock()

        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0,
            "disk_reads": 0,
            "disk_writes": 0,
        }

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._load_persistent_cache()

        logger.debug(f"Initialized cache manager with directory: {self.cache_dir}")

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._memory_cache:
                entry = self._memory_cache[key]

                if entry.is_expired():
                    del self._memory_cache[key]
                    self._delete_disk_cache(key)
                    self._stats["evictions"] += 1
                    self._stats["misses"] += 1
                    return None

                entry.touch()
                self._stats["hits"] += 1
                logger.debug(f"Cache hit for key: {key}")
                return entry.data

            disk_entry = self._load_disk_cache(key)
            if disk_entry and not disk_entry.is_expired():
                self._memory_cache[key] = disk_entry
                disk_entry.touch()
                self._stats["hits"] += 1
                logger.debug(f"Disk cache hit for key: {key}")
                return disk_entry.data
            elif disk_entry:
                self._delete_disk_cache(key)
                self._stats["evictions"] += 1

            self._stats["misses"] += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl or self.default_ttl

        with self._lock:
            entry = CacheEntry(data=value, timestamp=time.time(), ttl=ttl)

            self._memory_cache[key] = entry
            self._save_disk_cache(key, entry)
            self._stats["sets"] += 1

            logger.debug(f"Cached value for key: {key} (TTL: {ttl}s)")

    def delete(self, key: str) -> bool:
        with self._lock:
            deleted = False

            if key in self._memory_cache:
                del self._memory_cache[key]
                deleted = True

            if self._delete_disk_cache(key):
                deleted = True

            if deleted:
                self._stats["deletes"] += 1
                logger.debug(f"Deleted cache entry: {key}")

            return deleted

    def clear(self) -> int:
        with self._lock:
            memory_count = len(self._memory_cache)
            self._memory_cache.clear()
            disk_count = 0
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                    disk_count += 1
                except OSError:
                    pass

            total_cleared = memory_count + disk_count
            logger.info(f"Cleared {total_cleared} cache entries")
            return total_cleared

    def cleanup_expired(self) -> int:
        with self._lock:
            expired_keys = []

            for key, entry in self._memory_cache.items():
                if entry.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                del self._memory_cache[key]
                self._delete_disk_cache(key)

            disk_cleaned = 0
            for cache_file in self.cache_dir.glob("*.cache"):
                key = cache_file.stem
                if key not in self._memory_cache:
                    entry = self._load_disk_cache(key)
                    if entry and entry.is_expired():
                        cache_file.unlink()
                        disk_cleaned += 1

            total_cleaned = len(expired_keys) + disk_cleaned
            self._stats["evictions"] += total_cleaned

            if total_cleaned > 0:
                logger.info(f"Cleaned up {total_cleaned} expired cache entries")

            return total_cleaned

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / max(1, total_requests)

            memory_entries = len(self._memory_cache)
            disk_entries = len(list(self.cache_dir.glob("*.cache")))

            return {
                "hit_rate": hit_rate,
                "total_requests": total_requests,
                "memory_entries": memory_entries,
                "disk_entries": disk_entries,
                "cache_dir": str(self.cache_dir),
                "default_ttl": self.default_ttl,
                **self._stats,
            }

    def _load_persistent_cache(self) -> None:
        try:
            loaded_count = 0
            for cache_file in self.cache_dir.glob("*.cache"):
                key = cache_file.stem
                entry = self._load_disk_cache(key)

                if entry and not entry.is_expired():
                    self._memory_cache[key] = entry
                    loaded_count += 1
                elif entry:
                    cache_file.unlink()

            if loaded_count > 0:
                logger.info(f"Loaded {loaded_count} cache entries from disk")

        except Exception as e:
            logger.warning(f"Failed to load persistent cache: {e}")

    def _load_disk_cache(self, key: str) -> Optional[CacheEntry]:
        cache_file = self.cache_dir / f"{key}.cache"

        try:
            if cache_file.exists():
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self._stats["disk_reads"] += 1
                return CacheEntry(**data)

        except (json.JSONDecodeError, TypeError, KeyError, OSError) as e:
            logger.warning(f"Failed to load cache file {cache_file}: {e}")
            try:
                cache_file.unlink()
            except OSError:
                pass

        return None

    def _save_disk_cache(self, key: str, entry: CacheEntry) -> None:
        cache_file = self.cache_dir / f"{key}.cache"

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(asdict(entry), f, separators=(",", ":"))

            self._stats["disk_writes"] += 1

        except (OSError, TypeError) as e:
            logger.warning(f"Failed to save cache file {cache_file}: {e}")

    def _delete_disk_cache(self, key: str) -> bool:
        cache_file = self.cache_dir / f"{key}.cache"

        try:
            if cache_file.exists():
                cache_file.unlink()
                return True
        except OSError:
            pass

        return False


class TemplateCache:
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self._template_list_key = "gitignore_templates_list"
        self._template_content_prefix = "gitignore_content_"

    def get_template_list(self) -> Optional[List[str]]:
        return self.cache_manager.get(self._template_list_key)

    def set_template_list(self, templates: List[str]) -> None:
        self.cache_manager.set(self._template_list_key, templates)

    def get_template_content(self, technologies: List[str]) -> Optional[str]:
        key = self._make_content_key(technologies)
        return self.cache_manager.get(key)

    def set_template_content(self, technologies: List[str], content: str) -> None:
        key = self._make_content_key(technologies)
        self.cache_manager.set(key, content)

    def invalidate_template_content(self, template_name: str) -> int:
        invalidated = 0

        for cache_file in self.cache_manager.cache_dir.glob(
            f"{self._template_content_prefix}*.cache"
        ):
            key = cache_file.stem

            if template_name.lower() in key.lower():
                if self.cache_manager.delete(key):
                    invalidated += 1

        if invalidated > 0:
            logger.info(
                f"Invalidated {invalidated} cache entries for template: {template_name}"
            )

        return invalidated

    def _make_content_key(self, technologies: List[str]) -> str:
        sorted_techs = sorted([tech.lower().strip() for tech in technologies])
        tech_string = ",".join(sorted_techs)
        return f"{self._template_content_prefix}{hash(tech_string) % 1000000:06d}"
