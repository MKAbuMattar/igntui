"""Tests for the cache layer.

Locks in the Phase 2.1 fix (sha256 keys + cross-process disk hits).
"""

from igntui.core.cache import CacheManager, TemplateCache


def test_set_then_get_in_memory(tmp_cache_dir):
    cache = CacheManager(str(tmp_cache_dir))
    cache.set("k", "v")
    assert cache.get("k") == "v"


def test_get_missing_returns_none(tmp_cache_dir):
    cache = CacheManager(str(tmp_cache_dir))
    assert cache.get("nonexistent") is None


def test_disk_cache_survives_fresh_manager(tmp_cache_dir):
    """A new CacheManager pointing at the same dir must read prior writes.

    This is the regression test for the `hash() % 1e6` bug fixed in Phase 2.1.
    """
    cache1 = CacheManager(str(tmp_cache_dir))
    tc1 = TemplateCache(cache1)
    tc1.set_template_content(["python", "node"], "GENERATED_BLOB")

    cache2 = CacheManager(str(tmp_cache_dir))
    tc2 = TemplateCache(cache2)

    assert tc2.get_template_content(["python", "node"]) == "GENERATED_BLOB"


def test_template_content_key_is_order_insensitive(tmp_cache_dir):
    cache = CacheManager(str(tmp_cache_dir))
    tc = TemplateCache(cache)
    tc.set_template_content(["python", "node"], "BLOB")

    # Different order, different case, surrounding whitespace
    assert tc.get_template_content(["NODE", " python "]) == "BLOB"


def test_template_content_key_differs_for_different_combos(tmp_cache_dir):
    cache = CacheManager(str(tmp_cache_dir))
    tc = TemplateCache(cache)

    k1 = tc._make_content_key(["python"])
    k2 = tc._make_content_key(["python", "node"])
    k3 = tc._make_content_key(["rust"])

    assert len({k1, k2, k3}) == 3


def test_template_content_key_shape(tmp_cache_dir):
    cache = CacheManager(str(tmp_cache_dir))
    tc = TemplateCache(cache)

    key = tc._make_content_key(["python", "node"])
    assert key.startswith("gitignore_content_")
    digest = key.removeprefix("gitignore_content_")
    assert len(digest) == 16
    assert all(c in "0123456789abcdef" for c in digest)


def test_expired_entry_evicted_on_get(tmp_cache_dir):
    cache = CacheManager(str(tmp_cache_dir))
    cache.set("k", "v", ttl=-1)  # already expired
    assert cache.get("k") is None


def test_clear_empties_memory_and_disk(tmp_cache_dir):
    cache = CacheManager(str(tmp_cache_dir))
    cache.set("a", 1)
    cache.set("b", 2)

    cleared = cache.clear()
    assert cleared >= 2
    assert cache.get("a") is None
    assert list(tmp_cache_dir.glob("*.cache")) == []


def test_clear_all_alias(tmp_cache_dir):
    """Phase 1.2: `clear_all` is an alias used by `igntui cache clear`."""
    cache = CacheManager(str(tmp_cache_dir))
    cache.set("k", "v")
    assert cache.clear_all() >= 1


def test_legacy_content_keys_purged_on_init(tmp_cache_dir):
    """Phase 2.1: pre-sha256 entries (6 decimal digits) get auto-cleared."""
    legacy = tmp_cache_dir / "gitignore_content_123456.cache"
    legacy.write_text('{"data":"x","timestamp":0,"ttl":0,"access_count":0,"last_access":null}')
    sha_keyed = tmp_cache_dir / "gitignore_content_abcdef0123456789.cache"
    sha_keyed.write_text(
        '{"data":"y","timestamp":0,"ttl":99999999999,"access_count":0,"last_access":null}'
    )

    CacheManager(str(tmp_cache_dir))

    assert not legacy.exists(), "legacy 6-digit key should have been purged"
    assert sha_keyed.exists(), "sha256-keyed entry should have survived"


def test_template_list_round_trip(tmp_cache_dir):
    cache = CacheManager(str(tmp_cache_dir))
    tc = TemplateCache(cache)
    tc.set_template_list(["python", "node", "go"])
    assert tc.get_template_list() == ["python", "node", "go"]


def test_construction_does_not_read_the_cache_into_memory(tmp_cache_dir):
    """Startup is lazy: reading every entry cost every command real time.

    A CacheManager over a populated directory used to open and json.loads each
    file in __init__, which measured ~19 ms over 300 content blobs — paid by
    every command, because GitIgnoreAPI builds a manager before doing anything.
    """
    seed = CacheManager(str(tmp_cache_dir))
    for i in range(5):
        seed.set(f"key-{i}", f"value-{i}")

    fresh = CacheManager(str(tmp_cache_dir))

    assert fresh.get_stats()["memory_entries"] == 0
    assert fresh.get_stats()["disk_entries"] == 5


def test_lazy_start_still_serves_and_promotes_disk_entries(tmp_cache_dir):
    """Nothing is lost by not preloading: get() reads disk and caches the hit."""
    CacheManager(str(tmp_cache_dir)).set("k", "v")

    fresh = CacheManager(str(tmp_cache_dir))
    assert fresh.get("k") == "v"
    assert fresh.get_stats()["memory_entries"] == 1

    # Second read is served from memory, not disk.
    reads_before = fresh.get_stats()["disk_reads"]
    assert fresh.get("k") == "v"
    assert fresh.get_stats()["disk_reads"] == reads_before


def test_expired_entry_is_dropped_on_read_not_at_startup(tmp_cache_dir):
    CacheManager(str(tmp_cache_dir)).set("stale", "v", ttl=-1)

    fresh = CacheManager(str(tmp_cache_dir))
    # Still on disk — construction no longer sweeps.
    assert fresh.get_stats()["disk_entries"] == 1

    assert fresh.get("stale") is None
    assert list(tmp_cache_dir.glob("*.cache")) == []


def test_cleanup_expired_sweeps_without_a_preloaded_memory_cache(tmp_cache_dir):
    """What `igntui cache clear --expired` calls, on a cold manager."""
    seed = CacheManager(str(tmp_cache_dir))
    seed.set("fresh-1", "v")
    seed.set("stale-1", "v", ttl=-1)
    seed.set("stale-2", "v", ttl=-1)

    cold = CacheManager(str(tmp_cache_dir))
    assert cold.cleanup_expired() == 2

    assert cold.get("fresh-1") == "v"
    assert cold.get("stale-1") is None
    assert len(list(tmp_cache_dir.glob("*.cache"))) == 1


def test_cleanup_expired_on_an_empty_cache_is_a_no_op(tmp_cache_dir):
    assert CacheManager(str(tmp_cache_dir)).cleanup_expired() == 0


def test_failed_write_leaves_the_previous_entry_intact(tmp_cache_dir):
    """Atomic swap: a serialisation failure must not destroy what was there.

    An in-place write truncated the file first and only then discovered the
    value was unserialisable, losing a good entry to a bad write.
    """
    cache = CacheManager(str(tmp_cache_dir))
    cache.set("k", "good value")

    cache.set("k", {"unserialisable": object()})

    fresh = CacheManager(str(tmp_cache_dir))
    assert fresh.get("k") == "good value"


def test_failed_write_leaves_no_temp_files_behind(tmp_cache_dir):
    cache = CacheManager(str(tmp_cache_dir))
    cache.set("k", {"unserialisable": object()})

    assert list(tmp_cache_dir.glob("*.tmp")) == []


def test_successful_write_leaves_no_temp_files_behind(tmp_cache_dir):
    cache = CacheManager(str(tmp_cache_dir))
    for i in range(3):
        cache.set(f"k{i}", "v")

    assert list(tmp_cache_dir.glob("*.tmp")) == []
    assert len(list(tmp_cache_dir.glob("*.cache"))) == 3


def test_overwriting_a_key_never_exposes_a_partial_file(tmp_cache_dir):
    """Every rewrite of the same key must land as valid JSON, start to finish."""
    import json

    cache = CacheManager(str(tmp_cache_dir))
    cache_file = tmp_cache_dir / "k.cache"

    for i in range(20):
        cache.set("k", f"value-{i}" * 200)
        # Read the raw file the way a second process would.
        payload = json.loads(cache_file.read_text(encoding="utf-8"))
        assert payload["data"] == f"value-{i}" * 200
