# .igntui.repo.cfg.toml

## NAME

`.igntui.repo.cfg.toml` — team-shared repo configuration

## LOCATION

Anywhere along the directory walk-up from the current working directory,
**bounded** by the first repository marker (`.git/` or `.hg/`) or the
filesystem root. Conventionally placed at the repository root and
committed.

```
my-repo/
├── .git/
├── .igntui.repo.cfg.toml          # ← committed; team-shared
├── frontend/
│   └── (igntui run from here also discovers the file above)
└── backend/
    └── (same — walk-up finds it)
```

If a `.git/` boundary is encountered before any `.igntui.repo.cfg.toml`,
discovery returns no result — keeping per-repo config strictly inside the
repo.

## SYNOPSIS

```toml
[api]
base_url = "https://gitignore.internal.example.com/api"
timeout  = 5

[ui]
mouse_support = false

[behavior]
max_recent_templates = 5

[selection]
templates   = ["python", "node", "macos"]
search_mode = "fuzzy"
```

## DESCRIPTION

Provides team-wide defaults for an entire repository. Sits between the
user config and the per-output sidecar in the configuration cascade:

```
DEFAULT_CONFIG → ~/.igntui.cfg.toml → .igntui.repo.cfg.toml → IGNTUI_* env → CLI flags
```

The per-output sidecar [`.igntui.cfg.toml`](igntui-cfg-toml.md) overlays
**only selection state** (`templates`, `search_mode`, `output.path`) on top
of the cascade — it never overrides config knobs from the repo file.

When no per-output sidecar exists in CWD but the repo config defines
`[selection]`, the TUI uses those templates as the initial selection on
launch. The status bar reads:

```
✓ Seeded N templates from .igntui.repo.cfg.toml — Press 'c' to clear
```

## SCHEMA

The same four config sections recognized by
[`~/.igntui.cfg.toml`](user-config.md) (`[api]`, `[ui]`, `[behavior]`,
`[logging]`) plus an optional `[selection]` table.

### Config sections

See [User configuration](user-config.md#sections) for the full key list of
each section. Any keys present here override the user-config values for
contributors using this repo.

### `[selection]` table (repo-only)

| Field         | Type           | Default   | Description                                              |
| ------------- | -------------- | --------- | -------------------------------------------------------- |
| `templates`   | array<string>  | `[]`      | Default selection seeded into new sidecars.              |
| `search_mode` | string         | `"fuzzy"` | One of `fuzzy`, `exact`, `regex`. Restored on TUI launch when no sidecar is present. |

## DISCOVERY ORDER

Pseudocode:

```
def find_repo_config(cwd):
    current = cwd.resolve()
    while True:
        if (current / ".igntui.repo.cfg.toml").is_file():
            return current / ".igntui.repo.cfg.toml"
        if (current / ".git").exists() or (current / ".hg").exists():
            return None  # repo boundary — stop walking up
        if current.parent == current:
            return None  # filesystem root
        current = current.parent
```

This means:

- An `.igntui.repo.cfg.toml` sitting **outside** a repo (e.g., in `$HOME`)
  is **not** picked up — that's what `~/.igntui.cfg.toml` is for.
- Nested repos shadow their parent — the inner-most repo's config wins.
- A repo with no `.git/` and no `.hg/` walks all the way to `/`, but is
  unusual.

## EXAMPLES

### Internal mirror + team default selection

```toml
[api]
base_url   = "https://gitignore.internal.example.com/api"
user_agent = "igntui/0.1.0 (org=acme)"

[selection]
templates = ["python", "node", "macos"]
```

Every contributor cloning the repo gets:

- API requests routed through the org's gitignore mirror.
- A pre-seeded selection when they first run the TUI in the repo (until a
  per-output sidecar pins their own selection).

### Lock down behavior across a CI fleet

```toml
[behavior]
max_recent_templates = 0

[ui]
mouse_support = false

[logging]
level = "WARNING"
```

### Restrict TUI mouse support repo-wide

```toml
[ui]
mouse_support = false
```

## ERROR HANDLING

| Scenario                            | Behavior                                         |
| ----------------------------------- | ------------------------------------------------ |
| File not found in walk-up           | Cascade silently proceeds without it             |
| Malformed TOML                      | Warning logged, file ignored                     |
| `[selection].templates` not a list  | Warning logged, treated as empty                 |
| `[selection].search_mode` invalid   | Warning logged, treated as unset                 |
| Unknown sections / keys             | Ignored at read time                             |

## SEE ALSO

- [User configuration](user-config.md)
- [`.igntui.cfg.toml` (per-output sidecar)](igntui-cfg-toml.md)
- [Caching](../concepts/caching.md)
