"""Tests for the repo config (Phase 6.4)."""

from igntui.core.repo_config import (
    REPO_CONFIG_FILENAME,
    RepoConfig,
    find_repo_config,
)


def test_find_at_cwd(tmp_path):
    (tmp_path / REPO_CONFIG_FILENAME).write_text("[api]\ntimeout = 5\n")
    assert find_repo_config(tmp_path) == tmp_path / REPO_CONFIG_FILENAME


def test_find_walks_up(tmp_path):
    """Discovery walks upward through parent directories."""
    repo_root = tmp_path / "repo"
    sub = repo_root / "src" / "deep" / "nested"
    sub.mkdir(parents=True)
    cfg = repo_root / REPO_CONFIG_FILENAME
    cfg.write_text("[api]\ntimeout = 5\n")

    assert find_repo_config(sub) == cfg


def test_find_returns_none_when_no_config(tmp_path):
    sub = tmp_path / "deep" / "nested"
    sub.mkdir(parents=True)
    assert find_repo_config(sub) is None


def test_find_stops_at_git_boundary(tmp_path):
    """A `.git/` marker bounds the walk-up — outer config is not found."""
    outer = tmp_path
    repo_root = outer / "myrepo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()  # repo boundary
    sub = repo_root / "src"
    sub.mkdir()

    # Config OUTSIDE the repo — should NOT be picked up.
    (outer / REPO_CONFIG_FILENAME).write_text("[api]\ntimeout = 99\n")

    assert find_repo_config(sub) is None


def test_find_stops_at_hg_boundary(tmp_path):
    repo_root = tmp_path / "myrepo"
    repo_root.mkdir()
    (repo_root / ".hg").mkdir()
    sub = repo_root / "src"
    sub.mkdir()

    (tmp_path / REPO_CONFIG_FILENAME).write_text("[api]\ntimeout = 99\n")

    assert find_repo_config(sub) is None


def test_load_parses_documented_sections(tmp_path):
    p = tmp_path / REPO_CONFIG_FILENAME
    p.write_text(
        """
[api]
base_url = "https://internal.example.com/api"
timeout = 5

[ui]
mouse_support = false

[behavior]
max_recent_templates = 5

[selection]
templates = ["python", "node"]
search_mode = "exact"
"""
    )
    cfg = RepoConfig.load(p)
    assert cfg is not None
    assert cfg.api["base_url"] == "https://internal.example.com/api"
    assert cfg.api["timeout"] == 5
    assert cfg.ui["mouse_support"] is False
    assert cfg.behavior["max_recent_templates"] == 5
    assert cfg.selection_templates == ["python", "node"]
    assert cfg.selection_search_mode == "exact"
    assert cfg.has_selection() is True


def test_load_handles_missing_sections(tmp_path):
    p = tmp_path / REPO_CONFIG_FILENAME
    p.write_text("[api]\ntimeout = 5\n")
    cfg = RepoConfig.load(p)
    assert cfg is not None
    assert cfg.api == {"timeout": 5}
    assert cfg.ui == {}
    assert cfg.selection_templates == []
    assert cfg.has_selection() is False


def test_load_rejects_non_list_templates(tmp_path):
    p = tmp_path / REPO_CONFIG_FILENAME
    p.write_text('[selection]\ntemplates = "python"\n')
    cfg = RepoConfig.load(p)
    assert cfg is not None
    assert cfg.selection_templates == []


def test_load_rejects_invalid_search_mode(tmp_path):
    p = tmp_path / REPO_CONFIG_FILENAME
    p.write_text('[selection]\nsearch_mode = "totally-bogus"\n')
    cfg = RepoConfig.load(p)
    assert cfg is not None
    assert cfg.selection_search_mode is None


def test_load_returns_none_on_malformed_toml(tmp_path):
    p = tmp_path / REPO_CONFIG_FILENAME
    p.write_text("not toml = = =")
    assert RepoConfig.load(p) is None


def test_load_returns_none_on_missing_file(tmp_path):
    assert RepoConfig.load(tmp_path / "nonexistent.toml") is None
