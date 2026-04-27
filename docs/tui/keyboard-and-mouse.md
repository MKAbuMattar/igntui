# Keyboard and Mouse Reference

Complete input map for the [igntui TUI](overview.md).

## Quick reference

| Key                                | Effect                                               |
| ---------------------------------- | ---------------------------------------------------- |
| `Tab`                              | Focus next panel                                     |
| `Shift+Tab`                        | Focus previous panel                                 |
| `/`                                | Focus Search panel                                   |
| `Esc` (in Search)                  | Exit Search → focus Templates                        |
| `q` / `Q` / `Esc` (outside Search) | Quit                                                 |
| `Space` / `Enter` (in Templates)   | Toggle selection of highlighted template             |
| `Enter` (in Selected)              | Remove highlighted template from selection           |
| `s`                                | Save `.gitignore` (with diff preview if file exists) |
| `e`                                | Export selection as JSON                             |
| `r` / `F5`                         | Refresh template list from API                       |
| `c`                                | Clear all selections                                 |
| `a`                                | Select all visible (filtered) templates              |
| `x`                                | Remove all visible templates from selection          |
| `i`                                | Show app info dialog                                 |
| `h` / `?` / `F12`                  | Show help dialog                                     |
| `F1` / `F2` / `F3`                 | Switch search mode: Fuzzy / Exact / Regex            |

## Navigation keys

In any panel except Search:

| Key             | Effect                  |
| --------------- | ----------------------- |
| `↑` / `↓`       | Move selection by 1     |
| `PgUp` / `PgDn` | Move selection by 10    |
| `Home`          | Jump to top of panel    |
| `End`           | Jump to bottom of panel |

For the Content panel (read-only preview), the same keys scroll the
content rather than moving a cursor.

## Search panel

When focused (panel index 0) — typed characters become the filter query.
Live filtering re-runs on every keystroke.

| Key                | Effect                               |
| ------------------ | ------------------------------------ |
| ASCII printable    | Insert at cursor                     |
| `Backspace`        | Delete character before cursor       |
| `Delete`           | Delete character at cursor           |
| `←` / `→`          | Move cursor                          |
| `Home`             | Move cursor to start                 |
| `End`              | Move cursor to end                   |
| `Ctrl+A`           | Move cursor to start                 |
| `Ctrl+E`           | Move cursor to end                   |
| `Ctrl+U`           | Clear the entire query               |
| `F1` / `F2` / `F3` | Switch search mode (preserves query) |
| `Esc`              | Exit Search → focus Templates        |

## Search modes

| Mode  | Trigger | Behavior                                                          |
| ----- | ------- | ----------------------------------------------------------------- |
| Fuzzy | `F1`    | Subsequence match, scored by ratio + start-bonus + length-penalty |
| Exact | `F2`    | Case-insensitive substring                                        |
| Regex | `F3`    | Python `re` against each template name; invalid regex → empty     |

The current mode is shown in the Search panel title and in the status bar.

## Selection actions

| Key     | Where            | Effect                                     |
| ------- | ---------------- | ------------------------------------------ |
| `Space` | Templates        | Toggle add/remove the highlighted template |
| `Enter` | Templates        | Same as `Space`                            |
| `Enter` | Selected         | Remove the highlighted template            |
| `a`     | (any non-Search) | Add every visible (filtered) template      |
| `x`     | (any non-Search) | Remove every visible (filtered) template   |
| `c`     | (any non-Search) | Clear all selections (also clears preview) |

Each addition is recorded in `~/.igntui.usage.toml` (see
[Usage data](../files/usage-data.md)) and bumps the template's "recently
used" rank — recents are pinned to the top of the Templates panel within
the current filter.

## Mouse

When `ui.mouse_support` is `true` (default):

| Action               | Effect                                                        |
| -------------------- | ------------------------------------------------------------- |
| Left-click on panel  | Focus that panel                                              |
| Left-click on row    | Focus Templates panel + select that row + toggle on click     |
| Scroll wheel up/down | Scroll the panel under the cursor — does **not** change focus |

The scroll wheel scrolls the **viewport** (the "1-N/M" counter in the panel
title updates) and drags the selection cursor along only when it would
otherwise leave the visible window.

## Function-key map

| Key   | Effect                 |
| ----- | ---------------------- |
| `F1`  | Switch to Fuzzy search |
| `F2`  | Switch to Exact search |
| `F3`  | Switch to Regex search |
| `F5`  | Refresh template list  |
| `F12` | Show help dialog       |

## SEE ALSO

- [TUI overview](overview.md)
- [`igntui tui`](../reference/igntui-tui.md)
- [Usage data](../files/usage-data.md)
