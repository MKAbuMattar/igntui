# igntui

Agent instructions for this repo live in **@AGENTS.md** — read it first. It covers the module
layout, the config cascade, the queue-based threading model in the TUI, the managed-block file
format, the working commands, and the hard rules (three checks pass, version bumped in one
place, changelog entry, docs updated, clean conventional commits).

## The three that bite hardest

1. **Background threads never touch `TUIState` directly.** They post `StateUpdate` messages to
   a queue; `_drain_updates()` on the main loop is the only writer.
2. **`core/config.py` runs `Config()` at import.** It reads the user's home directory and can
   write a migrated config file. Tests construct their own `Config(config_path=...)`.
3. **The managed-block markers are a file format already living in users' repos.** Both
   regions — generated content and custom patterns — are pinned by tests. Read
   `core/managed_block.py` before touching either.

## Before changing the TUI

You cannot verify a curses change by reading the diff. Run it at 80×24 and at ~45×13; the
panels degrade silently rather than raising. `uv run` must be invoked from the repo root or it
resolves a different, globally installed `igntui`.

Keep this file thin: put durable instructions in `AGENTS.md`, not here.
