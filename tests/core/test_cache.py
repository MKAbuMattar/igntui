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
    sha_keyed.write_text('{"data":"y","timestamp":0,"ttl":99999999999,"access_count":0,"last_access":null}')

    CacheManager(str(tmp_cache_dir))

    assert not legacy.exists(), "legacy 6-digit key should have been purged"
    assert sha_keyed.exists(), "sha256-keyed entry should have survived"


def test_template_list_round_trip(tmp_cache_dir):
    cache = CacheManager(str(tmp_cache_dir))
    tc = TemplateCache(cache)
    tc.set_template_list(["python", "node", "go"])
    assert tc.get_template_list() == ["python", "node", "go"]
