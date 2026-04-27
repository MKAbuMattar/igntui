"""Regression tests for tui.lifecycle.filter_templates.

This locks in the Phase 1.1 fix — the call to SearchManager.search had its
positional args swapped, so search silently fell back to substring matching.
"""

from unittest.mock import Mock

import pytest

from igntui.core.search import SearchManager
from igntui.tui.lifecycle import TemplateLifecycle


@pytest.fixture
def lc():
    return TemplateLifecycle(api=Mock(), search_manager=SearchManager())


def test_fuzzy_returns_real_fuzzy_matches(lc, template_list):
    out = lc.filter_templates(template_list, "pyt", "fuzzy")
    assert "python" in out
    assert "pythonvanilla" in out


def test_exact_uses_exact_engine(lc, template_list):
    out = lc.filter_templates(template_list, "java", "exact")
    assert "java" in out
    assert "javascript" in out
    assert "python" not in out


def test_regex_anchors_work(lc, template_list):
    out = lc.filter_templates(template_list, "^r", "regex")
    assert set(out) == {"rust", "ruby"}


def test_unknown_mode_falls_back_to_fuzzy(lc, template_list):
    out = lc.filter_templates(template_list, "py", "spurious")
    # Falls back to fuzzy and produces results, doesn't crash.
    assert "python" in out


def test_empty_filter_returns_all(lc, template_list):
    out = lc.filter_templates(template_list, "", "fuzzy")
    assert set(out) == set(template_list)


def test_filter_returns_list_of_strings(lc, template_list):
    """Ensures the SearchResults wrapper is unwrapped before returning."""
    out = lc.filter_templates(template_list, "py", "fuzzy")
    assert isinstance(out, list)
    assert all(isinstance(x, str) for x in out)
