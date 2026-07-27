"""Shell completion, which is hand-written and therefore drifts.

`_SUBCOMMANDS`, `_GLOBAL_FLAGS` and the per-command flag lists inside the three
templates are not derived from the argparse tree. Nothing stops a new subcommand
or flag from being invisible to every shell, so these tests compare the emitted
scripts against what argparse actually knows.
"""

import argparse

import pytest

from igntui.cli.commands.completion_cmd import _SUBCOMMANDS, CompletionCommand
from igntui.cli.parser import create_base_parser, create_command_parser

SHELLS = ["bash", "zsh", "fish"]


@pytest.fixture
def subparsers() -> dict:
    parser = create_command_parser(create_base_parser())
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action.choices
    raise AssertionError("no subparsers on the base parser")


def emit(shell: str, capsys) -> str:
    command = CompletionCommand(cli=None)
    assert command.execute(argparse.Namespace(shell=shell)) == 0
    return capsys.readouterr().out


def test_declared_subcommands_match_the_parser(subparsers):
    """The one list every template interpolates has to be the real one."""
    assert sorted(_SUBCOMMANDS) == sorted(subparsers)


@pytest.mark.parametrize("shell", SHELLS)
def test_script_is_emitted_and_mentions_every_subcommand(shell, capsys):
    out = emit(shell, capsys)
    assert out.strip()
    for command in _SUBCOMMANDS:
        assert command in out, f"{shell} completion never mentions {command}"


@pytest.mark.parametrize("shell", SHELLS)
def test_script_has_no_unsubstituted_placeholders(shell, capsys):
    """A missing `%(name)s` key raises; a stray `%(` would ship as literal text."""
    assert "%(" not in emit(shell, capsys)


@pytest.mark.parametrize("shell", SHELLS)
def test_global_flags_are_offered(shell, capsys):
    out = emit(shell, capsys)
    for flag in ("--version", "--verbose", "--log-level", "--config", "--no-cache"):
        # fish spells them `-l no-cache`, so match on the flag name, not the dashes.
        assert flag.lstrip("-") in out, f"{shell} completion is missing {flag}"


@pytest.mark.parametrize(
    "command,flag",
    [
        ("tui", "no-splash"),
        ("list", "filter"),
        ("list", "count"),
        ("generate", "output"),
        ("generate", "dry-run"),
        ("generate", "no-sidecar"),
        ("generate", "force"),
    ],
)
def test_per_command_flags_reach_every_shell(command, flag, capsys):
    for shell in SHELLS:
        out = emit(shell, capsys)
        assert flag in out, f"{shell} completion is missing {command} --{flag}"


def test_cache_actions_are_offered(subparsers, capsys):
    for shell in SHELLS:
        out = emit(shell, capsys)
        for action in ("info", "stats", "clear"):
            assert action in out, f"{shell} completion is missing cache {action}"


def test_zsh_script_declares_itself_compdef(capsys):
    """Without #compdef on the first line, zsh will not load it from $fpath."""
    assert emit("zsh", capsys).lstrip().startswith("#compdef igntui")


def test_both_console_scripts_are_completed(capsys):
    """`gitignore-tui` is a real entry point; completion should cover it too."""
    for shell in ("zsh", "fish"):
        assert "gitignore-tui" in emit(shell, capsys)
