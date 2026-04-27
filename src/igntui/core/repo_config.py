"""Team-shared repo config (`.igntui.repo.cfg.toml`).

Discovered by walking up from CWD until a file with that name is found, or
the search is bounded by a repo marker (`.git/`, `.hg/`) or the filesystem
root.

The schema mirrors the user config's sections (`[api]`, `[ui]`, `[behavior]`,
`[logging]`) plus an optional `[selection]` table that seeds new sidecars
when none exist in CWD. The repo config sits between the user config and
the per-output sidecar in the cascade — see
`enhancement/INFORMATION_ARCHITECTURE.md`.
"""

import logging
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

REPO_CONFIG_FILENAME = ".igntui.repo.cfg.toml"
REPO_BOUNDARY_MARKERS = (".git", ".hg")


def find_repo_config(start: Path | None = None) -> Path | None:
    """Walk up from `start` looking for `.igntui.repo.cfg.toml`.

    Stops at:
    - the first `.igntui.repo.cfg.toml` found (returned),
    - a directory containing `.git/` or `.hg/` (no further walk-up — repo
      boundary),
    - the filesystem root.

    Returns `None` when no file is found within the bounded search.
    """
    current = (start or Path.cwd()).resolve()
    while True:
        candidate = current / REPO_CONFIG_FILENAME
        if candidate.is_file():
            return candidate
        # Repo boundary: stop search at top of the repo.
        for marker in REPO_BOUNDARY_MARKERS:
            if (current / marker).exists():
                return None
        parent = current.parent
        if parent == current:
            return None  # filesystem root
        current = parent


@dataclass
class RepoConfig:
    """Parsed `.igntui.repo.cfg.toml`. Sections beyond the documented set
    are ignored at read time but logged at debug level."""

    api: dict = field(default_factory=dict)
    ui: dict = field(default_factory=dict)
    behavior: dict = field(default_factory=dict)
    logging: dict = field(default_factory=dict)
    selection_templates: list[str] = field(default_factory=list)
    selection_search_mode: str | None = None
    path: Path | None = None

    @classmethod
    def load(cls, path: Path) -> "RepoConfig | None":
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
        except FileNotFoundError:
            return None
        except (OSError, tomllib.TOMLDecodeError) as e:
            logger.warning("Failed to load %s: %s", path, e)
            return None

        selection = data.get("selection", {}) or {}
        templates = selection.get("templates", [])
        if not isinstance(templates, list):
            logger.warning(
                "%s [selection].templates must be a list; ignoring", path
            )
            templates = []

        search_mode = selection.get("search_mode")
        if search_mode is not None and search_mode not in {"fuzzy", "exact", "regex"}:
            logger.warning(
                "%s [selection].search_mode=%r is invalid; ignoring", path, search_mode
            )
            search_mode = None

        return cls(
            api=data.get("api", {}) or {},
            ui=data.get("ui", {}) or {},
            behavior=data.get("behavior", {}) or {},
            logging=data.get("logging", {}) or {},
            selection_templates=[str(t) for t in templates],
            selection_search_mode=search_mode,
            path=path,
        )

    def has_selection(self) -> bool:
        return bool(self.selection_templates)
