"""Tests for the managed-block (Phase 2.5) helper."""

from igntui.core.managed_block import (
    BEGIN_MARKER,
    CUSTOM_BEGIN_MARKER,
    CUSTOM_END_MARKER,
    END_MARKER,
    extract_custom,
    merge,
    wrap,
)


def test_wrap_adds_markers():
    out = wrap("line1\nline2")
    assert BEGIN_MARKER in out
    assert END_MARKER in out
    assert "line1\nline2" in out


def test_merge_no_existing_returns_wrapped():
    out = merge(None, "fresh content")
    assert out.startswith(BEGIN_MARKER)
    assert "fresh content" in out
    # The generated region closes, then the custom-patterns region ends the file.
    assert END_MARKER in out
    assert out.rstrip().endswith(CUSTOM_END_MARKER)


def test_merge_empty_existing_returns_wrapped():
    out = merge("", "fresh")
    assert out.startswith(BEGIN_MARKER)
    assert "fresh" in out


def test_merge_replaces_only_managed_block():
    existing = (
        f"# top custom\nbuild/\n\n{BEGIN_MARKER}\nOLD\n{END_MARKER}\n\n# bottom custom\n*.log\n"
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


def test_markers_are_the_documented_text():
    """The exact text is a file format: it ships in files users commit."""
    assert BEGIN_MARKER == (
        "# >>> igntui >>> (do not edit between these markers; managed by igntui)"
    )
    assert END_MARKER == "# <<< igntui <<<"
    assert CUSTOM_BEGIN_MARKER == (
        "# >>> Start of custom patterns (do not edit between these markers; managed by igntui) <<<"
    )
    assert CUSTOM_END_MARKER == (
        "# >>> End of custom patterns (do not edit between these markers; managed by igntui) <<<"
    )


def test_wrap_emits_both_regions_custom_empty():
    out = wrap("generated")
    assert out.index(BEGIN_MARKER) < out.index(END_MARKER) < out.index(CUSTOM_BEGIN_MARKER)
    assert out.index(CUSTOM_BEGIN_MARKER) < out.index(CUSTOM_END_MARKER)
    # Nothing between the custom markers on a fresh file.
    between = out.split(CUSTOM_BEGIN_MARKER)[1].split(CUSTOM_END_MARKER)[0]
    assert between.strip() == ""


def test_custom_patterns_survive_regeneration():
    """The point of the custom block: your rules are still there afterwards."""
    first = merge(None, "GENERATED V1")
    edited = first.replace(CUSTOM_END_MARKER, "secret.env\n*.local\n" + CUSTOM_END_MARKER)

    out = merge(edited, "GENERATED V2")

    assert "secret.env" in out
    assert "*.local" in out
    assert "GENERATED V2" in out
    assert "GENERATED V1" not in out
    assert out.count(CUSTOM_BEGIN_MARKER) == 1
    assert out.count(CUSTOM_END_MARKER) == 1
    assert extract_custom(out) == "secret.env\n*.local"


def test_custom_block_is_not_duplicated_across_many_saves():
    text = merge(None, "X")
    text = text.replace(CUSTOM_END_MARKER, "mine/\n" + CUSTOM_END_MARKER)
    for _ in range(3):
        text = merge(text, "X")

    assert text.count(BEGIN_MARKER) == 1
    assert text.count(END_MARKER) == 1
    assert text.count(CUSTOM_BEGIN_MARKER) == 1
    assert text.count(CUSTOM_END_MARKER) == 1
    assert text.count("mine/") == 1


def test_extract_custom_handles_absent_and_unterminated_blocks():
    assert extract_custom(None) == ""
    assert extract_custom("no markers here\n") == ""
    assert extract_custom(f"{CUSTOM_BEGIN_MARKER}\ndangling\n") == ""


def test_legacy_file_without_markers_keeps_its_rules_and_gains_both_regions():
    out = merge("node_modules/\n*.pyc\n", "NEW")

    assert "node_modules/" in out and "*.pyc" in out
    assert out.index("node_modules/") < out.index(BEGIN_MARKER)
    assert CUSTOM_BEGIN_MARKER in out and CUSTOM_END_MARKER in out


def test_merge_malformed_markers_appends_fresh():
    """END before BEGIN is malformed; we append a fresh block instead of crashing."""
    existing = f"{END_MARKER}\nfoo\n{BEGIN_MARKER}\n"
    out = merge(existing, "NEW")

    # Original (malformed) content preserved + fresh block appended
    assert "NEW" in out
    # The fresh block introduces ONE more BEGIN marker on top of the malformed one.
    assert out.count(BEGIN_MARKER) >= 2
