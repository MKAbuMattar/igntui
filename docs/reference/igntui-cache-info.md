# igntui cache info

## NAME

`igntui cache info` — print cache directory, TTL, and entry count

## SYNOPSIS

```
igntui [global-options] cache info
igntui [global-options] cache             # 'info' is the default action
```

## DESCRIPTION

Prints high-level cache information without modifying state:

- Cache directory path
- Default TTL (seconds)
- Total cached entries (split into template list + content blobs)
- Total bytes on disk
- Oldest / newest entry timestamps

Reads `*.cache` files in the cache directory directly; does not contact the
API.

## OPTIONS

None.

## EXAMPLES

**Empty cache:**

```
$ igntui cache info
Cache Information:
  Location: /home/alice/.cache/igntui
  TTL: 3600 seconds
  Cached entries: 0
```

**Populated cache:**

```
$ igntui cache info
Cache Information:
  Location: /home/alice/.cache/igntui
  TTL: 3600 seconds
  Cached entries: 4
    template list: 1
    content blobs: 3
  Total size: 18,243 bytes
  Oldest entry: 2026-04-27 12:32:54
  Newest entry: 2026-04-27 12:33:07
```

## EXIT CODES

| Code | Meaning                       |
| ---- | ----------------------------- |
| `0`  | Success                       |
| `1`  | Cannot access cache directory |

## SEE ALSO

- [`igntui cache stats`](igntui-cache-stats.md)
- [`igntui cache clear`](igntui-cache-clear.md)
- [Caching](../concepts/caching.md)
