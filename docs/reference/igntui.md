# igntui

## NAME

`igntui` — interactive TUI and CLI for generating `.gitignore` files

## SYNOPSIS

```
igntui [global-options] <command> [command-options]
igntui                                    # equivalent to: igntui tui
```

## DESCRIPTION

`igntui` is a single-binary tool with two modes:

- **Interactive TUI** — a curses-based interface with searchable templates,
  multi-selection, live preview, and save-to-file. Launched by running
  `igntui` with no subcommand, or explicitly via [`igntui tui`](igntui-tui.md).
- **Non-interactive CLI** — five subcommands (`list`, `generate`, `cache`,
  `test`, `completion`) for scripting and shell pipelines.

When invoked with no subcommand, `igntui` defaults to TUI mode (with splash).
Use `--no-splash` (TUI mode) or any explicit subcommand to bypass the splash.

The companion script `gitignore-tui` is a shortcut that always launches the
TUI; it accepts a smaller set of flags (see [`igntui tui`](igntui-tui.md)).

## SYNOPSIS — Available Commands

| Command                              | Purpose                       |
| ------------------------------------ | ----------------------------- |
| [`tui`](igntui-tui.md)               | Launch the interactive TUI    |
| [`list`](igntui-list.md)             | Print available templates     |
| [`generate`](igntui-generate.md)     | Generate `.gitignore` content |
| [`cache`](igntui-cache.md)           | Manage the local cache        |
| [`test`](igntui-test.md)             | Test API connectivity         |
| [`completion`](igntui-completion.md) | Emit shell completion script  |

## GLOBAL OPTIONS

These flags apply to every subcommand and must appear **before** the
subcommand name.

### `--version`, `-v`

(boolean) Print version, Python version, and OS, then exit. Output format:

```
igntui/<version> Python/<py-version> <OS>/<release>
```

### `--verbose`

(boolean) Enable debug-level logging. Equivalent to `--log-level DEBUG`.

### `--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}`, `-l`

(string) Set the logging level. Default: value of `logging.level` in
[`~/.igntui.cfg.toml`](../files/user-config.md), or `INFO`.

### `--config <path>`, `-c`

(path) Load configuration from `<path>` instead of the default
`~/.igntui.cfg.toml`. See [User configuration](../files/user-config.md).

### `--no-cache`

(boolean) Bypass the local cache for the entire session. All API requests are
fresh; results are still written to the cache for subsequent invocations
(without the flag) to use. See [Caching](../concepts/caching.md).

## ENVIRONMENT VARIABLES

The following environment variables override values from `~/.igntui.cfg.toml`.
Booleans accept `true`/`false`; numeric values are auto-detected.

| Variable             | Maps to                         |
| -------------------- | ------------------------------- |
| `IGNTUI_API_URL`     | `api.base_url`                  |
| `IGNTUI_API_TIMEOUT` | `api.timeout` (seconds)         |
| `IGNTUI_CACHE_TTL`   | `api.cache_ttl` (seconds)       |
| `IGNTUI_THEME`       | `ui.theme`                      |
| `IGNTUI_MOUSE`       | `ui.mouse_support`              |
| `IGNTUI_LOG_LEVEL`   | `logging.level`                 |
| `IGNTUI_MAX_RECENT`  | `behavior.max_recent_templates` |

## EXAMPLES

**Launch the TUI:**

```
$ igntui
```

**Generate a `.gitignore` for a Python project (TUI-free):**

```
$ igntui generate python --output .gitignore
```

**Force a fresh fetch (bypass cache):**

```
$ igntui --no-cache list --count
```

**Run with a project-specific config:**

```
$ igntui --config ./team.igntui.cfg.toml tui
```

## EXIT CODES

| Code | Meaning                                       |
| ---- | --------------------------------------------- |
| `0`  | Success                                       |
| `1`  | General failure (see stderr; use `--verbose`) |
| `2`  | Argument parse error (from argparse)          |

See [Exit codes](../concepts/return-codes.md) for details.

## SEE ALSO

- [`igntui tui`](igntui-tui.md)
- [`igntui generate`](igntui-generate.md)
- [User configuration](../files/user-config.md)
- [Caching](../concepts/caching.md)
