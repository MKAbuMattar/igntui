"""Shared pytest fixtures for igntui tests."""

import pytest


@pytest.fixture
def tmp_cache_dir(tmp_path):
    """A throwaway directory usable as a CacheManager cache_dir."""
    d = tmp_path / "cache"
    d.mkdir()
    return d


@pytest.fixture
def template_list():
    """A small representative list of templates for search tests."""
    return [
        "python",
        "pythonvanilla",
        "java",
        "javascript",
        "go",
        "rust",
        "ruby",
        "node",
        "macos",
        "linux",
        "windows",
    ]
