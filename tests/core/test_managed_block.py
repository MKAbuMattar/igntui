"""Tests for the managed-block (Phase 2.5) helper."""

from igntui.core.managed_block import (
    BEGIN_MARKER,
    CUSTOM_BEGIN_MARKER,
    CUSTOM_END_MARKER,
    END_MARKER,
    LEGACY_CUSTOM_MARKER_PAIRS,
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
        "# >>> Start of custom patterns (edit freely; igntui preserves this block) <<<"
    )
    assert CUSTOM_END_MARKER == (
        "# >>> End of custom patterns (edit freely; igntui preserves this block) <<<"
    )


def test_custom_markers_invite_editing():
    """The custom block is the one region the user owns.

    Through 0.4.0 it said "do not edit between these markers" — the opposite of
    its purpose, telling people not to use the block that exists for them.
    """
    for marker in (CUSTOM_BEGIN_MARKER, CUSTOM_END_MARKER):
        assert "do not edit" not in marker
        assert "edit freely" in marker


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


def test_old_custom_wording_is_rewritten_and_rules_survive():
    """A .gitignore written by 0.2.0-0.4.0 upgrades in place.

    The old pair said "do not edit between these markers". Failing to recognise
    it would leave that block orphaned and append a second one below it.
    """
    old_begin, old_end = LEGACY_CUSTOM_MARKER_PAIRS[0]
    existing = (
        f"# mine\nbuild/\n\n"
        f"{BEGIN_MARKER}\nOLD GENERATED\n{END_MARKER}\n\n"
        f"{old_begin}\nsecrets.local\n*.pem\n{old_end}\n"
    )

    out = merge(existing, "NEW GENERATED")

    assert "secrets.local" in out and "*.pem" in out
    assert old_begin not in out and old_end not in out
    assert out.count(CUSTOM_BEGIN_MARKER) == 1
    assert out.count(CUSTOM_END_MARKER) == 1
    assert "OLD GENERATED" not in out and "NEW GENERATED" in out
    assert "# mine" in out and "build/" in out


def test_extract_custom_reads_the_old_wording():
    old_begin, old_end = LEGACY_CUSTOM_MARKER_PAIRS[0]
    assert extract_custom(f"{old_begin}\nnode_modules/\n{old_end}\n") == "node_modules/"


def test_upgrading_twice_does_not_duplicate_anything():
    old_begin, old_end = LEGACY_CUSTOM_MARKER_PAIRS[0]
    text = f"{BEGIN_MARKER}\nG\n{END_MARKER}\n\n{old_begin}\nkeep-me\n{old_end}\n"

    for _ in range(3):
        text = merge(text, "G")

    assert text.count(CUSTOM_BEGIN_MARKER) == 1
    assert text.count(CUSTOM_END_MARKER) == 1
    assert text.count("keep-me") == 1
    assert old_begin not in text
