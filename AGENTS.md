# AGENTS.md — igntui

Instructions for AI agents working in this repo. Human contributors: see `README.md`,
`docs/`, and `.github/CONTRIBUTING.md`.

## What this is

A curses TUI **and** a CLI for generating `.gitignore` files from
[gitignore.io](https://www.toptal.com/developers/gitignore) templates. Shipped to PyPI as
`igntui`, with two console scripts: `igntui` (CLI + TUI) and `gitignore-tui` (TUI only).

```bash
pipx install igntui && igntui
```

~6,300 lines under `src/igntui/`, three runtime dependencies (`pyfiglet`, `tomli-w`, and
`windows-curses` on Windows only). One network dependency: the gitignore.io API. Everything
else is stdlib.

## Layout

- `src/igntui/main.py` — `main()` for the CLI, `tui_main()` for `gitignore-tui`. Argument
  parsing, logging setup, dispatch, top-level error handling.
- `src/igntui/app.py` — `run_tui()`: the `curses.wrapper` boundary. **This is the entry point
  the package uses.** (`tui/app.py` has a second, unused `main()` — see `ROADMAP.md` item 8.)
- `src/igntui/cli/` — `parser.py` builds the argparse tree and maps command names to classes;
  `base.py` holds `BaseCLI` (config + API handle) and the `CLICommand` interface;
  `setup.py` owns logging configuration; `commands/` is one file per subcommand.
- `src/igntui/core/` — everything with no terminal in it:
  - `config.py` — the config cascade and the `config` singleton.
  - `cache.py` — `CacheManager` (memory + disk, sha256-keyed) and `TemplateCache`.
  - `api/` — `client.py` (template list/content, cache-aware), `request_handler.py`
    (urllib, retries, rate limit), `response.py` (frozen `APIResponse`), `errors.py`.
  - `search.py` — fuzzy / exact / regex matching over template names.
  - `managed_block.py` — the marker format written into `.gitignore`.
  - `project_config.py` / `repo_config.py` / `usage.py` — the three TOML files on disk.
- `src/igntui/tui/` — `app.py` (`GitIgnoreTUI`, the main loop), `state.py` (`TUIState`
  dataclass), `event_handler.py` (keys and mouse), `actions.py` (save/export/dialogs),
  `renderer.py`, `lifecycle.py` (background API work), `updates.py` (the update messages),
  `curses_setup.py` (colour pairs).
- `src/igntui/ui/components/` — one class per panel or dialog. Pure drawing.
- `docs/` — user-facing reference, kept per command and per file format.
- `scripts/release_version.py` — version bookkeeping; CI runs `assert-consistent`.

## The five things that will bite you

**1. Cross-thread state goes through a queue, never a direct assignment.**
`tui/lifecycle.py` runs API calls on daemon threads. They post `StateUpdate` messages
(`updates.py`) onto `queue.Queue`; `GitIgnoreTUI._drain_updates()` is the *only* place those
become `state.X = Y`, and it runs on the main loop between renders. Mutating `TUIState` from a
worker thread reintroduces a bug that was already fixed once.

**2. `config` is a module-level singleton with import-time side effects.**
`core/config.py` ends with `config = Config()`. Importing it reads `~/.igntui.cfg.toml`,
migrates a legacy JSON file if present, and applies env overrides. Anything that needs an
isolated config in a test must construct `Config(config_path=...)` explicitly — and note that
`get_cache_dir()` calls `mkdir`, so it touches the filesystem.

**3. `Config.DEFAULT_CONFIG` is class-level nested state.**
`__init__` and `reset_to_defaults` `deepcopy` it on purpose. A shallow `{**DEFAULT_CONFIG}`
shares the section dicts, and `set()` then writes into the class attribute — leaking into
every later instance. There is a regression test; keep the deepcopy.

**4. The managed block is a file format, and it is in users' repos.**
`core/managed_block.py` writes two marked regions into `.gitignore`: the generated content
between `# >>> igntui >>>` / `# <<< igntui <<<`, then a custom-patterns region whose body is
read out of the existing file and re-emitted verbatim. Changing marker text without
recognising the old text on read means the next save appends a second block instead of
replacing the first. Tests pin the exact strings.

**5. The cache key is a sha256 prefix, not a name.**
`TemplateCache._make_content_key` sorts and lowercases the template list, then hashes it.
Cache filenames are therefore stable across processes but say nothing about their contents —
which is why the name-matching invalidation helper does not work (`ROADMAP.md` item 7).

## Config cascade

```
DEFAULT_CONFIG → ~/.igntui.cfg.toml → .igntui.repo.cfg.toml → IGNTUI_* env → CLI flags
```

The per-output sidecar (`.igntui.cfg.toml` next to the generated file) overlays *selection*
state — templates and search mode — on top of that. It does not override config knobs.
`docs/files/` documents each file; keep those pages in step with the code.

## Working commands

| Command | What it does |
|---|---|
| `uv sync --extra test --extra dev` | Install the project with the tools CI uses. |
| `uv run igntui` / `uv run igntui tui` | Run it. Needs a real TTY. |
| `uv run --frozen pytest -q` | Run the tests. No terminal required. |
| `uvx ruff check src tests` | Lint. |
| `uvx ty check --python .venv src/igntui` | Type-check. |
| `uv run --frozen pytest --cov --cov-report=term-missing` | Coverage. |
| `uv build` | Build sdist + wheel via `uv_build`. |
| `uv run python scripts/release_version.py status` | This checkout's version vs PyPI. |
| `grep -rnE '(#\|//) ?ponytail:' .` | Deferred-shortcut ledger. |

`uv run` outside the project directory resolves a *different* environment — it will happily
run a globally installed `igntui` and make it look like your change did nothing. Stay in the
repo root.

## Testing

Tests are pure: no network, no terminal, no home directory. Use `tmp_path` for anything that
touches disk and construct `Config(config_path=tmp_path / ...)` rather than importing the
singleton. The API layer is exercised through fakes, not live HTTP.

What tests cannot cover: the draw path (`ui/`, `tui/renderer.py`, `tui/curses_setup.py` are
excluded from coverage for this reason) and the mouse handling. **Verifying a TUI change means
running it in a terminal**, and the pull request template asks which one you used.

For a TUI change, check at 80×24 and again at something small like 45×13 — the panels
degrade rather than raising, so a broken layout is silent. Check with the mouse both enabled
and disabled (`ui.mouse_support`).

## Conventions

- **Type hints on new code.** `disallow_untyped_defs` is off; don't mass-annotate untouched
  functions in an unrelated change. `ty` is clean across `src/igntui` and CI enforces it.
- **`%s` deferred logging, not f-strings**, in anything that logs on a hot path. The API and
  cache layers were migrated deliberately.
- **`raise X from err`** in the API layer. Ruff `B904` enforces it.
- **Exceptions carry their cause.** `core/api/errors.py` has the hierarchy; don't raise bare
  `Exception` from a new failure mode.
- **Nothing writes to stdout while the TUI is running.** The terminal belongs to curses; use
  the status bar or the logger.
- Keep the dependency list where it is. Three runtime dependencies, one of them platform
  gated, and everything else stdlib.

## Hard rules

- **`uvx ruff check src tests`, `uvx ty check --python .venv src/igntui`, and
  `uv run --frozen pytest -q` must pass** before commit. All three are clean on `main`, so
  anything they report is yours.
- **Never edit the version by hand in one place.** It lives in `pyproject.toml` *and*
  `src/igntui/__init__.py`; `scripts/release_version.py apply <version>` writes both and rolls
  the changelog. CI fails if they disagree.
- **Add a `CHANGELOG.md` entry** under `## [Unreleased]` for anything a user would notice.
- **Update `docs/` in the same change.** Every command and every file format has a page; a
  flag that works but is undocumented is half-shipped.
- **Clean commits.** Conventional-commit subject + body. **No** `Co-Authored-By` trailer,
  **no** "Generated with Claude Code", **no** AI-assistant mention of any kind.
- **GPL-3.0-or-later.** Don't add a dependency under an incompatible licence.
- Push only when asked.
