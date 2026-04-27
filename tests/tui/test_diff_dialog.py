"""Tests for DiffPreviewDialog logic (Phase 5.4).

We test the diff-computation parts only — the curses interaction layer
(`show()`'s key loop) requires a real terminal and isn't unit-tested.
"""

from unittest.mock import MagicMock

from igntui.ui.components.diff_preview_dialog import DiffPreviewDialog


def test_empty_when_contents_match():
    dlg = DiffPreviewDialog(MagicMock(), current="same\n", proposed="same\n")
    assert dlg.is_empty()


def test_non_empty_when_contents_differ():
    dlg = DiffPreviewDialog(MagicMock(), current="old\n", proposed="new\n")
    assert not dlg.is_empty()
    body = "\n".join(dlg.diff_lines)
    assert "-old" in body
    assert "+new" in body


def test_diff_uses_filename_in_headers():
    dlg = DiffPreviewDialog(
        MagicMock(),
        current="line\n",
        proposed="line2\n",
        filename=".gitignore",
    )
    assert any(".gitignore" in line for line in dlg.diff_lines)
