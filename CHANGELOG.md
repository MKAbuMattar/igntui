# Changelog

All notable changes to igntui are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.1] — 2026-07-30

### Fixed

- **A failed cache write no longer destroys the entry it was replacing.**
  `_save_disk_cache` opened the target file with `"w"` — truncating it — and only
  then serialised the value. A crash, a full disk, or an unserialisable value
  left truncated JSON where a good entry had been; the next read logged a
  warning, deleted the file, and reported a miss. Writes now go to a temporary
  file in the same directory and are renamed into place, so a reader (including
  a second igntui process running at the same time) sees either the previous
  entry or the new one, never half of either.

## [0.3.0] — 2026-07-28

### Changed

- **The cache no longer reads itself into memory at startup.** `CacheManager`
  opened and parsed every `.cache` file in its constructor, and every command
  paid for it because `GitIgnoreAPI` builds a manager before doing anything.
  Measured over a realistic cache — 300 content blobs, 3.5 MiB — that was
  **~19 ms down to ~0.9 ms**. Nothing is lost: a read already fell back to disk
  and promoted what it found, so the eager pass bought latency and nothing else.

  One behaviour does change. That pass also deleted expired files, and nothing
  sweeps them automatically now. In practice a stale entry is short-lived — a
  content key is a hash of its template set, so requesting the same set again
  overwrites it in place — and only sets cached once and never asked for again
  linger.

### Added

- **`igntui cache clear --expired`** removes only entries past their TTL and
  keeps everything still valid, so the next run is not forced back to the
  network. This is the on-demand replacement for the startup sweep, and it gives
  `CacheManager.cleanup_expired()` — which had no callers at all — a home.

## [0.2.0] — 2026-07-27

### Added

- **A custom-patterns region in generated `.gitignore` files.** Alongside the
  managed block that holds template content, igntui now writes a second marked
  region:

  ```gitignore
  # >>> Start of custom patterns (do not edit between these markers; managed by igntui) <<<
  # >>> End of custom patterns (do not edit between these markers; managed by igntui) <<<
  ```

  Its contents are read out of the existing file and written back verbatim on
  every save, so project-specific rules have one obvious, labelled home instead
  of relying on "anywhere outside the markers". Rules outside both regions are
  still preserved. A file written by an earlier version gains an empty custom
  region on its next save; nothing is discarded and the block cannot be
  duplicated across repeated saves.

### Fixed

- **`--log-level` was parsed and then ignored**, and the `[logging]` config
  section had no reader at all. Both did nothing: file logging, rotation,
  `IGNTUI_LOG_LEVEL`, and the level itself. The implementation already existed in
  `cli/setup.py` and nothing called it — `main()` and `tui_main()` call it now.
- **`Config.set()` wrote into the class-level defaults.** The nested section
  dicts were shared with `Config.DEFAULT_CONFIG`, so one instance's write became
  the starting value for every instance built afterwards in the same process, and
  `reset_to_defaults()` could never undo it.
- **`igntui test` always reported `Response time: 0.000s` and `Status code: N/A`.**
  The timing lives in the response payload, not on the wrapper the command was
  reading. It now reports the real latency, the endpoint, and how many entries are
  cached.
- **The GPL licence text shipped in neither the wheel nor the sdist.** The SPDX
  metadata field was set, but the only thing that would have included the file was
  a `[tool.hatch.build]` table that this project's build backend never reads.
- **The README said MIT.** The LICENSE file, the badge, the package metadata, and
  the changelog all say GPL-3.0-or-later.
- Three type errors outside `core/`: an implicit shadow of `run_tui` in
  `__init__.py`, a bare `Optional` annotation in `tui/curses_setup.py` (which
  annotates nothing), and a possibly-`None` `stdscr` in the mouse handler.
- README: the development commands referenced `black`, `isort` and `mypy` — none
  of which CI runs — and a test path that does not exist; troubleshooting
  suggested `igntui cache --clear` instead of `igntui cache clear`.
- **`--config` and `--no-cache` never reached `igntui test`.** The command built
  its own `GitIgnoreAPI` instead of using the session's, so it tested a different
  configuration than the one in effect.
- **`igntui cache info` reported the wrong TTL.** It built its own
  `CacheManager`, which defaults to 3600 regardless of `api.cache_ttl` — and
  re-read every cache file from disk to do it.
- **The fish completion was missing `--log-level`**, which bash and zsh both
  offered. Found by a new test that compares each emitted script against the real
  argparse tree.

### Removed

- `src/igntui/utils/` — 287 lines of logging and performance-metric machinery that
  nothing imported, and the only module in the package at 0% coverage.
- `TemplateCache.invalidate_template_content()` and
  `GitIgnoreAPI.invalidate_template()`. Content cache keys have been sha256
  prefixes since 0.0.2, so matching a template name against a key could only ever
  hit by accident — and a short hex-ish name like `cafe` would delete unrelated
  entries. Neither had any caller. `igntui cache clear` is the honest operation.
- A second, unused `main()` in `tui/app.py` that duplicated `app.py:run_tui()`
  with different exit handling, plus `check_curses_availability()`, which was
  exported and never called.
- `MANIFEST.in`, which the `uv_build` backend does not read.

### Added for contributors

- `AGENTS.md` and `CLAUDE.md` cover the module layout, the queue-based threading
  model in the TUI, the config cascade, the managed-block format, and how to
  verify a change you cannot see in a diff.
- `ROADMAP.md` — what is queued, with the evidence for each item, plus what has
  been rejected on purpose.
- `scripts/release_version.py` owns the two files that carry the version, and CI
  now fails if they disagree. `.github/workflows/release.yml` publishes to PyPI
  from a `release/<version>` branch with a labelled pull request: preparing is
  repeatable, merging is the one irreversible step.
- CI type-checks all of `src/igntui` instead of only `core/`, which is what
  surfaced the three errors above, and gates `ruff format --check` now that the
  tree is formatted consistently (43 of 76 files disagreed with it before).
- Coverage 46% → 66%, aimed at the half that had none: `cli/parser.py` 14% → 100%,
  `completion_cmd.py` 0% → 93%, `tui/event_handler.py` 7% → 63%, `tui/state.py`
  54% → 84%, plus the `list` / `cache` / `test` command output paths and their exit
  codes. 201 tests, up from 96.
- Community health files: `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`,
  a pull request template, issue forms, `CODEOWNERS`, and `dependabot.yml`. Bug
  reports and TUI problems are separate forms because they need different
  evidence: "it looks wrong" is unactionable without the terminal emulator,
  `$TERM`, size, and locale, so that form asks for all four.
- `py.typed`, so the annotations are visible to anything installing this package.
- Dead configuration removed from `pyproject.toml`: the `[tool.hatch.*]` tables
  (inert under `uv_build`), `[tool.isort]` (which set a line length contradicting
  ruff's), and the `black` / `isort` / `flake8` / `mypy` / `hatch` / `pre-commit`
  dev dependencies that nothing invoked. The `uv_build` upper bound was widened so
  a current uv no longer warns on every build.

## [0.1.1] — 2026-04-27

### Changed

- **Minimum Python bumped to 3.11.** Unlocks stdlib `tomllib` directly and
  removes the `tomli` conditional runtime dep. Drops
  `Programming Language :: Python :: 3.10` from classifiers; CI matrix is
  now `3.11 / 3.12 / 3.13`.
- **`core/` passes `uvx ty check` clean (0 diagnostics).** Required step
  in CI between `ruff` and `pytest`. Achieved via:
  - `ApiConfig`, `UiConfig`, `BehaviorConfig`, `LoggingConfig`,
    `IgntuiConfig` `TypedDict` descriptors in `core/config.py` documenting
    the schema.
  - `Config._config` typed as `dict[str, Any]` so the recursive
    `get`/`set`/env-override descent type-checks cleanly.
  - `CacheManager(cache_dir=...)` accepts `str | Path` (was `str` only),
    matching how `config.get_cache_dir()` returns paths.

### Fixed

- Last 3 f-string log calls in `core/api/rate_limiter.py` and
  `core/api/client.py` migrated to `%s` deferred formatting.
- Updated stale example in `docs/reference/igntui.md` from
  `team.igntui.json` to `team.igntui.cfg.toml` to match the v0.1.0 file
  format.

## [0.1.0] — 2026-04-27

### Renamed

| Old (v0.0.x)           | New (v0.1.0)           | Format change |
| ---------------------- | ---------------------- | ------------- |
| `igntui.cfg.toml`      | `.igntui.cfg.toml`     | (none — TOML) |
| `~/.igntui.json`       | `~/.igntui.cfg.toml`   | JSON → TOML   |
| `~/.igntui_usage.json` | `~/.igntui.usage.toml` | JSON → TOML   |

All four files now follow one convention: `[.]igntui.[<scope>.]<role>.toml`.
Leading dot when the file lives inside a project tree, role tag (`cfg` /
`usage`) for purpose, always TOML on disk.

### Added

- **`.igntui.repo.cfg.toml`** — new team-shared repo configuration. Lives
  at any layer of the repo (discovered by walking up from CWD, bounded by
  `.git/` / `.hg/` / filesystem root). Sits between user config and the
  per-output sidecar in the cascade. Schema mirrors user config sections
  (`[api]`, `[ui]`, `[behavior]`, `[logging]`) plus an optional
  `[selection]` table that seeds new sidecars when none exists in CWD.
  See [`docs/files/igntui-repo-cfg-toml.md`](docs/files/igntui-repo-cfg-toml.md).
- New module `core/repo_config.py` with `find_repo_config()` and
  `RepoConfig.load()`.
- Tests: `tests/core/test_repo_config.py` (10 tests) and
  `tests/core/test_config_cascade.py` (7 tests covering the documented
  precedence cascade end-to-end).

### Changed

- **User configuration on-disk format is now TOML.** Schema is unchanged
  (`[api]`, `[ui]`, `[behavior]`, `[logging]`); only the wire format
  changes. TOML supports comments — your `~/.igntui.cfg.toml` can be
  documented inline.
- **Usage data on-disk format is now TOML.** Same `count` / `last_used`
  schema per template name.
- **Configuration cascade is documented and enforced**:

  ```
  DEFAULT_CONFIG → ~/.igntui.cfg.toml → .igntui.repo.cfg.toml → IGNTUI_* env → CLI flags
  ```

  The per-output sidecar overlays selection state (templates, search mode)
  on top of this cascade — it does not override config knobs.

### Migrations

On first launch, igntui v0.1.0 transparently migrates v0.0.x users:

- If `~/.igntui.json` exists and `~/.igntui.cfg.toml` does not, the JSON
  is read and a TOML file is written. The legacy JSON is **left in
  place** for the user to delete; an `info` log records the migration.
- Same one-shot conversion for `~/.igntui_usage.json` →
  `~/.igntui.usage.toml`.
- The legacy non-dotted sidecar `igntui.cfg.toml` is still **discovered**
  by the TUI (with a one-shot info log prompting rename), but new saves
  always write `.igntui.cfg.toml`.

All three legacy paths are scheduled for removal in v0.2.0.

### Documentation

- New page: [`docs/files/igntui-repo-cfg-toml.md`](docs/files/igntui-repo-cfg-toml.md)
  documenting the new repo configuration file.
- Every reference to old filenames swept across `docs/` and `README.md`.
- New "File Naming Convention" section published, documenting the
  `[.]igntui.[<scope>.]<role>.toml` contract going forward.

## [0.0.2] — 2026-04-27

### Added

- **Per-project sidecar `igntui.cfg.toml`.** Saving a `.gitignore` writes a small
  TOML next to it pinning the templates, search mode, and igntui version that
  produced it. Re-running `igntui` in the same directory restores that selection.
  Safe to commit to git. Opt out with `--no-sidecar` on the CLI.
- **Append-safe re-save with managed-block markers.** Generated content is
  wrapped between `# >>> igntui >>>` and `# <<< igntui <<<`. Re-saves replace
  only the managed block; user edits outside the markers are preserved verbatim.
- **`igntui generate --dry-run`** prints the resolved content to stdout without
  writing any file. Pairs with `--output FILE` to preview a target write.
- **Diff preview before overwrite.** Save-flow shows a unified diff between
  current and proposed `.gitignore` contents, with scrollable preview, before
  asking to apply. No-op writes short-circuit with a message.
- **Recently-used templates pinned to top** of the Templates panel. Persisted
  to `~/.igntui_usage.json`. Honors `behavior.max_recent_templates`.
- **Mouse support** in the TUI. Click to focus a panel; click a row in
  Templates to select; scroll wheel scrolls the panel under the cursor without
  changing focus.
- **Shell completion.** `igntui completion <bash|zsh|fish>` prints a completion
  script. Install with `eval "$(igntui completion zsh)"` (or save to your
  shell's completions directory).
- **`gitignore-tui` script honors flags.** `--version`, `--no-splash`, and
  `--verbose` now work on the dedicated TUI entry point.
- **`igntui cache info`** reports real cache contents — entry count, total
  bytes, oldest/newest timestamps. Previously looked for a non-existent
  `templates.json`.
- **Pytest suite** with 72 tests covering core (cache, search, managed-block,
  project-config, usage, API client) and the CLI generate command.
- **GitHub Actions CI** runs ruff + pytest on Python 3.10 / 3.11 / 3.12 plus a
  build sanity check.

### Changed

- **Disk content cache survives across processes.** Replaced
  `hash() % 1_000_000` with a 16-hex sha256 prefix, so cache filenames are
  stable between runs and collision-resistant. Legacy 6-digit-keyed entries
  are auto-purged on first launch.
- **CLI `--no-cache` and `--config` flags now actually work.** `--no-cache`
  forces fresh API fetches for the session; `--config PATH` loads an alternate
  config file.
- **TUI state is thread-safe.** Background workers post discriminated-union
  `StateUpdate` messages to a queue drained on the main loop; no more direct
  cross-thread mutation of `TUIState`.
- **Logging migrated to `%s` deferred formatting** in the API and cache layers,
  so log calls don't pay format cost when filtered out.
- **Exception chaining (`raise X from err`)** in the API layer preserves
  original tracebacks. Enforced by ruff `B904`.
- **Search-panel UX.** Esc inside Search now exits search mode (focus
  Templates); `q` / `Q` are usable as letters; Shift-Tab uses
  `curses.KEY_BTAB` instead of magic literal `353`.
- **Render path uses `stdscr.erase()`** instead of `clear()`, eliminating
  visible flicker. The About-dialog backdrop was rewritten to use one
  `addstr` per row instead of a 12 000-call `addch` loop.
- **`APIResponse` is now `frozen=True`** with a `with_data()` helper, removing
  the one mutation site in `client.py`.
- **Package metadata is internally consistent.** Single license
  (`GPL-3.0-or-later`), Python `>=3.10`, ruff/mypy/classifiers all aligned.
- **License classifier dropped per PEP 639** in favor of the
  `project.license` SPDX field.

### Fixed

- **TUI search now actually returns fuzzy/regex results.** Positional args to
  `SearchManager.search` were swapped in `tui/lifecycle.filter_templates`,
  causing every search to throw and silently fall back to substring matching.
- **`igntui cache clear` no longer crashes.** Added `clear_all` alias on
  `CacheManager`. The missing `--force` flag on the parser is also restored.
- **Mouse scroll wheel actually scrolls** the panel under the cursor — the
  viewport moves and the row counter updates. Earlier behavior fought the
  panel's auto-snap.

### Removed

- **`urllib3` dependency.** Code uses stdlib `urllib.request`; the declared
  dep was unused.
- **Duplicate `create_base_parser`** in `cli/base.py` (dead code; the
  canonical version lives in `cli/parser.py`).

## [0.0.1] — 2026-04-22

- Initial release.

[0.3.1]: https://github.com/MKAbuMattar/igntui/releases/tag/v0.3.1
[0.3.0]: https://github.com/MKAbuMattar/igntui/releases/tag/v0.3.0
[0.2.0]: https://github.com/MKAbuMattar/igntui/releases/tag/v0.2.0
[0.1.1]: https://github.com/MKAbuMattar/igntui/releases/tag/v0.1.1
[0.1.0]: https://github.com/MKAbuMattar/igntui/releases/tag/v0.1.0
[0.0.2]: https://github.com/MKAbuMattar/igntui/releases/tag/v0.0.2
[0.0.1]: https://github.com/MKAbuMattar/igntui/releases/tag/v0.0.1
