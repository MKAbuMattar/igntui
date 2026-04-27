"""Tests for the queue-based lifecycle (Phase 3.7).

Verifies background threads post the right StateUpdate messages without
ever touching state directly.
"""

import queue
from unittest.mock import MagicMock

import pytest

from igntui.core.api.response import APIResponse
from igntui.core.search import SearchManager
from igntui.tui.lifecycle import TemplateLifecycle
from igntui.tui.updates import (
    ContentGenerated,
    ContentGenerationFailed,
    GenerationCompleted,
    LoadCompleted,
    StateUpdate,
    TemplatesLoaded,
    TemplatesLoadFailed,
)


def _drain(q: "queue.Queue[StateUpdate]", timeout: float = 1.0) -> list:
    """Wait until LoadCompleted/GenerationCompleted arrives, return all messages."""
    out = []
    while True:
        msg = q.get(timeout=timeout)
        out.append(msg)
        if isinstance(msg, (LoadCompleted, GenerationCompleted)):
            return out


def test_load_success_posts_loaded_then_completed():
    api = MagicMock()
    api.list_templates.return_value = APIResponse(success=True, data=["python", "go"])
    lc = TemplateLifecycle(api, SearchManager())

    q: queue.Queue[StateUpdate] = queue.Queue()
    lc.load_templates_async(q)
    msgs = _drain(q)

    assert any(isinstance(m, TemplatesLoaded) and m.templates == ["go", "python"] for m in msgs)
    assert isinstance(msgs[-1], LoadCompleted)


def test_load_failure_posts_failed_then_completed():
    api = MagicMock()
    api.list_templates.return_value = APIResponse(
        success=False, data=[], error_message="boom"
    )
    lc = TemplateLifecycle(api, SearchManager())

    q: queue.Queue[StateUpdate] = queue.Queue()
    lc.load_templates_async(q)
    msgs = _drain(q)

    assert any(isinstance(m, TemplatesLoadFailed) and "boom" in m.message for m in msgs)
    assert isinstance(msgs[-1], LoadCompleted)


def test_generate_success_posts_content_then_completed():
    api = MagicMock()
    api.get_templates.return_value = APIResponse(
        success=True, data="GENERATED", from_cache=True
    )
    lc = TemplateLifecycle(api, SearchManager())

    q: queue.Queue[StateUpdate] = queue.Queue()
    lc.generate_content_async(["python"], q)
    msgs = _drain(q)

    matches = [m for m in msgs if isinstance(m, ContentGenerated)]
    assert len(matches) == 1
    assert matches[0].content == "GENERATED"
    assert matches[0].from_cache is True
    assert isinstance(msgs[-1], GenerationCompleted)


def test_generate_empty_template_list_posts_failure_synchronously():
    api = MagicMock()
    lc = TemplateLifecycle(api, SearchManager())

    q: queue.Queue[StateUpdate] = queue.Queue()
    lc.generate_content_async([], q)

    # Synchronous: no background thread should be needed
    msgs = []
    while not q.empty():
        msgs.append(q.get_nowait())

    assert any(isinstance(m, ContentGenerationFailed) for m in msgs)
    assert any(isinstance(m, GenerationCompleted) for m in msgs)
    api.get_templates.assert_not_called()


def test_state_updates_are_immutable():
    """`@dataclass(frozen=True)` should prevent post-construction mutation."""
    import dataclasses

    msg = TemplatesLoaded(templates=["a"])
    with pytest.raises(dataclasses.FrozenInstanceError):
        msg.templates = ["b"]  # type: ignore[misc]
