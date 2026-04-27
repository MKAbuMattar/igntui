# igntui cache clear

## NAME

`igntui cache clear` — delete all cached entries

## SYNOPSIS

```
igntui [global-options] cache clear [--force]
```

## DESCRIPTION

Removes every entry from the cache — both the in-memory layer (current
process; effectively a no-op since CLI invocations are short-lived) and
every `*.cache` file in the cache directory.

After clearing, the next run of [`igntui list`](igntui-list.md) or
[`igntui generate`](igntui-generate.md) will hit the API.

## OPTIONS

### `--force`

(boolean) Skip the interactive confirmation prompt. Default: prompt with
`Clear cache? This will remove all cached data. (y/N):`.

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

## OUTPUT

On success: a single line `Cache cleared successfully`.

## EXIT CODES

| Code | Meaning                                   |
| ---- | ----------------------------------------- |
| `0`  | Success (or user said "no" at the prompt) |
| `1`  | User cancelled, or filesystem error       |

## SEE ALSO

- [`igntui cache info`](igntui-cache-info.md)
- [`igntui cache stats`](igntui-cache-stats.md)
- [Caching](../concepts/caching.md)
