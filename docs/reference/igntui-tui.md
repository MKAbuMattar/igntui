# igntui tui

## NAME

`igntui tui` — launch the interactive Terminal User Interface

## SYNOPSIS

```
igntui [global-options] tui [--no-splash]
gitignore-tui [--no-splash] [--verbose] [--version]
```

## DESCRIPTION

Launches the interactive curses-based TUI. The TUI presents four panels
(Search, Available Templates, Selected, Generated Content) plus a status
bar.

If the working directory contains an [`.igntui.cfg.toml`](../files/igntui-cfg-toml.md)
sidecar, its `[selection]` is auto-loaded on launch and the status bar
reports `✓ Loaded N templates from .igntui.cfg.toml — Press 'c' to clear`.

This command is the **default** when `igntui` is invoked with no subcommand.

`gitignore-tui` is a separate console script that always launches the TUI.
It accepts its own argument set (subset of `igntui tui`'s flags); it does
**not** parse the global `igntui` flags.

## OPTIONS

### `--no-splash`

(boolean) Skip the splash screen on startup. Default: splash is shown.

The splash performs the initial template list fetch in the background; with
`--no-splash` the fetch is deferred to the first interaction with the
Templates panel.

## EXAMPLES

**Launch the TUI:**

```
$ igntui tui
```

**Launch without the splash screen:**

```
$ igntui tui --no-splash
```

**Launch via the dedicated script:**

```
$ gitignore-tui
$ gitignore-tui --no-splash
$ gitignore-tui --version
```

## OUTPUT

None to stdout under normal use — the TUI takes over the terminal until
the user quits with `q` or `Esc`. Errors during initialization are printed
to stderr.

When the TUI exits, control returns to the shell with the cursor at column
0 (curses cleanup is automatic).

## EXIT CODES

| Code | Meaning                                                  |
| ---- | -------------------------------------------------------- |
| `0`  | TUI exited normally (user quit)                          |
| `1`  | Initialization failed (no curses, terminal incompatible) |

## SEE ALSO

- [TUI overview](../tui/overview.md)
- [Keyboard and mouse reference](../tui/keyboard-and-mouse.md)
- [`.igntui.cfg.toml`](../files/igntui-cfg-toml.md)
