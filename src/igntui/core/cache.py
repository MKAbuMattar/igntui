#!/usr/bin/env python3


import hashlib
import json
import logging
import os
import re
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import RLock
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    data: Any
    timestamp: float
    ttl: int
    access_count: int = 0
    last_access: float | None = None

    def is_expired(self) -> bool:
        return time.time() > (self.timestamp + self.ttl)

    def touch(self) -> None:
        self.access_count += 1
        self.last_access = time.time()


class CacheManager:
    def __init__(self, cache_dir: str | Path, default_ttl: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl
        self._memory_cache: dict[str, CacheEntry] = {}
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
        self._purge_legacy_content_keys()

        # Deliberately not reading the cache into memory here. `get()` already
        # falls back to disk and promotes what it finds, so an eager load bought
        # nothing except latency — and every command pays it, because
        # GitIgnoreAPI constructs a manager on the way to doing anything. Over a
        # realistic cache (300 content blobs, ~3.5 MiB) it measured ~19 ms of
        # open + json.loads before the process could start its actual work.
        #
        # The eager pass also deleted expired files. Losing that is nearly free:
        # a content key is a hash of its template set, so re-requesting the same
        # set overwrites the stale entry in place, and `get()` deletes any
        # expired entry it touches. Only sets never asked for again linger, and
        # `igntui cache clear --expired` sweeps those.
        logger.debug("Initialized cache manager with directory: %s", self.cache_dir)

    def _purge_legacy_content_keys(self) -> None:
        # Pre-Phase-2.1 keys used `hash() % 1000000` (6 decimal digits, non-stable
        # across processes). New keys are 16 hex chars from sha256. Anything that
        # matches the old shape is dead weight — drop it.
        legacy_re = re.compile(r"^gitignore_content_\d{6}$")
        purged = 0
        for cache_file in self.cache_dir.glob("gitignore_content_*.cache"):
            if legacy_re.match(cache_file.stem):
                try:
                    cache_file.unlink()
                    purged += 1
                except OSError:
                    pass
        if purged:
            logger.info("Purged %d legacy content cache entries", purged)

    def get(self, key: str) -> Any | None:
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
                logger.debug("Cache hit for key: %s", key)
                return entry.data

            disk_entry = self._load_disk_cache(key)
            if disk_entry and not disk_entry.is_expired():
                self._memory_cache[key] = disk_entry
                disk_entry.touch()
                self._stats["hits"] += 1
                logger.debug("Disk cache hit for key: %s", key)
                return disk_entry.data
            elif disk_entry:
                self._delete_disk_cache(key)
                self._stats["evictions"] += 1

            self._stats["misses"] += 1
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ttl = ttl or self.default_ttl

        with self._lock:
            entry = CacheEntry(data=value, timestamp=time.time(), ttl=ttl)

            self._memory_cache[key] = entry
            self._save_disk_cache(key, entry)
            self._stats["sets"] += 1

            logger.debug("Cached value for key: %s (TTL: %ds)", key, ttl)

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
                logger.debug("Deleted cache entry: %s", key)

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
            logger.info("Cleared %d cache entries", total_cleared)
            return total_cleared

    # Backwards-compatible alias used by `igntui cache clear`.
    def clear_all(self) -> int:
        return self.clear()

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
                logger.info("Cleaned up %d expired cache entries", total_cleaned)

            return total_cleaned

    def get_stats(self) -> dict[str, Any]:
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

    def _load_disk_cache(self, key: str) -> CacheEntry | None:
        cache_file = self.cache_dir / f"{key}.cache"

        try:
            if cache_file.exists():
                with open(cache_file, encoding="utf-8") as f:
                    data = json.load(f)

                self._stats["disk_reads"] += 1
                return CacheEntry(**data)

        except (json.JSONDecodeError, TypeError, KeyError, OSError) as e:
            logger.warning("Failed to load cache file %s: %s", cache_file, e)
            try:
                cache_file.unlink()
            except OSError:
                pass

        return None

    def _save_disk_cache(self, key: str, entry: CacheEntry) -> None:
        """Write an entry to disk atomically.

        Writing in place meant a crash, a full disk, or two processes saving the
        same key could leave truncated JSON behind. That was survivable — a read
        catches the JSONDecodeError and unlinks the file — but the entry was lost
        and the failure was silent. Writing a temp file in the same directory and
        renaming makes the swap atomic on POSIX and Windows: a reader sees either
        the old entry or the new one, never half of either.
        """
        cache_file = self.cache_dir / f"{key}.cache"
        tmp_path: str | None = None

        try:
            # Same directory, so os.replace is a rename rather than a cross-device copy.
            fd, tmp_path = tempfile.mkstemp(dir=self.cache_dir, suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(asdict(entry), f, separators=(",", ":"))
            os.replace(tmp_path, cache_file)
            tmp_path = None

            self._stats["disk_writes"] += 1

        except (OSError, TypeError) as e:
            logger.warning("Failed to save cache file %s: %s", cache_file, e)
        finally:
            # A serialisation failure leaves the temp file behind; the previous
            # good entry is still in place, which is the point.
            if tmp_path is not None:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

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

    def get_template_list(self) -> list[str] | None:
        return self.cache_manager.get(self._template_list_key)

    def set_template_list(self, templates: list[str]) -> None:
        self.cache_manager.set(self._template_list_key, templates)

    def get_template_content(self, technologies: list[str]) -> str | None:
        key = self._make_content_key(technologies)
        return self.cache_manager.get(key)

    def set_template_content(self, technologies: list[str], content: str) -> None:
        key = self._make_content_key(technologies)
        self.cache_manager.set(key, content)

    # No per-template invalidation helper: content keys are sha256 prefixes, so a
    # template name cannot be recovered from one. The version that tried matched
    # `name in key`, which could only ever hit by accident — and would delete
    # unrelated entries for a short hex-ish name like `ade` or `cafe`. Clearing
    # the whole content cache (`igntui cache clear`) is the honest operation; a
    # real implementation needs a stored name -> digest index.

    def _make_content_key(self, technologies: list[str]) -> str:
        sorted_techs = sorted({tech.lower().strip() for tech in technologies if tech.strip()})
        tech_string = ",".join(sorted_techs)
        digest = hashlib.sha256(tech_string.encode("utf-8")).hexdigest()[:16]
        return f"{self._template_content_prefix}{digest}"
