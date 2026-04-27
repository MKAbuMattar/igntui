"""Tests for the user-config + repo-config cascade (Phase 6)."""

import os
from pathlib import Path
from unittest.mock import patch

import tomli_w

from igntui.core.config import Config


def _write_toml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        tomli_w.dump(data, f)


def test_repo_config_overrides_user_config(tmp_path):
    user_path = tmp_path / "user.cfg.toml"
    repo_path = tmp_path / "repo.cfg.toml"

    _write_toml(user_path, {"api": {"timeout": 30}})
    _write_toml(repo_path, {"api": {"timeout": 5}})

    cfg = Config(config_path=user_path, repo_config_path=repo_path)
    assert cfg.get("api", "timeout") == 5


def test_user_config_used_when_no_repo_config(tmp_path):
    user_path = tmp_path / "user.cfg.toml"
    _write_toml(user_path, {"api": {"timeout": 30}})

    cfg = Config(config_path=user_path)
    assert cfg.get("api", "timeout") == 30


def test_env_overrides_repo_config(tmp_path):
    user_path = tmp_path / "user.cfg.toml"
    repo_path = tmp_path / "repo.cfg.toml"
    _write_toml(user_path, {"api": {"timeout": 30}})
    _write_toml(repo_path, {"api": {"timeout": 5}})

    with patch.dict(os.environ, {"IGNTUI_API_TIMEOUT": "1"}):
        cfg = Config(config_path=user_path, repo_config_path=repo_path)
    assert cfg.get("api", "timeout") == 1


def test_repo_config_does_not_leak_selection_into_config(tmp_path):
    """`[selection]` from repo config is not merged into the runtime config —
    it's read separately by the TUI/CLI sidecar-seeding path."""
    repo_path = tmp_path / "repo.cfg.toml"
    _write_toml(
        repo_path,
        {"selection": {"templates": ["python"]}, "api": {"timeout": 7}},
    )

    cfg = Config(config_path=tmp_path / "absent.toml", repo_config_path=repo_path)
    assert cfg.get("api", "timeout") == 7
    assert cfg.get("selection") is None


def test_defaults_when_no_files_present(tmp_path):
    cfg = Config(config_path=tmp_path / "absent.toml")
    assert cfg.get("api", "timeout") == 10  # DEFAULT_CONFIG.api.timeout
    assert cfg.get("ui", "mouse_support") is True


def test_merge_is_deep_not_replace(tmp_path):
    """Setting one key in a section preserves siblings."""
    user_path = tmp_path / "user.cfg.toml"
    _write_toml(user_path, {"api": {"timeout": 99}})
    cfg = Config(config_path=user_path)
    # Other api defaults survive
    assert cfg.get("api", "timeout") == 99
    assert cfg.get("api", "retry_attempts") == 3  # default


def test_user_config_legacy_json_is_migrated(tmp_path):
    """Phase 6.2: ~/.igntui.json gets one-shot converted to ~/.igntui.cfg.toml."""
    legacy = tmp_path / ".igntui.json"
    target = tmp_path / ".igntui.cfg.toml"
    legacy.write_text('{"api": {"timeout": 42}}')

    with patch.object(Path, "home", lambda: tmp_path):
        cfg = Config(config_path=target)

    assert target.exists()
    assert legacy.exists()  # left in place
    assert cfg.get("api", "timeout") == 42
