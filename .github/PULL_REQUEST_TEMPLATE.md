<!-- What does this change, and why? One or two lines. -->

## Summary

## How you verified it

The tests are pure — no network, no terminal. **A passing test run is not evidence that the
TUI renders correctly.** If you touched `tui/` or `ui/`, tell us what you actually ran:

- Terminal emulator and OS:
- `$TERM` and terminal size:
- Tried it with `mouse_support = false` too:  yes / no / n/a
- Checked both `igntui tui` and `gitignore-tui`:  yes / no / n/a

## Checklist

- [ ] `uvx ruff check src tests` passes (zero findings on `main`)
- [ ] `uvx ty check --python .venv src/igntui` passes (also clean on `main`)
- [ ] `uv run --frozen pytest -q` passes
- [ ] Ran `uv run` **from the repo root** — from elsewhere it silently uses a globally
      installed igntui and your change appears to do nothing
- [ ] New flag or config key has a **reader**, not just a parser entry
- [ ] New subcommand or flag has a page (or a line) under `docs/`
- [ ] Touched the save path: tested against a `.gitignore` that already has content **and** one
      that already has a managed block — custom patterns survived
- [ ] Touched `TUIState` from a background thread: **no** (post a `StateUpdate` to the queue)
- [ ] No new dependency (three runtime deps is the budget, one platform gated)
- [ ] Nothing writes to stdout while the TUI is running
- [ ] `CHANGELOG.md` updated under `## [Unreleased]` if a user would notice the change
- [ ] Version **not** touched by hand — `scripts/release_version.py` owns both files
- [ ] Conventional-commit messages, no `Co-Authored-By` / AI-assistant trailer

<!--
RELEASING: don't edit versions here. Branch as release/<version>, open a PR to
main, add the `release` label. Preparing is safe and repeatable; MERGING is what
publishes to PyPI and cannot be undone. See the Releasing section in AGENTS.md.
-->

## Scope

- [ ] This PR does **one** thing. Unrelated features, refactors, and README sections belong in
      separate PRs — they are much slower to review together and one blocking problem holds up
      everything else in the branch.
