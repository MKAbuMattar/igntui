"""_drain_updates applies only results that match the current selection."""

import queue
from unittest.mock import MagicMock

from igntui.core.search import SearchManager
from igntui.tui.actions import TUIActions
from igntui.tui.app import GitIgnoreTUI
from igntui.tui.lifecycle import TemplateLifecycle
from igntui.tui.state import TUIState
from igntui.tui.updates import (
    ContentGenerated,
    ContentGenerationFailed,
    GenerationCompleted,
    TemplatesLoaded,
)


def _tui(selected: set[str]) -> GitIgnoreTUI:
    tui = GitIgnoreTUI.__new__(GitIgnoreTUI)  # skip curses setup
    tui.state = TUIState()
    tui.state.selected_templates = set(selected)
    tui.updates = queue.Queue()
    tui.lifecycle = TemplateLifecycle(MagicMock(), SearchManager())
    tui.lifecycle.usage = MagicMock(top=MagicMock(return_value=[]))
    return tui


def test_stale_result_from_earlier_selection_is_dropped():
    tui = _tui({"node", "python"})
    tui.state.generation_in_progress = True
    tui.updates.put(ContentGenerated("NODE+PY", False, ("node", "python")))
    tui.updates.put(GenerationCompleted(("node", "python")))
    tui.updates.put(ContentGenerated("PY ONLY", False, ("python",)))
    tui.updates.put(GenerationCompleted(("python",)))
    tui._drain_updates()
    assert tui.state.generated_content == "NODE+PY"
    assert tui.state.content_ok
    assert not tui.state.generation_in_progress


def test_result_arriving_after_clear_is_dropped():
    tui = _tui(set())
    tui.updates.put(ContentGenerated("PY", False, ("python",)))
    tui._drain_updates()
    assert tui.state.generated_content == ""
    assert not tui.state.content_ok


def test_failed_generation_is_not_saveable():
    tui = _tui({"python"})
    tui.state.content_ok = True
    tui.updates.put(ContentGenerationFailed("Error: offline", ["python"]))
    tui._drain_updates()
    assert not tui.state.content_ok
    actions = TUIActions(MagicMock(), tui.state)
    actions.save_gitignore()
    assert "failed" in tui.state.error_message


def test_refresh_keeps_active_filter():
    tui = _tui(set())
    tui.state.filter_text = "py"
    tui.updates.put(TemplatesLoaded(["node", "python", "rust"]))
    tui._drain_updates()
    assert tui.state.filtered_templates == ["python"]


def test_resave_of_same_selection_reports_no_changes(tmp_path, monkeypatch):
    import igntui.tui.actions as actions_mod

    target = tmp_path / ".gitignore"
    state = TUIState()
    state.selected_templates = {"python"}
    state.generated_content = "__pycache__/\n"
    state.content_ok = True
    monkeypatch.setattr(actions_mod, "SaveDialog", lambda _s: MagicMock(show=lambda: str(target)))
    diff = MagicMock()
    monkeypatch.setattr(actions_mod, "DiffPreviewDialog", diff)
    actions = TUIActions(MagicMock(), state)

    actions.save_gitignore()
    first = target.read_text(encoding="utf-8")
    monkeypatch.setattr(actions_mod.time, "strftime", lambda _f: "2099-01-01 00:00:00")
    actions.save_gitignore()

    assert "No changes" in state.status_message
    diff.assert_not_called()
    assert target.read_text(encoding="utf-8") == first
