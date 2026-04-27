"""Tests for the usage tracker (Phase 3.8 + Phase 6.3)."""

import json

from igntui.core.usage import (
    LEGACY_USAGE_FILENAME,
    USAGE_FILENAME,
    UsageTracker,
)


def test_record_then_top(tmp_path):
    t = UsageTracker(tmp_path / USAGE_FILENAME)
    t.record("python")
    t.record("python")
    t.record("node")
    assert t.top(2) == ["python", "node"]


def test_top_orders_by_count_then_recency(tmp_path):
    t = UsageTracker(tmp_path / USAGE_FILENAME)
    t.record("a")
    t.record("b")
    t.record("b")
    t.record("c")
    # b has count 2, then a/c have count 1; among ties, more recent wins
    top = t.top(3)
    assert top[0] == "b"
    # c was recorded after a → c before a
    assert top.index("c") < top.index("a")


def test_top_n_caps_size(tmp_path):
    t = UsageTracker(tmp_path / USAGE_FILENAME)
    for i in range(5):
        t.record(f"t{i}")
    assert len(t.top(3)) == 3


def test_persists_across_instances_in_toml(tmp_path):
    """Phase 6.3: persistence uses TOML; survives a fresh tracker instance."""
    path = tmp_path / USAGE_FILENAME
    t1 = UsageTracker(path)
    t1.record("python")
    t1.record("python")
    t1.record("node")

    # File is TOML, not JSON
    raw = path.read_text(encoding="utf-8")
    assert "[python]" in raw
    assert "count" in raw

    t2 = UsageTracker(path)
    assert t2.top(2) == ["python", "node"]


def test_load_handles_missing_file(tmp_path):
    t = UsageTracker(tmp_path / "nonexistent.toml")
    assert t.top(10) == []


def test_load_handles_corrupt_file(tmp_path):
    path = tmp_path / USAGE_FILENAME
    path.write_text("this is not toml = = =")
    t = UsageTracker(path)
    assert t.top(10) == []


def test_filename_is_dotted_toml():
    """Phase 6.3: filename uses dot-separator + .toml extension."""
    assert USAGE_FILENAME == ".igntui.usage.toml"
    assert LEGACY_USAGE_FILENAME == ".igntui_usage.json"


def test_legacy_json_is_migrated_to_toml(tmp_path):
    """Phase 6.3: legacy JSON auto-migrates to TOML on first launch."""
    legacy = tmp_path / LEGACY_USAGE_FILENAME
    legacy.write_text(
        json.dumps(
            {
                "python": {"count": 5, "last_used": 1714209487.0},
                "node": {"count": 2, "last_used": 1714209412.0},
            }
        )
    )
    target = tmp_path / USAGE_FILENAME
    assert not target.exists()

    t = UsageTracker(target)

    assert target.exists(), "TOML file should have been created"
    assert legacy.exists(), "legacy JSON should be left in place"
    assert t.top(2) == ["python", "node"]


def test_no_migration_when_target_already_exists(tmp_path):
    """If TOML already exists, the legacy file is ignored — no double-migration."""
    target = tmp_path / USAGE_FILENAME
    legacy = tmp_path / LEGACY_USAGE_FILENAME

    # Pre-existing TOML
    UsageTracker(target).record("python")

    # Legacy file with conflicting content
    legacy.write_text(
        json.dumps({"node": {"count": 99, "last_used": 1.0}})
    )

    t = UsageTracker(target)
    # node should not appear; the existing TOML is the source of truth.
    assert "node" not in t.top(10)
    assert "python" in t.top(10)
