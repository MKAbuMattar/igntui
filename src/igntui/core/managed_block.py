#!/usr/bin/env python3
"""Managed-block marker handling for `.gitignore` files.

igntui wraps the content it writes with `BEGIN` / `END` markers so re-saves
replace only the managed region; everything outside (user-added rules) is
preserved verbatim.
"""

import logging

logger = logging.getLogger(__name__)

BEGIN_MARKER = "# >>> igntui >>> (do not edit between these markers; managed by igntui)"
END_MARKER = "# <<< igntui <<<"


def wrap(content: str) -> str:
    """Wrap raw generated content with BEGIN/END markers."""
    body = content.rstrip("\n")
    return f"{BEGIN_MARKER}\n{body}\n{END_MARKER}\n"


def merge(existing: str | None, new_content: str) -> str:
    """Merge new managed content into an existing `.gitignore`.

    - No existing file or empty file → return wrapped content.
    - Existing file with markers → replace only the managed block.
    - Existing file without markers (legacy) → append managed block at end.
    - Malformed (END before BEGIN, or BEGIN without END) → append a fresh
      managed block at the end and log a warning.
    """
    wrapped = wrap(new_content)

    if not existing or not existing.strip():
        return wrapped

    begin_idx = existing.find(BEGIN_MARKER)
    end_idx = existing.find(END_MARKER)

    # Both markers present and in correct order → splice
    if begin_idx != -1 and end_idx != -1 and end_idx > begin_idx:
        before = existing[:begin_idx].rstrip("\n")
        after_start = end_idx + len(END_MARKER)
        after = existing[after_start:].lstrip("\n")

        parts = []
        if before:
            parts.append(before + "\n\n")
        parts.append(wrapped)
        if after:
            parts.append("\n" + after)
        return "".join(parts)

    # Markers missing or malformed → append fresh block
    if begin_idx != -1 or end_idx != -1:
        logger.warning(
            "managed-block markers in existing file are malformed; appending a fresh block"
        )

    trimmed = existing.rstrip("\n")
    return f"{trimmed}\n\n{wrapped}"
