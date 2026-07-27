# igntui generate

## NAME

`igntui generate` — generate `.gitignore` content for one or more templates

## SYNOPSIS

```
igntui [global-options] generate <template>...
                                  [--output <file>]
                                  [--append]
                                  [--force]
                                  [--dry-run]
                                  [--no-sidecar]
```

## DESCRIPTION

Fetches one or more templates (concatenated server-side by gitignore.io) and
either prints the result to stdout or writes it to a file.

When writing to a file (`--output`), `igntui generate` performs two
additional actions by default:

1. **Writes two marked regions**: the generated content between
   `# >>> igntui >>>` … `# <<< igntui <<<`, then a custom-patterns region
   (`# >>> Start of custom patterns … <<<` … `# >>> End of custom patterns … <<<`)
   for your own rules. On re-save only the generated region is replaced; the
   custom region's contents are carried over verbatim, as is anything outside
   both regions. See [Managed blocks](../concepts/managed-blocks.md).
2. **Writes a sidecar** [`.igntui.cfg.toml`](../files/igntui-cfg-toml.md)
   alongside the output file, pinning the template list. Subsequent runs
   of `igntui` (TUI mode) in the same directory auto-load the sidecar.

Both behaviors can be opted out individually. `--append` skips the managed
block (writes raw content); `--no-sidecar` skips the sidecar.

Template names are validated and sanitized before being sent to the API:
non-alphanumeric characters other than `- _ + .` are stripped, names longer
than 100 characters are rejected, and patterns like `..`, `//`, `\\`, `<`,
`>`, `|` are refused as suspicious.

## OPTIONS

### `<template>...`

(positional, one or more) Template names. Space-separated. Names are
canonicalized to lowercase before being submitted to the API.

### `--output <file>`, `-o <file>`

(path) Write content to `<file>` instead of stdout. When omitted, content is
printed to stdout (pipeable, clean output with no header line).

### `--append`, `-a`

(boolean) Append to `<file>` instead of replacing it. Bypasses managed-block
markers — content is written raw with a separator comment. Mutually
exclusive with `--force` semantically (force has no effect when appending).
Default: false.

### `--force`, `-f`

(boolean) Overwrite an existing file without the interactive prompt.
Default: prompt for confirmation when file exists.

### `--dry-run`

(boolean) Resolve content but do **not** write any file. Content is printed
to stdout with a `# (dry-run — no file written)` comment on stderr. With
`--output FILE`, the byte count of what would be written is reported on
stderr. Default: false.

### `--no-sidecar`

(boolean) Skip writing the [`.igntui.cfg.toml`](../files/igntui-cfg-toml.md)
sidecar. Has no effect when `--output` is omitted (no sidecar is ever
written for stdout output). Default: false (sidecar is written).

## EXAMPLES

**Print to stdout:**

```
$ igntui generate python
# Created by https://www.toptal.com/developers/gitignore/api/python
...
```

**Combine multiple templates and write to a file:**

```
$ igntui generate python node macos --output .gitignore
✓ Generated .gitignore
✓ Wrote .igntui.cfg.toml
```

**Preview without writing:**

```
$ igntui generate python --output .gitignore --dry-run
# (dry-run — would write 3583 bytes to .gitignore)
# Created by https://www.toptal.com/developers/gitignore/api/python
...
```

**Re-generate without prompting (managed block is replaced; user edits
outside markers are preserved):**

```
$ igntui generate python node --output .gitignore --force
✓ Generated .gitignore
✓ Wrote .igntui.cfg.toml
```

**Append (bypasses markers, no sidecar refresh):**

```
$ igntui generate visualstudiocode --output .gitignore --append
✓ Appended to .gitignore
```

**Pipe to another tool:**

```
$ igntui generate python | grep -v __pycache__ > .gitignore.filtered
```

## OUTPUT

To stdout (when `--output` is omitted): the resolved `.gitignore` content,
verbatim from gitignore.io, no header.

To stderr (with `--dry-run`): a single `# (dry-run …)` comment.

When writing to a file: a one-line confirmation `✓ Generated <file>`, plus
`✓ Wrote .igntui.cfg.toml` if the sidecar was written.

## EXIT CODES

| Code | Meaning                                         |
| ---- | ----------------------------------------------- |
| `0`  | Success                                         |
| `1`  | API failure, empty content, or file write error |

## SEE ALSO

- [`igntui list`](igntui-list.md)
- [Managed blocks](../concepts/managed-blocks.md)
- [`.igntui.cfg.toml`](../files/igntui-cfg-toml.md)
- [Caching](../concepts/caching.md)
