# Managed Blocks

How igntui re-saves a `.gitignore` without clobbering your hand-edits.

## OVERVIEW

When [`igntui generate --output FILE`](../reference/igntui-generate.md)
or the TUI Save dialog writes a `.gitignore`, the generated content is
wrapped between two marker comments:

```
# >>> igntui >>> (do not edit between these markers; managed by igntui)
# Created by https://www.toptal.com/developers/gitignore/api/python
# Edit at https://www.toptal.com/developers/gitignore?templates=python
*.pyc
__pycache__/
...
# End of https://www.toptal.com/developers/gitignore/api/python
# <<< igntui <<<
```

On a re-save, only the region **between the markers** is replaced. Anything
above the BEGIN marker or below the END marker is preserved verbatim.

## WHY

Common workflow:

1. Run `igntui generate python --output .gitignore`.
2. Add a project-specific rule by hand: `secrets.local.json`.
3. Re-run `igntui generate python node --output .gitignore --force` to add
   another stack.

Without managed blocks, step 3 would overwrite step 2's edit. With managed
blocks, the hand-edited rule survives because it lives outside the markers.

## EXACT MARKERS

```
BEGIN_MARKER  = "# >>> igntui >>> (do not edit between these markers; managed by igntui)"
END_MARKER    = "# <<< igntui <<<"
```

These strings are matched **exactly**. Don't paraphrase them.

## MERGE BEHAVIOR

When writing `new_content` to a file with optional existing content
`existing`:

| `existing`                                | Behavior                                                    |
| ----------------------------------------- | ----------------------------------------------------------- |
| `None` or empty                           | Wrap `new_content` in markers; write                        |
| has both markers in correct order         | Replace text between markers; preserve above/below verbatim |
| has only one marker (or END before BEGIN) | Append a fresh wrapped block at the end + log a warning     |
| no markers                                | Append a wrapped block at the end (legacy file)             |

Idempotent: re-saving the same content yields exactly one marker pair.

## EXAMPLE

**Before re-save:**

```
# my custom rule
build/

# >>> igntui >>> (do not edit between these markers; managed by igntui)
*.pyc
# <<< igntui <<<

# more custom rules
*.log
```

**Re-save with new content `*.tmp`:**

```
# my custom rule
build/

# >>> igntui >>> (do not edit between these markers; managed by igntui)
*.tmp
# <<< igntui <<<

# more custom rules
*.log
```

The `# my custom rule`, `build/`, `# more custom rules`, and `*.log` lines
are untouched. The managed block contents went from `*.pyc` to `*.tmp`.

## OPTING OUT

To write content **without** the markers (legacy / manually-curated
workflow), use `--append`:

```
$ igntui generate python --output .gitignore --append
✓ Appended to .gitignore
```

`--append` writes raw content with a separator comment, and does not
refresh the [sidecar](../files/igntui-cfg-toml.md). It is mutually
exclusive with managed-block semantics.

## DIFF PREVIEW (TUI)

When saving from the TUI to an existing file, a `DiffPreviewDialog` shows
a unified diff between current and proposed contents before applying the
change. With managed blocks active, the diff is **small** — usually just
the lines inside the marker pair — making review fast.

If the diff is empty (no semantic change), the save is short-circuited
with a status message and the file is not rewritten.

## SEE ALSO

- [`igntui generate`](../reference/igntui-generate.md)
- [`.igntui.cfg.toml`](../files/igntui-cfg-toml.md)
- [TUI overview: ON SAVE](../tui/overview.md#on-save)
