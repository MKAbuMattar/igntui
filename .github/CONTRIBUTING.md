# Contributing

Thanks for wanting to improve igntui.

Two surfaces share one core: a CLI and a curses TUI over the same `core/` package. Most bugs
worth reporting live in the seam between them — a flag that the parser accepts and nothing
reads, a config key with no reader, a marker format that drifts from what is already sitting
in people's repositories.

## Setup

```bash
git clone https://github.com/MKAbuMattar/igntui
cd igntui
uv sync --extra test --extra dev
uv run igntui
```

**Stay in the repo root when you run `uv run`.** From anywhere else it resolves a different
environment and will happily run a globally installed `igntui`, which makes your change look
like it did nothing.

## Before you open a pull request

```bash
uvx ruff check src tests
uvx ty check --python .venv src/igntui
uv run --frozen pytest -q
```

All three are **clean on `main`**. If any of them reports something, it came from your change.
CI runs the same three, plus a build and a check that the two version files agree.

## Verifying a change you cannot see in a diff

The tests are pure: no network, no terminal, no home directory. That is deliberate, and it
means they cannot tell you whether the TUI *works*. For anything in `tui/` or `ui/`:

1. **Run it at 80×24, then at something small like 45×13.** The panels clip rather than
   raising, so a broken layout is silent — nothing will crash to tell you.
2. **Try it with the mouse off** (`mouse_support = false` in `~/.igntui.cfg.toml`). Mouse
   handling is the least covered path in the codebase.
3. **Check both entry points**: `igntui tui` and the standalone `gitignore-tui`.
4. **Exercise the save flow on a `.gitignore` that already has content**, including one with a
   managed block already in it. That is the path with real user data in it.

Write down what you actually did in the pull request template. "Lint passes" is not
verification of a terminal UI.

## Threading

`tui/lifecycle.py` runs API calls on daemon threads. They post `StateUpdate` messages onto a
`queue.Queue`; `GitIgnoreTUI._drain_updates()` is the **only** place those become
`state.X = Y`, and it runs on the main loop between renders.

Do not mutate `TUIState` from a worker thread. That bug has been fixed once already.

## The managed block is a file format

`core/managed_block.py` writes two marked regions into a user's `.gitignore`:

```
# >>> igntui >>> (do not edit between these markers; managed by igntui)
...generated content, replaced on every save...
# <<< igntui <<<

# >>> Start of custom patterns (do not edit between these markers; managed by igntui) <<<
...your own rules, carried over verbatim...
# >>> End of custom patterns (do not edit between these markers; managed by igntui) <<<
```

Those exact strings are already in files people have committed. If you change one, the next
save will not recognise the old text and will append a second block instead of replacing the
first — so any change has to keep reading the previous form. Tests pin both pairs.

## Configuration

```
DEFAULT_CONFIG → ~/.igntui.cfg.toml → .igntui.repo.cfg.toml → IGNTUI_* env → CLI flags
```

If you add a config key, add a reader for it in the same change. A documented key that nothing
reads is worse than no key: it looks like a feature. Two of those were found and fixed
recently — see `ROADMAP.md` items 2 and 9.

`Config` deep-copies `DEFAULT_CONFIG`. Keep it that way: a shallow copy shares the nested
section dicts and `set()` then writes into the class attribute.

## Scope

**One PR, one thing.** A branch carrying a feature plus an unrelated refactor plus a README
section is slower to review than the sum of its parts, and one blocking problem in any part of
it holds up all the rest.

Specifically, please don't:

- Add a flag without a reader, or a config key without a reader.
- Add a subcommand without a page under `docs/reference/`.
- Add a dependency for something the standard library does. Three runtime dependencies, one of
  them platform gated, is the budget.
- Leave superseded iterations of your own work in the diff (`do_thing`, `do_thing_v2`).

If you are unsure whether something is in scope, open an issue first. That is cheaper than
finding out after you have written it.

## Commits

Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `ci:`.

No `Co-Authored-By` trailer, no "Generated with …", no AI-assistant attribution of any kind in
the subject or body.

Never edit the version by hand. It lives in `pyproject.toml` **and**
`src/igntui/__init__.py`; `scripts/release_version.py apply <version>` writes both and rolls
the changelog. CI fails if they disagree.

## Licence

GPL-3.0-or-later. Contributions are accepted under the same licence. Don't add a dependency
under an incompatible one.
