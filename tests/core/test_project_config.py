"""Tests for the per-output sidecar (Phase 2.4 + Phase 6.1)."""


from igntui.core.project_config import (
    LEGACY_SIDECAR_FILENAME,
    SCHEMA_VERSION,
    SIDECAR_FILENAME,
    ProjectConfig,
    find_sidecar,
)


def test_round_trip_preserves_fields(tmp_path):
    p = tmp_path / SIDECAR_FILENAME
    cfg = ProjectConfig(
        templates=["python", "node"],
        search_mode="exact",
        output_path=".gitignore",
        preserve_user_edits=False,
    )
    cfg.dump(p)
    loaded = ProjectConfig.load(p)

    assert loaded is not None
    assert loaded.templates == ["python", "node"]
    assert loaded.search_mode == "exact"
    assert loaded.output_path == ".gitignore"
    assert loaded.preserve_user_edits is False
    assert loaded.schema_version == SCHEMA_VERSION
    assert loaded.igntui_version  # populated on dump


def test_load_missing_file_returns_none(tmp_path):
    assert ProjectConfig.load(tmp_path / "nonexistent.toml") is None


def test_load_malformed_toml_returns_none(tmp_path):
    p = tmp_path / SIDECAR_FILENAME
    p.write_text("this is not toml = = =")
    assert ProjectConfig.load(p) is None


def test_find_sidecar_present(tmp_path):
    (tmp_path / SIDECAR_FILENAME).write_text("schema_version = 1\n")
    assert find_sidecar(tmp_path) == tmp_path / SIDECAR_FILENAME


def test_find_sidecar_absent(tmp_path):
    assert find_sidecar(tmp_path) is None


def test_load_tolerates_missing_sections(tmp_path):
    p = tmp_path / SIDECAR_FILENAME
    p.write_text("schema_version = 1\n")
    cfg = ProjectConfig.load(p)
    assert cfg is not None
    assert cfg.templates == []
    assert cfg.search_mode == "fuzzy"


def test_load_rejects_non_list_templates(tmp_path):
    p = tmp_path / SIDECAR_FILENAME
    p.write_text(
        'schema_version = 1\n[selection]\ntemplates = "python"\n'
    )
    cfg = ProjectConfig.load(p)
    assert cfg is not None
    assert cfg.templates == []  # gracefully ignored


def test_dump_includes_metadata_lines(tmp_path):
    p = tmp_path / SIDECAR_FILENAME
    ProjectConfig(templates=["python"]).dump(p)
    content = p.read_text(encoding="utf-8")
    assert "# .igntui.cfg.toml" in content
    assert "safe to commit" in content
    assert "schema_version" in content
    assert "[selection]" in content
    assert "[output]" in content


def test_sidecar_filename_is_dotfile():
    """Phase 6.1: sidecar is hidden (leading dot)."""
    assert SIDECAR_FILENAME == ".igntui.cfg.toml"
    assert LEGACY_SIDECAR_FILENAME == "igntui.cfg.toml"


def test_find_sidecar_falls_back_to_legacy(tmp_path):
    """Phase 6.1: legacy non-dot file is still discovered for one release."""
    legacy_path = tmp_path / LEGACY_SIDECAR_FILENAME
    legacy_path.write_text("schema_version = 1\n")
    found = find_sidecar(tmp_path)
    assert found == legacy_path


def test_find_sidecar_prefers_new_over_legacy(tmp_path):
    """When both names exist, the dotfile wins."""
    legacy = tmp_path / LEGACY_SIDECAR_FILENAME
    legacy.write_text("schema_version = 1\n")
    new = tmp_path / SIDECAR_FILENAME
    new.write_text("schema_version = 1\n")
    assert find_sidecar(tmp_path) == new
