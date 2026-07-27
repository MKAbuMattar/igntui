#!/usr/bin/env python3
"""Managed-block marker handling for `.gitignore` files.

A file written by igntui carries two marked regions:

    # >>> igntui >>> (do not edit between these markers; managed by igntui)
    ...generated template content...
    # <<< igntui <<<

    # >>> Start of custom patterns (do not edit between these markers; managed by igntui) <<<
    ...your own rules...
    # >>> End of custom patterns (do not edit between these markers; managed by igntui) <<<

The first region is rewritten on every save. The second is never touched: its
body is read out of the existing file and put back verbatim, so rules you add
there survive regeneration. Anything outside both regions is also preserved.
"""

import logging

logger = logging.getLogger(__name__)

BEGIN_MARKER = "# >>> igntui >>> (do not edit between these markers; managed by igntui)"
END_MARKER = "# <<< igntui <<<"

CUSTOM_BEGIN_MARKER = (
    "# >>> Start of custom patterns (do not edit between these markers; managed by igntui) <<<"
)
CUSTOM_END_MARKER = (
    "# >>> End of custom patterns (do not edit between these markers; managed by igntui) <<<"
)


def wrap(content: str, custom: str = "") -> str:
    """Render both regions: generated content, then the custom-patterns block."""
    body = content.rstrip("\n")
    custom_body = custom.strip("\n")
    custom_lines = f"{custom_body}\n" if custom_body else ""
    return (
        f"{BEGIN_MARKER}\n"
        f"{body}\n"
        f"{END_MARKER}\n"
        f"\n"
        f"{CUSTOM_BEGIN_MARKER}\n"
        f"{custom_lines}"
        f"{CUSTOM_END_MARKER}\n"
    )


def extract_custom(existing: str | None) -> str:
    """Read back whatever the user put in the custom-patterns block.

    Returns "" when the file has no custom block yet, or when the markers are
    present but out of order (in which case nothing can be safely carried over).
    """
    if not existing:
        return ""

    begin = existing.find(CUSTOM_BEGIN_MARKER)
    if begin == -1:
        return ""
    body_start = begin + len(CUSTOM_BEGIN_MARKER)
    end = existing.find(CUSTOM_END_MARKER, body_start)
    if end == -1:
        logger.warning(
            "custom-patterns block has no closing marker; its contents are left "
            "where they are rather than being moved into a new block"
        )
        return ""

    return existing[body_start:end].strip("\n")


def _strip_block(text: str, begin_marker: str, end_marker: str) -> str:
    """Remove one marked region from `text`, leaving the surrounding lines."""
    begin = text.find(begin_marker)
    if begin == -1:
        return text
    end = text.find(end_marker, begin + len(begin_marker))
    if end == -1:
        return text
    return text[:begin].rstrip("\n") + "\n\n" + text[end + len(end_marker) :].lstrip("\n")


def merge(existing: str | None, new_content: str) -> str:
    """Merge new generated content into an existing `.gitignore`.

    - No existing file or empty file → both regions, custom block empty.
    - Existing regions → generated content is replaced, the custom block's body
      is carried over unchanged, and text outside both is preserved.
    - Existing file without markers (legacy) → the regions are appended after it.
    - Malformed (END before BEGIN, or BEGIN without END) → a fresh pair of
      regions is appended and a warning logged; nothing is thrown away.
    """
    custom = extract_custom(existing)
    wrapped = wrap(new_content, custom)

    if not existing or not existing.strip():
        return wrapped

    begin_idx = existing.find(BEGIN_MARKER)
    end_idx = existing.find(END_MARKER, begin_idx + len(BEGIN_MARKER) if begin_idx != -1 else 0)

    # Both markers present and in the right order → splice both regions in place.
    if begin_idx != -1 and end_idx != -1 and end_idx > begin_idx:
        after_start = end_idx + len(END_MARKER)
        before = existing[:begin_idx].rstrip("\n")
        # The old custom block is dropped from the tail because its body has
        # already been read out and is being re-emitted inside `wrapped`.
        after = _strip_block(existing[after_start:], CUSTOM_BEGIN_MARKER, CUSTOM_END_MARKER).strip(
            "\n"
        )

        parts = []
        if before:
            parts.append(before + "\n\n")
        parts.append(wrapped)
        if after:
            parts.append("\n" + after + "\n")
        return "".join(parts)

    # Markers missing or malformed → append fresh regions.
    if begin_idx != -1 or existing.find(END_MARKER) != -1:
        logger.warning(
            "managed-block markers in existing file are malformed; appending a fresh block"
        )

    trimmed = _strip_block(existing, CUSTOM_BEGIN_MARKER, CUSTOM_END_MARKER).rstrip("\n")
    return f"{trimmed}\n\n{wrapped}" if trimmed else wrapped
