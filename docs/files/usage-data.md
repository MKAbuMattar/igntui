# ~/.igntui.usage.toml

## NAME

`~/.igntui.usage.toml` — persistent counter of recently-used templates

## LOCATION

`~/.igntui.usage.toml`. Path is fixed (no override flag).

## SYNOPSIS

```json
{
  "python": { "count": 7, "last_used": 1714209487.123 },
  "node": { "count": 4, "last_used": 1714209412.456 },
  "macos": { "count": 4, "last_used": 1714209380.789 },
  "rust": { "count": 1, "last_used": 1714209100.234 }
}
```

## DESCRIPTION

The file records how many times the user has selected each template and
when. The TUI uses this data to **pin recently-used templates to the top**
of the Available Templates panel within the current filter result.

The file is written every time a template is added to the selection (either
in the TUI or implicitly via [`.igntui.cfg.toml`](igntui-cfg-toml.md)
auto-load — sidecar loads do not count as "uses").

It is **not** written by `igntui generate` from the CLI — only TUI
selections increment counters.

## SCHEMA

The file is a JSON object. Each top-level key is a template name. Each
value is an object with:

| Field       | Type    | Description                                     |
| ----------- | ------- | ----------------------------------------------- |
| `count`     | integer | Total number of times the template was selected |
| `last_used` | float   | Unix timestamp of the most recent selection     |

## RANKING

`UsageTracker.top(n)` orders entries by:

1. `count` descending — most-used first.
2. Ties broken by `last_used` descending — most recent first.

The top `behavior.max_recent_templates` entries (default `10`) that also
appear in the current filter result are surfaced at the top of the
Templates panel.

## OPTING OUT

Set `behavior.save_usage_stats = false` in [`~/.igntui.cfg.toml`](user-config.md)
to stop further writes. Existing entries are still loaded and used for
ranking unless the file is deleted.

To reset:

```
$ rm ~/.igntui.usage.toml
```

The file will be re-created on the next selection.

## ERROR HANDLING

| Scenario                     | Behavior                                       |
| ---------------------------- | ---------------------------------------------- |
| File missing                 | Loaded as empty; first record creates the file |
| File exists but invalid JSON | Warning logged, treated as empty               |
| Entry value not a dict       | That entry skipped silently                    |
| Filesystem write error       | Warning logged, in-memory state still updated  |

## SEE ALSO

- [User configuration](user-config.md)
- [Keyboard and mouse reference](../tui/keyboard-and-mouse.md)
