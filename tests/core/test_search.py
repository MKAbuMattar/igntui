"""Tests for template search."""

from igntui.core.search import SearchMode, search


def test_fuzzy_finds_subsequence(template_list):
    items = search(template_list, "pyt")
    assert "python" in items
    assert "pythonvanilla" in items


def test_fuzzy_orders_exact_match_first(template_list):
    # `java` is a substring/exact match and must outrank `javascript`
    assert search(template_list, "java")[0] == "java"


def test_exact_matches_substring(template_list):
    items = search(template_list, "java", SearchMode.EXACT)
    assert "java" in items
    assert "javascript" in items
    assert "python" not in items


def test_regex_anchors_work(template_list):
    assert set(search(template_list, "^r", SearchMode.REGEX)) == {"rust", "ruby"}


def test_regex_invalid_pattern_returns_empty(template_list):
    assert search(template_list, "[invalid", SearchMode.REGEX) == []


def test_regex_zero_width_match_counts(template_list):
    assert set(search(template_list, "x*", SearchMode.REGEX)) == set(template_list)


def test_empty_query_returns_all(template_list):
    assert set(search(template_list, "")) == set(template_list)


def test_no_matches(template_list):
    assert search(template_list, "zzzzzz") == []


def test_max_results_caps_output(template_list):
    assert len(search(template_list, "", max_results=3)) == 3
