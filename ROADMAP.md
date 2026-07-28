# Roadmap

Paced improvements. Each increment lands as its own conventional commit, must keep
`uvx ruff check src tests`, `uvx ty check --python .venv src/igntui` and
`uv run --frozen pytest -q` at zero findings, and gets a `CHANGELOG.md` entry.

Ordered by what an audit of the current tree actually exposed, not by what would be nice to
have. Every item names its evidence rather than an aspiration.

## Phase 1 — Defects

| # | Increment | Status |
|---|---|---|
| 1 | **`Config.set()` wrote into the class defaults.** `__init__` did `{**self.DEFAULT_CONFIG}` — a shallow copy that shares the nested section dicts with the class attribute. `set()` therefore mutated `Config.DEFAULT_CONFIG`, so the value leaked into every `Config` built afterwards in the same process and `reset_to_defaults()` could never restore anything. Reproduced with two instances and a fresh interpreter. | ✅ done — `deepcopy` in both places, with a regression test |
| 2 | **`--log-level` was parsed and then ignored, and `[logging]` had no reader.** `main()` only branched on `args.verbose` and called a three-line `basicConfig` on `BaseCLI`. The implementation that honours `--log-level`, the `[logging]` config section, file rotation and `IGNTUI_LOG_LEVEL` already existed in `cli/setup.py` and nothing called it. Two documented features did nothing. | ✅ done — `main()` and `tui_main()` call `cli/setup.py:setup_logging`; `BaseCLI.setup_logging` deleted |
| 3 | **`igntui test` always reported `0.000s` / `N/A`.** `GitIgnoreAPI.test_connection()` puts the probe's timing and endpoint inside `data`; the command read `response.response_time` and `response.status_code` off the wrapper, which it never populates. The one command whose job is diagnosing latency could not report it. | ✅ done — reads the payload, and shows the endpoint and cached-entry count |
| 4 | **Three `ty` diagnostics outside `core/`.** `run_tui = None` implicitly shadowed the imported function in `__init__.py`; `curses_setup.cleanup(stdscr: Optional = None)` used a bare `Optional`, which annotates nothing; `event_handler._panel_at` accessed `self.stdscr.getmaxyx()` on an attribute typed as possibly-`None`. CI only checked `core/`, so none of them were visible. | ✅ done — all three fixed and CI now checks all of `src/igntui` |
| 5 | **Nothing checked that the two version files agree.** The version lives in `pyproject.toml` and `src/igntui/__init__.py`; a mismatch would first appear as a mislabelled PyPI release. | ✅ done — `scripts/release_version.py` plus an `assert-consistent` step in CI |

## Phase 2 — Dead weight

Nothing here changed behaviour. Every item was evidence that something had been written and
then never wired up.

| # | Increment | Status |
|---|---|---|
| 6 | **`src/igntui/utils/` was unreachable.** 287 lines of `PerformanceLogger`, `JSONFormatter`, `LoggingManager`, `measure_performance` and `get_performance_stats`, re-exported by `utils/__init__.py`, imported by nothing. It was also the only module at 0% coverage of 147 statements. | ✅ done — both files deleted |
| 7 | **The cache invalidation helper could not work.** `TemplateCache.invalidate_template_content(name)` matched `name.lower() in key.lower()`, but keys became 16-hex sha256 prefixes in 0.0.2 — a template name can never appear in one, and a short hex-ish name (`ade`, `cafe`, `beef`) matched unrelated digests and deleted them. No callers anywhere. | ✅ done — it and `GitIgnoreAPI.invalidate_template` are gone, with a comment recording what a real implementation would need |
| 8 | **A second, unused TUI entry point.** `tui/app.py` ended with its own `main()` and `__main__` block duplicating `app.py:run_tui()`, with different exit handling. `tui/__init__.py` re-exported it, which is why a plain grep for the import missed it — the gate caught it. | ✅ done — deleted, with a comment naming the real boundary |
| 9 | **Dead curses-availability helpers.** `check_curses_availability()` was exported and never called. `print_curses_error()` was also unused while `app.py:run_tui` printed the same two lines inline. | ✅ done — the first deleted, the second now used by `run_tui` |
| 10 | **`MANIFEST.in` did nothing.** The build backend is `uv_build`; `MANIFEST.in` is a setuptools file. It also listed `.vscode/*.json` for inclusion in the distribution. | ✅ done — deleted |
| 11 | **Dead build config in `pyproject.toml`.** `[tool.hatch.*]` tables and their `fmt`/`lint` scripts were inert under `uv_build` and pointed at tools CI does not run; `[tool.isort]` set `line_length = 88` against ruff's 100; `flake8`/`black`/`isort`/`mypy`/`hatch`/`pre-commit` were declared dev dependencies nothing invoked. | ✅ done — removed, and the `uv_build` bound widened so current uv stops warning |
| 22 | **Two commands ignored the session's own objects.** `TestCommand.execute` constructed a fresh `GitIgnoreAPI`, so `--config` and `--no-cache` never reached `igntui test`; `CacheCommand.execute` constructed a fresh `CacheManager`, so `igntui cache info` reported the default TTL rather than the configured `api.cache_ttl` and re-read every cache file to do it. Found because a fake CLI injected into either one was silently bypassed. | ✅ done — both use `self.cli.api` |

## Phase 3 — Verification gaps

| # | Increment | Status |
|---|---|---|
| 12 | **46% coverage, concentrated in the wrong half.** `core/` was well covered; the CLI and TUI plumbing was not — `cli/parser.py` 14%, `main.py` 10%, `tui/event_handler.py` 7%, `completion_cmd.py` 0%. Now 62% overall: `parser.py` 100%, `completion_cmd.py` 93%, `event_handler.py` 63%, `state.py` 84%, and the `list` / `cache` / `test` command output paths covered. Still thin: `tui/actions.py` (12%), `tui/app.py` (16%), `main.py` (10%) — the dialog and curses-wiring layers, which need a different approach than pure unit tests. | in progress |
| 13 | **Shell completion is generated and never checked.** Three scripts with a hardcoded `_SUBCOMMANDS` list and per-command flag lists, none derived from the argparse tree. `tests/cli/test_completion_cmd.py` now compares the emitted scripts against what argparse actually knows — and immediately caught that the fish script was missing `--log-level`, which bash and zsh had. | ✅ done — drift is now a test failure |
| 14 | **`ruff format --check` failed on 43 of 73 files.** `ruff format` was configured but never run, and the tree was black-formatted at a different line length. | ✅ done — reformatted in one pass, and `ruff format --check` is now a CI step |
| 15 | **No release pipeline.** Publishing to PyPI was manual, which is the highest-impact thing in this repo to get wrong: PyPI forbids re-uploading a version, so a mistake burns the number permanently. | ✅ done — `scripts/release_version.py` plus `.github/workflows/release.yml`; preparing is repeatable on a labelled pull request, merging is the one irreversible step. First used for v0.2.0 |
| 23 | **The CLI surface is defined three times.** Each command class has an `add_arguments` method that **nothing calls** — `cli/parser.py` hardcodes the same subparsers and flags, and `completion_cmd.py` hardcodes them a third time for the shell scripts. The copies have already drifted: `GenerateCommand.add_arguments` is missing `--dry-run` and `--no-sidecar`, which the live parser has. That is why adding `cache clear --expired` meant editing three files. Not a mechanical fix — wiring `add_arguments` up as-is would silently drop flags — so it needs the class copies reconciled against the parser first, then one of the two deleted. The completion tests at least make the third copy's drift a test failure. | planned |
| 16 | **Branch protection does not require the checks.** CI runs on pull requests but is not a required status check, so a red pull request can still be merged. Repository setting, not a file in the tree. | planned |

## Phase 4 — Quality

| # | Increment | Status |
|---|---|---|
| 17 | **The TUI redraws everything every 100 ms whether or not anything changed.** `GitIgnoreTUI.run()` calls `renderer.render()` unconditionally each iteration, with `stdscr.timeout(100)` pacing the loop, plus a redundant `time.sleep(0.01)` after a `getch()` that has already blocked. Rendering on a dirty flag would cut the work to roughly nothing while idle. Not urgent — it is a template picker, not a game. | planned |
| 18 | **No minimum terminal size, but also no crash.** Probed at 120×40 down to 20×8: the TUI starts, degrades, and exits 0 at every size — panels clip rather than raising. So this is not a defect, it is an undocumented limit. Either state a supported minimum in `docs/tui/overview.md` or show a "terminal too small" message under some threshold. Deliberately *not* fixed by inventing a number. | planned |
| 19 | **`_load_persistent_cache` read every cache file at startup.** Every `.cache` file was opened and JSON-parsed in `CacheManager.__init__`, and every command paid it because `GitIgnoreAPI` builds a manager before doing anything. Benchmarked at 300 content blobs / 3.5 MiB: **18.8 ms → 0.9 ms**. `get()` already fell back to disk and promoted what it found, so the eager pass bought nothing. The expired-file sweep it also performed moved to `igntui cache clear --expired`, which gives the previously-callerless `cleanup_expired()` a home. *(`igntui --version` never paid, incidentally — argparse exits before `BaseCLI` is constructed.)* | ✅ done |
| 20 | **Disk cache writes are not atomic.** `_save_disk_cache` writes in place; a crash mid-write leaves truncated JSON. `_load_disk_cache` does handle the resulting `JSONDecodeError` by unlinking the file, so the failure mode is a lost entry rather than a crash — write to a temp file and `os.replace` to close it properly. | planned |
| 21 | **`windows-curses` is unbounded on Python version.** The marker is `sys_platform == 'win32'` with no upper version bound, unlike the sibling asciiquarium repo which caps it. If a Python release ships without a working `windows-curses` wheel, the install fails at resolve time rather than degrading. Worth confirming which versions actually have wheels before claiming 3.13. | planned |

## Rejected on purpose

- **A plugin system for templates.** The API returns a flat list of names; `SearchManager`
  filters it. There is nothing for a plugin to extend that a list comprehension does not
  already do.
- **Replacing curses with Textual or Rich.** It would add a dependency tree to a package with
  three dependencies, in exchange for abstractions this app does not use. The panels are
  already one class each.
- **A settings UI in the TUI.** Config is a documented TOML file with a documented cascade.
  Editing it in a curses dialog means a form layer, validation, and a write path for something
  users edit once.
- **Caching the rendered `.gitignore` per template set beyond the existing content cache.**
  The API response *is* the artifact; caching it twice at different granularities is two
  invalidation problems.
- **Vendoring the gitignore.io template list.** It would go stale silently, and the cache
  already covers the offline case for anything previously fetched.
