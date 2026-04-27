# igntui list

## NAME

`igntui list` — print available `.gitignore` templates

## SYNOPSIS

```
igntui [global-options] list [--filter <pattern>] [--count]
```

## DESCRIPTION

Fetches the list of templates from gitignore.io (or the local cache) and
prints them to stdout. Output is alphabetized.

Without `--filter`, all templates are printed in a column-aligned grid (max
width ~80 characters). With `--filter`, only templates whose name contains
the substring are listed.

This command is read-only. It does not modify the cache except to populate
it with the template list (subject to `api.cache_ttl`).

## OPTIONS

### `--filter <pattern>`, `-f <pattern>`

(string) Substring filter (case-insensitive). Only templates whose name
contains `<pattern>` are listed. The match is plain substring; for fuzzy or
regex matching use the TUI ([`F1`/`F2`/`F3`](../tui/keyboard-and-mouse.md)).

### `--count`, `-c`

(boolean) Print the matching template count instead of the list. Pairs with
`--filter` to count filtered results.

## EXAMPLES

**List all templates:**

```
$ igntui list
Available templates (571):

ada                  agda                 al                   alteraquartusii
android              angular              ansible              apachecordova
...
```

**Count all templates:**

```
$ igntui list --count
Found 571 templates
```

**Find Python-related templates:**

```
$ igntui list --filter python
Available templates (4):

cpython              ipythonnotebook      jython               python
```

**Count templates matching a pattern:**

```
$ igntui list --filter rust --count
Found 2 templates
```

## OUTPUT

When listing: header `Available templates (N):`, blank line, then a
column-aligned grid. Trailing newline.

When counting: a single line `Found N templates`.

## EXIT CODES

| Code | Meaning                                                        |
| ---- | -------------------------------------------------------------- |
| `0`  | Success                                                        |
| `1`  | API failure or empty list (no matches when `--filter` was set) |

## SEE ALSO

- [`igntui generate`](igntui-generate.md)
- [`igntui cache`](igntui-cache.md)
- [Caching](../concepts/caching.md)
