"""Tests for the search engines."""

import pytest

from igntui.core.search import SearchManager, SearchMode


@pytest.fixture
def mgr():
    return SearchManager()


def test_fuzzy_finds_subsequence(mgr, template_list):
    out = mgr.search(template_list, "pyt", mode=SearchMode.FUZZY)
    items = out.get_items()
    assert "python" in items
    assert "pythonvanilla" in items


def test_fuzzy_orders_exact_match_first(mgr, template_list):
    out = mgr.search(template_list, "java", mode=SearchMode.FUZZY)
    items = out.get_items()
    # `java` is a substring/exact match — must outrank `javascript`
    assert items[0] == "java"


def test_exact_matches_substring(mgr, template_list):
    out = mgr.search(template_list, "java", mode=SearchMode.EXACT)
    items = out.get_items()
    assert "java" in items
    assert "javascript" in items
    assert "python" not in items


def test_regex_anchors_work(mgr, template_list):
    out = mgr.search(template_list, "^r", mode=SearchMode.REGEX)
    items = out.get_items()
    assert set(items) == {"rust", "ruby"}


def test_regex_invalid_pattern_returns_empty(mgr, template_list):
    out = mgr.search(template_list, "[invalid", mode=SearchMode.REGEX)
    assert out.get_items() == []


def test_empty_query_returns_all(mgr, template_list):
    out = mgr.search(template_list, "", mode=SearchMode.FUZZY)
    assert set(out.get_items()) == set(template_list)


def test_no_matches(mgr, template_list):
    out = mgr.search(template_list, "zzzzzz", mode=SearchMode.FUZZY)
    assert out.get_items() == []


def test_max_results_caps_output(mgr, template_list):
    out = mgr.search(template_list, "", mode=SearchMode.FUZZY, max_results=3)
    assert len(out.get_items()) == 3


def test_set_mode_changes_default(mgr):
    mgr.set_mode(SearchMode.REGEX)
    assert mgr.get_mode() == SearchMode.REGEX
