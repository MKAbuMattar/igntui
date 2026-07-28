"""The argparse tree and the command dispatch table.

Both are pure functions of their arguments, and both are places where a rename
disappears silently: a flag nothing reads still parses, and a subcommand missing
from the dispatch table only shows up as "Unknown command" at runtime.
"""

import argparse

import pytest

from igntui.cli.parser import (
    create_base_parser,
    create_command_parser,
    get_command_instance,
)

# Every subcommand the CLI advertises, and the flags each one owns. The
# completion scripts hardcode the same lists — see test_completion_cmd.py.
SUBCOMMANDS = ["tui", "list", "generate", "cache", "test", "completion"]
GLOBAL_FLAGS = ["--version", "--verbose", "--log-level", "--config", "--no-cache"]
COMMAND_FLAGS = {
    "tui": ["--no-splash"],
    "list": ["--filter", "--count"],
    "generate": ["--output", "--append", "--force", "--dry-run", "--no-sidecar"],
    "test": ["--timeout"],
}


@pytest.fixture
def parser() -> argparse.ArgumentParser:
    return create_command_parser(create_base_parser())


def _subparser_actions(parser: argparse.ArgumentParser) -> dict:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action.choices
    raise AssertionError("no subparsers on the base parser")


def test_every_subcommand_is_registered(parser):
    assert sorted(_subparser_actions(parser)) == sorted(SUBCOMMANDS)


@pytest.mark.parametrize("flag", GLOBAL_FLAGS)
def test_global_flag_parses(parser, flag):
    value = {"--log-level": "DEBUG", "--config": "cfg.toml"}.get(flag)
    argv = [flag, value] if value else [flag]
    if flag == "--version":
        # argparse exits on --version; that it is registered is the assertion.
        with pytest.raises(SystemExit):
            parser.parse_args(argv)
        return
    parser.parse_args(argv)


@pytest.mark.parametrize("command", sorted(COMMAND_FLAGS))
def test_command_owns_its_flags(parser, command):
    registered = {
        option
        for action in _subparser_actions(parser)[command]._actions
        for option in action.option_strings
    }
    missing = set(COMMAND_FLAGS[command]) - registered
    assert not missing, f"{command} lost {sorted(missing)}"


def test_log_level_only_accepts_real_levels(parser):
    parser.parse_args(["--log-level", "WARNING"])
    with pytest.raises(SystemExit):
        parser.parse_args(["--log-level", "LOUD"])


def test_completion_requires_a_supported_shell(parser):
    for shell in ("bash", "zsh", "fish"):
        assert parser.parse_args(["completion", shell]).shell == shell
    with pytest.raises(SystemExit):
        parser.parse_args(["completion", "powershell"])


def test_generate_requires_at_least_one_template(parser):
    assert parser.parse_args(["generate", "python"]).templates == ["python"]
    assert parser.parse_args(["generate", "python", "node"]).templates == [
        "python",
        "node",
    ]
    with pytest.raises(SystemExit):
        parser.parse_args(["generate"])


def test_cache_actions_are_registered(parser):
    for action in ("clear", "stats", "info"):
        assert parser.parse_args(["cache", action]).cache_action == action
    assert parser.parse_args(["cache", "clear", "--force"]).force is True
    assert parser.parse_args(["cache", "clear", "--expired"]).expired is True
    assert parser.parse_args(["cache", "clear"]).expired is False


def test_no_command_leaves_command_unset(parser):
    """`igntui` with no arguments falls through to the TUI in main()."""
    assert parser.parse_args([]).command is None


@pytest.mark.parametrize("command", SUBCOMMANDS)
def test_every_subcommand_has_a_dispatch_entry(command):
    """A subparser with no dispatch entry parses fine and then fails at runtime."""
    assert get_command_instance(command, cli_instance=None) is not None


def test_unknown_command_dispatches_to_nothing():
    assert get_command_instance("nope", cli_instance=None) is None
