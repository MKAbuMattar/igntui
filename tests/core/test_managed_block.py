"""Tests for the managed-block (Phase 2.5) helper."""

from igntui.core.managed_block import BEGIN_MARKER, END_MARKER, merge, wrap


def test_wrap_adds_markers():
    out = wrap("line1\nline2")
    assert BEGIN_MARKER in out
    assert END_MARKER in out
    assert "line1\nline2" in out


def test_merge_no_existing_returns_wrapped():
    out = merge(None, "fresh content")
    assert out.startswith(BEGIN_MARKER)
    assert "fresh content" in out
    assert out.rstrip().endswith(END_MARKER)


def test_merge_empty_existing_returns_wrapped():
    out = merge("", "fresh")
    assert out.startswith(BEGIN_MARKER)
    assert "fresh" in out


def test_merge_replaces_only_managed_block():
    existing = (
        f"# top custom\nbuild/\n\n"
        f"{BEGIN_MARKER}\n"
        f"OLD\n"
        f"{END_MARKER}\n\n"
        f"# bottom custom\n*.log\n"
    )
    out = merge(existing, "NEW")

    assert "# top custom" in out
    assert "build/" in out
    assert "# bottom custom" in out
    assert "*.log" in out
    assert "NEW" in out
    assert "OLD" not in out


def test_merge_idempotent_marker_count():
    """Re-saving must not duplicate the marker pair."""
    once = merge(None, "X")
    twice = merge(once, "X")
    thrice = merge(twice, "X")
    assert thrice.count(BEGIN_MARKER) == 1
    assert thrice.count(END_MARKER) == 1


def test_merge_legacy_file_no_markers_appends_block():
    existing = "node_modules/\n*.pyc\n"
    out = merge(existing, "NEW")

    assert "node_modules/" in out
    assert "*.pyc" in out
    assert BEGIN_MARKER in out
    assert "NEW" in out
    # Managed block comes after the legacy content
    assert out.index("node_modules/") < out.index(BEGIN_MARKER)


def test_merge_malformed_markers_appends_fresh():
    """END before BEGIN is malformed; we append a fresh block instead of crashing."""
    existing = f"{END_MARKER}\nfoo\n{BEGIN_MARKER}\n"
    out = merge(existing, "NEW")

    # Original (malformed) content preserved + fresh block appended
    assert "NEW" in out
    # The fresh block introduces ONE more BEGIN marker on top of the malformed one.
    assert out.count(BEGIN_MARKER) >= 2
