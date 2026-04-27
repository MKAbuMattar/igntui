"""Tests for `igntui generate`.

Covers:
- managed-block markers on first save (Phase 2.5)
- managed-block preserves user content on re-save (Phase 2.5)
- sidecar written on default save, skipped with --no-sidecar (Phase 2.4)
- --dry-run prints content + writes nothing (Phase 1.5)
"""

import argparse
from unittest.mock import MagicMock

from igntui.cli.commands.generate_cmd import GenerateCommand
from igntui.core.api.response import APIResponse
from igntui.core.managed_block import BEGIN_MARKER, END_MARKER
from igntui.core.project_config import SIDECAR_FILENAME, ProjectConfig


def _make_args(**overrides) -> argparse.Namespace:
    base = dict(
        templates=["python"],
        output=None,
        append=False,
        force=False,
        dry_run=False,
        no_sidecar=False,
        verbose=False,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


def _command_with_response(content: str) -> GenerateCommand:
    cli = MagicMock()
    cli.api.get_templates.return_value = APIResponse(success=True, data=content)
    return GenerateCommand(cli)


def test_dry_run_prints_content_and_writes_nothing(tmp_path, capsys):
    cmd = _command_with_response("GENERATED")
    out_file = tmp_path / ".gitignore"
    args = _make_args(output=out_file, dry_run=True, force=True)

    rc = cmd.execute(args)
    out = capsys.readouterr()

    assert rc == 0
    assert "GENERATED" in out.out
    assert "dry-run" in out.err
    assert not out_file.exists()


def test_first_save_wraps_in_markers_and_writes_sidecar(tmp_path):
    cmd = _command_with_response("GEN")
    out_file = tmp_path / ".gitignore"
    args = _make_args(output=out_file, force=True)

    rc = cmd.execute(args)
    assert rc == 0

    text = out_file.read_text(encoding="utf-8")
    assert BEGIN_MARKER in text
    assert END_MARKER in text
    assert "GEN" in text

    sidecar = tmp_path / SIDECAR_FILENAME
    assert sidecar.exists()
    cfg = ProjectConfig.load(sidecar)
    assert cfg is not None
    assert cfg.templates == ["python"]


def test_no_sidecar_flag_skips_sidecar(tmp_path):
    cmd = _command_with_response("GEN")
    out_file = tmp_path / ".gitignore"
    args = _make_args(output=out_file, force=True, no_sidecar=True)

    cmd.execute(args)

    assert out_file.exists()
    assert not (tmp_path / SIDECAR_FILENAME).exists()


def test_resave_preserves_user_edits_outside_markers(tmp_path):
    cmd = _command_with_response("FIRST")
    out_file = tmp_path / ".gitignore"

    # First save
    cmd.execute(_make_args(output=out_file, force=True))

    # User adds custom rules outside markers
    text = out_file.read_text(encoding="utf-8")
    out_file.write_text(text + "\n# custom user rule\n*.local\n", encoding="utf-8")

    # Re-save with new content
    cmd2 = _command_with_response("SECOND")
    cmd2.execute(_make_args(templates=["python", "node"], output=out_file, force=True))

    final = out_file.read_text(encoding="utf-8")
    assert "SECOND" in final
    assert "FIRST" not in final  # managed block replaced
    assert "# custom user rule" in final  # outside-marker content preserved
    assert "*.local" in final
    # Marker pair count is exactly 1 (idempotent)
    assert final.count(BEGIN_MARKER) == 1


def test_no_output_prints_to_stdout(capsys):
    cmd = _command_with_response("STDOUT_BODY")
    rc = cmd.execute(_make_args(output=None))
    out = capsys.readouterr()
    assert rc == 0
    assert "STDOUT_BODY" in out.out


def test_failure_response_returns_nonzero(capsys):
    cli = MagicMock()
    cli.api.get_templates.return_value = APIResponse(
        success=False, data="", error_message="boom"
    )
    cmd = GenerateCommand(cli)
    rc = cmd.execute(_make_args())
    out = capsys.readouterr()
    assert rc == 1
    assert "boom" in out.out
