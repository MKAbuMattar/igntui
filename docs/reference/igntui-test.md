# igntui test

## NAME

`igntui test` — test connectivity to the gitignore.io API

## SYNOPSIS

```
igntui [global-options] test [--timeout <seconds>]
```

## DESCRIPTION

Issues a single live request to `<api.base_url>/list?limit=1` and reports
the result. Use to validate network connectivity, certificate trust, or
proxy configuration before running real workloads.

This command bypasses the cache for the test request. The cache **is**
written to with the response, so a successful `igntui test` warms up the
template list.

## OPTIONS

### `--timeout <seconds>`

(integer) Request timeout in seconds. Default: `10`.

## EXAMPLES

**Default timeout:**

```
$ igntui test
Testing connection to gitignore.io API...
Timeout: 10 seconds

Attempting to connect... SUCCESS

API Response:
  Response time: 0.345s
  From cache: No
  Status code: 200

✓ API is working correctly
```

**Stricter timeout for CI smoke tests:**

```
$ igntui test --timeout 3
```

## OUTPUT

On success: a multi-line block ending with `✓ API is working correctly`.

On failure: `Attempting to connect... FAILED` followed by the error
message. With `--verbose`, a Python traceback is appended.

## EXIT CODES

| Code | Meaning                             |
| ---- | ----------------------------------- |
| `0`  | API responded successfully          |
| `1`  | Network failure or non-200 response |

## SEE ALSO

- [`igntui --no-cache`](igntui.md#--no-cache)
- [Caching](../concepts/caching.md)
