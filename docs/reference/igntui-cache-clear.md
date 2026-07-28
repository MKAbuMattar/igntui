# igntui cache clear

## NAME

`igntui cache clear` — delete all cached entries

## SYNOPSIS

```
igntui [global-options] cache clear [--force] [--expired]
```

## DESCRIPTION

Removes every entry from the cache — both the in-memory layer (current
process; effectively a no-op since CLI invocations are short-lived) and
every `*.cache` file in the cache directory.

After clearing, the next run of [`igntui list`](igntui-list.md) or
[`igntui generate`](igntui-generate.md) will hit the API.

With `--expired`, only entries past their TTL are removed and everything
still valid is kept, so the next run is not forced back to the network.

## OPTIONS

### `--force`

(boolean) Skip the interactive confirmation prompt. Default: prompt with
`Clear cache? This will remove all cached data. (y/N):`.

### `--expired`

(boolean) Remove only entries whose TTL has passed. Implies no prompt —
there is nothing to confirm, since everything it deletes is already dead.

Nothing sweeps expired files automatically: doing it at startup meant every
command paid to read the whole cache first. See
[Caching](../concepts/caching.md) for why, and note that a stale entry is
usually overwritten in place the next time the same template set is
requested — this flag is for sets that were cached once and never asked for
again.

## EXAMPLES

**Clear with confirmation:**

```
$ igntui cache clear
Clear cache? This will remove all cached data. (y/N): y
Cache cleared successfully
```

**Clear unattended (CI / scripting):**

```
$ igntui cache clear --force
Cache cleared successfully
```

**Sweep only what has expired, keeping valid entries:**

```
$ igntui cache clear --expired
Removed 3 expired entries
```

## OUTPUT

On success: a single line `Cache cleared successfully`, or with `--expired`,
`Removed N expired entries` (`No expired entries` when there was nothing to
do).

## EXIT CODES

| Code | Meaning                                   |
| ---- | ----------------------------------------- |
| `0`  | Success (or user said "no" at the prompt) |
| `1`  | User cancelled, or filesystem error       |

## SEE ALSO

- [`igntui cache info`](igntui-cache-info.md)
- [`igntui cache stats`](igntui-cache-stats.md)
- [Caching](../concepts/caching.md)
