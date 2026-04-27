# igntui cache

## NAME

`igntui cache` — manage the local template / content cache

## SYNOPSIS

```
igntui [global-options] cache <action> [action-options]
```

## DESCRIPTION

Top-level command for cache inspection and management. The cache is a
two-layer (in-memory + disk) store of:

- The full template list (one entry, key `gitignore_templates_list`).
- Generated `.gitignore` content per unique template combination
  (key prefix `gitignore_content_`, hashed by sha256).

Cache directory: `~/.cache/igntui/`. TTL is `api.cache_ttl` seconds (default
3600). See [Caching](../concepts/caching.md) for the full model.

If `<action>` is omitted, `cache info` is run.

## ACTIONS

| Action                           | Purpose                                 |
| -------------------------------- | --------------------------------------- |
| [`info`](igntui-cache-info.md)   | Print cache directory, TTL, entry count |
| [`stats`](igntui-cache-stats.md) | Print hit/miss counters                 |
| [`clear`](igntui-cache-clear.md) | Delete all cached entries               |

## EXAMPLES

**Inspect the cache:**

```
$ igntui cache info
```

**Clear the cache after a gitignore.io schema update:**

```
$ igntui cache clear --force
```

## SEE ALSO

- [`igntui cache info`](igntui-cache-info.md)
- [`igntui cache stats`](igntui-cache-stats.md)
- [`igntui cache clear`](igntui-cache-clear.md)
- [Caching](../concepts/caching.md)
