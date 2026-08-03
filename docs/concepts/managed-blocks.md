# Managed Blocks

How igntui re-saves a `.gitignore` without clobbering your hand-edits.

## OVERVIEW

When [`igntui generate --output FILE`](../reference/igntui-generate.md) or the TUI
Save dialog writes a `.gitignore`, it writes **two marked regions**:

```
# >>> igntui >>> (do not edit between these markers; managed by igntui)
# Created by https://www.toptal.com/developers/gitignore/api/python
# Edit at https://www.toptal.com/developers/gitignore?templates=python
*.pyc
__pycache__/
...
# End of https://www.toptal.com/developers/gitignore/api/python
# <<< igntui <<<

# >>> Start of custom patterns (edit freely; igntui preserves this block) <<<
secrets.local.json
*.local
# >>> End of custom patterns (edit freely; igntui preserves this block) <<<
```

- The **generated region** is replaced wholesale on every save. Nothing you put
  there survives — it belongs to the template content.
- The **custom-patterns region** is where your own rules go. igntui reads its
  body out of the existing file and writes it back unchanged on every save.
- Anything **outside both regions** is also preserved verbatim.

The custom region is written empty on a first save, so the place to put your own
rules is already there and labelled.

## WHY

Common workflow:

1. Run `igntui generate python --output .gitignore`.
2. Add a project-specific rule inside the custom-patterns region:
   `secrets.local.json`.
3. Re-run `igntui generate python node --output .gitignore --force` to add
   another stack.

Step 3 replaces the generated region and carries step 2's rule across untouched.
Rules written outside both regions survive too — the custom region exists so
there is one obvious, labelled place for them, and so a reader of the file knows
which lines igntui will overwrite.

## EXACT MARKERS

```
BEGIN_MARKER         = "# >>> igntui >>> (do not edit between these markers; managed by igntui)"
END_MARKER           = "# <<< igntui <<<"
CUSTOM_BEGIN_MARKER  = "# >>> Start of custom patterns (edit freely; igntui preserves this block) <<<"
CUSTOM_END_MARKER    = "# >>> End of custom patterns (edit freely; igntui preserves this block) <<<"
```

These strings are matched **exactly**. Don't paraphrase them — a marker igntui
does not recognise means the next save appends a second block instead of
replacing the first. They are pinned by tests for the same reason.

## MERGE BEHAVIOR

When writing `new_content` to a file with optional existing content `existing`:

| `existing`                                | Behavior                                                                     |
| ----------------------------------------- | ---------------------------------------------------------------------------- |
| `None` or empty                           | Write both regions; custom region empty                                      |
| has both markers in correct order         | Replace the generated region, carry the custom region's body over, preserve above/below verbatim |
| has a generated region but no custom one  | Add an empty custom region after it                                          |
| has only one marker (or END before BEGIN) | Append a fresh pair of regions at the end + log a warning; nothing discarded  |
| no markers                                | Append both regions after the existing content (legacy file)                 |
| custom BEGIN with no matching END         | Leave those lines where they are and start a new empty custom region + warn   |

Idempotent: re-saving yields exactly one of each marker, however many times you
run it.

## EXAMPLE

**Before re-save:**

```
# my custom rule
build/

# >>> igntui >>> (do not edit between these markers; managed by igntui)
*.pyc
# <<< igntui <<<

# >>> Start of custom patterns (edit freely; igntui preserves this block) <<<
secrets.local.json
# >>> End of custom patterns (edit freely; igntui preserves this block) <<<

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

# >>> Start of custom patterns (edit freely; igntui preserves this block) <<<
secrets.local.json
# >>> End of custom patterns (edit freely; igntui preserves this block) <<<

# more custom rules
*.log
```

`# my custom rule`, `build/`, `secrets.local.json`, `# more custom rules`, and
`*.log` are all untouched. Only the generated region went from `*.pyc` to
`*.tmp`.

## OPTING OUT

To write content **without** the markers (legacy / manually-curated workflow),
use `--append`:

```
$ igntui generate python --output .gitignore --append
✓ Appended to .gitignore
```

`--append` writes raw content with a separator comment, and does not refresh the
[sidecar](../files/igntui-cfg-toml.md). It is mutually exclusive with
managed-block semantics.

## DIFF PREVIEW (TUI)

When saving from the TUI to an existing file, a `DiffPreviewDialog` shows a
unified diff between current and proposed contents before applying the change.
With managed blocks active, the diff is **small** — usually just the lines inside
the generated region — making review fast.

If the diff is empty (no semantic change), the save is short-circuited with a
status message and the file is not rewritten.

## SEE ALSO

- [`igntui generate`](../reference/igntui-generate.md)
- [`.igntui.cfg.toml`](../files/igntui-cfg-toml.md)
- [TUI overview: ON SAVE](../tui/overview.md#on-save)
