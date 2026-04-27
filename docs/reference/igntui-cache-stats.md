# igntui cache stats

## NAME

`igntui cache stats` — print cache hit/miss counters

## SYNOPSIS

```
igntui [global-options] cache stats
```

## DESCRIPTION

Prints process-local cache counters. Note: counters are **not** persisted —
they reset every invocation. Each metric reflects activity in the current
`igntui cache stats` process only.

For long-running stats, watch the TUI; for static information about what's
on disk, use [`igntui cache info`](igntui-cache-info.md).

## OUTPUT FIELDS

| Field            | Meaning                                    |
| ---------------- | ------------------------------------------ |
| `hit_rate`       | hits / (hits + misses) — float in `[0, 1]` |
| `total_requests` | hits + misses                              |
| `memory_entries` | entries currently in the in-memory cache   |
| `disk_entries`   | `.cache` files in the cache directory      |
| `cache_dir`      | absolute path to the cache directory       |
| `default_ttl`    | TTL applied to fresh writes (seconds)      |
| `hits`           | counter of cache hits                      |
| `misses`         | counter of cache misses                    |
| `sets`           | counter of cache writes                    |
| `deletes`        | counter of explicit deletions              |
| `evictions`      | counter of expired-on-read evictions       |
| `disk_reads`     | counter of disk file loads                 |
| `disk_writes`    | counter of disk file saves                 |

## OPTIONS

None.

## EXAMPLES

```
$ igntui cache stats
Cache Statistics:
  hit_rate: 0.0
  total_requests: 0
  memory_entries: 4
  disk_entries: 4
  cache_dir: /home/alice/.cache/igntui
  default_ttl: 3600
  hits: 0
  misses: 0
  sets: 0
  deletes: 0
  evictions: 0
  disk_reads: 4
  disk_writes: 0
```

## EXIT CODES

| Code | Meaning                       |
| ---- | ----------------------------- |
| `0`  | Success                       |
| `1`  | Cannot access cache directory |

## SEE ALSO

- [`igntui cache info`](igntui-cache-info.md)
- [`igntui cache clear`](igntui-cache-clear.md)
- [Caching](../concepts/caching.md)
