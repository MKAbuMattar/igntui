# TUI Overview

## NAME

`igntui` TUI — interactive curses interface for selecting templates and
generating a `.gitignore`

## LAUNCHING

```
igntui                        # default; with splash
igntui tui [--no-splash]      # explicit
gitignore-tui [--no-splash]   # alternate entry point
```

See [`igntui tui`](../reference/igntui-tui.md).

## LAYOUT

```
┌──────────────────────┬────────────────────────────────────────────┐
│ Search        (0)    │                                            │
├──────────────────────┤  Generated Content (3)                     │
│                      │                                            │
│ Available Templates  │                                            │
│ (1)                  │                                            │
│                      │                                            │
├──────────────────────┴────────────────────────────────────────────┤
│ Selected Templates (2)                                            │
├───────────────────────────────────────────────────────────────────┤
│ Status Bar                                                        │
└───────────────────────────────────────────────────────────────────┘
```

The numbers in parentheses are the **panel index** used by `Tab`/`Shift-Tab`
to cycle focus.

| Index | Panel               | Purpose                                              |
| ----- | ------------------- | ---------------------------------------------------- |
| 0     | Search              | Live filter input, current search mode               |
| 1     | Available Templates | Scrollable list, recents pinned to top, multi-select |
| 2     | Selected Templates  | Currently selected items                             |
| 3     | Generated Content   | Live preview of the generated `.gitignore`           |

## FOCUS MODEL

Exactly one panel is focused at a time. The focused panel:

- Has a highlighted border in the title color.
- Is the recipient of arrow keys, PgUp/PgDn, Home/End, Space, Enter.

`Tab` advances focus; `Shift-Tab` reverses. `/` jumps directly to the Search
panel. Mouse click focuses the panel under the cursor.

## STATUS BAR

The bottom-most line displays:

- **Status messages** (success: green; error: red) — auto-clear after 5 s.
- **Current panel index** and search mode.
- **Cache hit / load-progress notes** during async fetches.

## ASYNC OPERATIONS

Two operations run in background threads and post results to the main loop:

- **Template list load** — at startup (via splash or first launch) and on
  `r` / `F5` refresh.
- **Content generation** — every time the selection set changes.

The TUI remains responsive while these run; the status bar reports
progress.

## SIDECAR AUTO-LOAD

If the working directory contains an [`.igntui.cfg.toml`](../files/igntui-cfg-toml.md)
sidecar, its `[selection]` is loaded into the Selected panel before the
first render and a generation is triggered. Status bar shows:

```
✓ Loaded N templates from .igntui.cfg.toml — Press 'c' to clear
```

## ON SAVE

Pressing `s` opens a Save dialog. If the target file already exists:

- A [diff preview](../reference/igntui-generate.md) is rendered showing the
  unified diff between current and proposed contents.
- If the diff is empty (no-op), the save is short-circuited with a status
  message.
- Confirmation writes the file (preserving user-edited regions outside the
  managed-block markers — see [Managed blocks](../concepts/managed-blocks.md))
  and refreshes `.igntui.cfg.toml`.

## SEE ALSO

- [Keyboard and mouse reference](keyboard-and-mouse.md)
- [`.igntui.cfg.toml`](../files/igntui-cfg-toml.md)
- [Managed blocks](../concepts/managed-blocks.md)
