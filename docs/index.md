# igntui Documentation

Interactive Terminal User Interface and command-line tool for generating
`.gitignore` files from [gitignore.io](https://www.toptal.com/developers/gitignore)
templates.

## Where to start

| If you want to…                        | Read                                                                              |
| -------------------------------------- | --------------------------------------------------------------------------------- |
| Run a single command                   | [`igntui`](reference/igntui.md)                                                   |
| Use the interactive TUI                | [`igntui tui`](reference/igntui-tui.md) · [TUI keymap](tui/keyboard-and-mouse.md) |
| Generate a `.gitignore` from the shell | [`igntui generate`](reference/igntui-generate.md)                                 |
| Pin a project's selection across runs  | [`.igntui.cfg.toml` reference](files/igntui-cfg-toml.md)                           |
| Understand caching behavior            | [Caching](concepts/caching.md)                                                    |

## Reference

### CLI commands

- [`igntui`](reference/igntui.md) — top-level command (global flags)
- [`igntui tui`](reference/igntui-tui.md) — launch the interactive TUI
- [`igntui list`](reference/igntui-list.md) — list available templates
- [`igntui generate`](reference/igntui-generate.md) — generate `.gitignore` content
- [`igntui cache`](reference/igntui-cache.md) — cache management
  - [`igntui cache info`](reference/igntui-cache-info.md)
  - [`igntui cache stats`](reference/igntui-cache-stats.md)
  - [`igntui cache clear`](reference/igntui-cache-clear.md)
- [`igntui test`](reference/igntui-test.md) — test API connectivity
- [`igntui completion`](reference/igntui-completion.md) — emit shell completion script

### TUI

- [TUI overview](tui/overview.md) — panels, focus model, status bar
- [Keyboard and mouse](tui/keyboard-and-mouse.md) — full keymap

### File formats

- [`.igntui.cfg.toml`](files/igntui-cfg-toml.md) — per-output sidecar (next to `.gitignore`)
- [`.igntui.repo.cfg.toml`](files/igntui-repo-cfg-toml.md) — team-shared repo configuration
- [`~/.igntui.cfg.toml`](files/user-config.md) — user-level configuration
- [`~/.igntui.usage.toml`](files/usage-data.md) — recently-used templates

### Concepts

- [Caching](concepts/caching.md) — how disk + memory caches work
- [Managed blocks](concepts/managed-blocks.md) — append-safe `.gitignore` editing
- [Exit codes](concepts/return-codes.md) — what each non-zero exit means

## Conventions

This documentation uses the following conventions:

- `<value>` — required positional argument
- `[--flag]` — optional flag
- `[--flag VALUE]` — optional flag taking a value
- `option | option` — choice between alternatives
- `command...` — repeatable / variadic
- Code blocks beginning with `$` are shell commands; the `$` is the prompt and
  is not part of the command.

## Versioning

This documentation describes igntui **v0.0.2**. See
[CHANGELOG.md](../CHANGELOG.md) for the change history.
