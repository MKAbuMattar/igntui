# Caching

How igntui's two-layer cache decides when to hit the API.

## OVERVIEW

igntui caches every API response on disk and in memory. Two cache categories:

- **Template list** — one entry under key `gitignore_templates_list`,
  populated by [`igntui list`](../reference/igntui-list.md) and the TUI
  startup load. Nothing is read into memory when a process starts; the first
  lookup pulls what it needs off disk and keeps it for the rest of the run.
- **Template content blobs** — one entry per unique template combination,
  populated by [`igntui generate`](../reference/igntui-generate.md) and the
  TUI's content panel.

## DIRECTORY LAYOUT

```
~/.cache/igntui/
├── gitignore_templates_list.cache       # full template list
├── gitignore_content_<sha256-prefix>.cache   # one per combination
└── gitignore_content_<sha256-prefix>.cache
```

Each `.cache` file is JSON with this shape:

```json
{
  "data": "<cached value>",
  "timestamp": 1714209487.123,
  "ttl": 3600,
  "access_count": 0,
  "last_access": null
}
```

## KEY DERIVATION

Content keys derive from a sorted, deduplicated, lowercased, comma-joined
string of template names, hashed with **sha256**. The first 16 hex
characters are used as the filename suffix:

```
sha256("node,python")[:16]  →  "ab23cd45ef678901"
key:  gitignore_content_ab23cd45ef678901
```

This guarantees:

- The same combination produces the same filename **across processes** —
  Python's randomized `hash()` is not used (legacy entries from pre-0.0.2
  are auto-purged on first launch).
- Different combinations are collision-resistant.
- Order, casing, and whitespace in the input do not change the key.

## TTL & EVICTION

Default TTL: `api.cache_ttl = 3600` seconds (1 hour). Override in
[`~/.igntui.cfg.toml`](../files/user-config.md) or via `IGNTUI_CACHE_TTL`.

| Trigger                        | Behavior                                |
| ------------------------------ | --------------------------------------- |
| Read finds entry within TTL    | Hit; `last_access` updated              |
| Read finds expired entry       | Evict (delete from memory + disk); miss |
| `igntui cache clear --expired` | Delete every `*.cache` file past its TTL |
| `igntui cache clear`           | Delete every `*.cache` file             |

**Nothing sweeps expired files on its own.** Construction used to read every
entry and delete the expired ones, but that cost every command the time to
open and parse the whole cache — around 19 ms over 300 content blobs — for no
benefit, since a read already falls back to disk on its own. Startup is lazy
now, and expired files are removed when something touches them, or on demand
with `igntui cache clear --expired`.

In practice a stale entry is short-lived anyway: a content key is a hash of its
template set, so asking for the same set again overwrites the expired entry in
place. Only sets that were cached once and never requested again linger.

There is no LRU / size-based eviction — the cache grows linearly with the
number of unique combinations the user has generated, plus the one
template-list entry. Run `igntui cache clear` periodically if disk usage
is a concern.

## TWO-LAYER MODEL

```
                    ┌─────────────┐
                    │  In-memory  │  ← O(1), per-process, lost at exit
                    └──────┬──────┘
                           │ miss
                    ┌──────▼──────┐
                    │     Disk    │  ← persistent, sha256-keyed
                    └──────┬──────┘
                           │ miss / expired
                    ┌──────▼──────┐
                    │ gitignore.io│  ← network call
                    └─────────────┘
```

A miss in memory promotes the disk hit into memory.

## BYPASSING THE CACHE

| How                                                           | Scope                                        |
| ------------------------------------------------------------- | -------------------------------------------- |
| [`--no-cache`](../reference/igntui.md#--no-cache) global flag | Per session — `force_refresh_default = True` |
| `force_refresh=True` in code                                  | Per call                                     |
| `igntui cache clear`                                          | Wipe everything; subsequent calls re-fetch   |

A bypassed read still **writes** the response to the cache. This means
`igntui --no-cache list` warms the cache for subsequent (non-`--no-cache`)
calls.

## OBSERVABILITY

| Command                                                    | Shows                                             |
| ---------------------------------------------------------- | ------------------------------------------------- |
| [`igntui cache info`](../reference/igntui-cache-info.md)   | dir, TTL, entry count, total bytes, oldest/newest |
| [`igntui cache stats`](../reference/igntui-cache-stats.md) | hit/miss counters (per process)                   |

## SEE ALSO

- [`igntui cache`](../reference/igntui-cache.md)
- [`igntui --no-cache`](../reference/igntui.md#--no-cache)
- [User configuration: `api`](../files/user-config.md#api)
