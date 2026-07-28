"""The command classes: what they print and what they return.

Each one is `execute(args) -> int` over an injected `cli` object, so a fake CLI
and a fake API cover them with no network. Exit codes matter — they are
documented in `docs/concepts/return-codes.md` and scripts depend on them.
"""

import argparse

import pytest

from igntui.cli.commands import CacheCommand, ListCommand
from igntui.cli.commands import (
    TestCommand as ConnectionCommand,  # aliased: pytest collects Test* classes
)
from igntui.core.api.response import APIResponse


class FakeAPI:
    def __init__(self, list_response=None, test_response=None, cache_manager=None):
        self._list = list_response
        self._test = test_response
        self.cache_manager = cache_manager

    def list_templates(self, force_refresh: bool = False):
        if isinstance(self._list, Exception):
            raise self._list
        return self._list

    def test_connection(self):
        if isinstance(self._test, Exception):
            raise self._test
        return self._test


class FakeCLI:
    def __init__(self, api):
        self.api = api
        self.errors: list[Exception] = []

    def handle_api_error(self, error: Exception) -> None:
        self.errors.append(error)
        print(f"Error: {error}")


def args(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(verbose=False, **kwargs)


# --- list ------------------------------------------------------------------


def list_command(templates=("python", "node", "macos"), error=None):
    response = (
        error
        if isinstance(error, Exception)
        else APIResponse(success=error is None, data=list(templates), error_message=error)
    )
    return ListCommand(FakeCLI(FakeAPI(list_response=response)))


def test_list_prints_every_template(capsys):
    assert list_command().execute(args(filter=None, count=False)) == 0
    out = capsys.readouterr().out
    for template in ("python", "node", "macos"):
        assert template in out


def test_list_count_reports_the_number_only(capsys):
    assert list_command().execute(args(filter=None, count=True)) == 0
    out = capsys.readouterr().out
    assert "3" in out
    assert "python" not in out


def test_list_filter_narrows_case_insensitively(capsys):
    assert list_command().execute(args(filter="PY", count=False)) == 0
    out = capsys.readouterr().out
    assert "python" in out
    assert "node" not in out


def test_list_filter_matching_nothing_is_a_failure(capsys):
    """Non-zero, so `igntui list --filter x` is usable in a shell conditional."""
    assert list_command().execute(args(filter="zzz", count=False)) == 1
    assert "zzz" in capsys.readouterr().out


def test_list_reports_api_failure(capsys):
    command = list_command(templates=[], error="upstream is down")
    assert command.execute(args(filter=None, count=False)) == 1
    assert "upstream is down" in capsys.readouterr().out


def test_list_routes_exceptions_through_the_error_handler(capsys):
    command = list_command(error=ConnectionError("no route to host"))
    assert command.execute(args(filter=None, count=False)) == 1
    assert command.cli.errors


# --- test ------------------------------------------------------------------


def test_connection_command_reports_the_real_latency(capsys):
    """Regression: it used to read the wrapper, which is never populated.

    `test_connection()` puts timing, endpoint and cache stats inside `data`, so
    reading `response.response_time` printed 0.000s and `N/A` on every run.
    """
    payload = {
        "status": "connected",
        "response_time": 0.4242,
        "api_url": "https://example.test/api",
        "cache_stats": {"disk_entries": 7},
    }
    command = ConnectionCommand(FakeCLI(FakeAPI(test_response=APIResponse(True, payload))))

    assert command.execute(args(timeout=10)) == 0

    out = capsys.readouterr().out
    assert "0.424s" in out
    assert "https://example.test/api" in out
    assert "7" in out
    assert "0.000s" not in out
    assert "N/A" not in out


def test_connection_command_reports_failure(capsys):
    command = ConnectionCommand(
        FakeCLI(
            FakeAPI(
                test_response=APIResponse(False, {"status": "failed"}, error_message="timed out")
            )
        )
    )

    assert command.execute(args(timeout=1)) == 1
    assert "timed out" in capsys.readouterr().out


def test_connection_command_survives_a_missing_payload(capsys):
    """A non-dict `data` must not crash the diagnostic."""
    command = ConnectionCommand(FakeCLI(FakeAPI(test_response=APIResponse(True, "plain text"))))

    assert command.execute(args(timeout=10)) == 0
    assert "0.000s" in capsys.readouterr().out


# --- cache -----------------------------------------------------------------


@pytest.fixture
def cache_cli(tmp_path):
    """A cache manager rooted in tmp_path, so nothing touches the real one."""
    from igntui.core.cache import CacheManager

    manager = CacheManager(cache_dir=str(tmp_path), default_ttl=1234)
    return FakeCLI(FakeAPI(cache_manager=manager))


def test_cache_info_reports_an_empty_cache(cache_cli, capsys, tmp_path):
    assert CacheCommand(cache_cli).execute(args(cache_action="info")) == 0
    out = capsys.readouterr().out
    assert str(tmp_path) in out
    # The session's configured TTL, not a fresh CacheManager's 3600 default.
    assert "1234" in out


def test_cache_info_is_the_default_action(cache_cli, capsys):
    assert CacheCommand(cache_cli).execute(args(cache_action=None)) == 0
    assert "Cache Information" in capsys.readouterr().out


def test_cache_stats_reports_the_counters(cache_cli, capsys):
    assert CacheCommand(cache_cli).execute(args(cache_action="stats")) == 0
    out = capsys.readouterr().out
    for field in ("hit_rate", "memory_entries", "disk_entries"):
        assert field in out


def test_cache_clear_with_force_removes_entries(cache_cli, capsys, tmp_path):
    cache_cli.api.cache_manager.set("some-key", "value")
    assert list(tmp_path.glob("*.cache"))

    assert CacheCommand(cache_cli).execute(args(cache_action="clear", force=True)) == 0
    assert not list(tmp_path.glob("*.cache"))


def test_cache_clear_without_force_asks_first(cache_cli, capsys, tmp_path, monkeypatch):
    cache_cli.api.cache_manager.set("some-key", "value")
    monkeypatch.setattr("builtins.input", lambda *_: "n")

    CacheCommand(cache_cli).execute(args(cache_action="clear", force=False))

    assert list(tmp_path.glob("*.cache")), "declining the prompt must keep the cache"


def test_unknown_cache_action_is_a_failure(cache_cli, capsys):
    assert CacheCommand(cache_cli).execute(args(cache_action="nope")) == 1
    assert "nope" in capsys.readouterr().out


def test_cache_clear_expired_keeps_valid_entries(cache_cli, capsys, tmp_path):
    """`--expired` is the on-demand replacement for the old startup sweep."""
    manager = cache_cli.api.cache_manager
    manager.set("keep-me", "v")
    manager.set("stale", "v", ttl=-1)

    assert (
        CacheCommand(cache_cli).execute(args(cache_action="clear", force=False, expired=True)) == 0
    )

    out = capsys.readouterr().out
    assert "1 expired" in out
    assert manager.get("keep-me") == "v"
    assert len(list(tmp_path.glob("*.cache"))) == 1


def test_cache_clear_expired_says_so_when_there_is_nothing_to_do(cache_cli, capsys):
    cache_cli.api.cache_manager.set("keep-me", "v")

    CacheCommand(cache_cli).execute(args(cache_action="clear", force=False, expired=True))

    assert "No expired entries" in capsys.readouterr().out


def test_cache_clear_expired_does_not_prompt(cache_cli, capsys, monkeypatch):
    """It removes only what is already dead, so there is nothing to confirm."""

    def refuse(*_):
        raise AssertionError("--expired must not prompt")

    monkeypatch.setattr("builtins.input", refuse)
    cache_cli.api.cache_manager.set("stale", "v", ttl=-1)

    assert (
        CacheCommand(cache_cli).execute(args(cache_action="clear", force=False, expired=True)) == 0
    )
