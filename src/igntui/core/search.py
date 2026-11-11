"""Filter template names by fuzzy, exact, or regex match, best match first."""

import logging
import re
from enum import Enum

logger = logging.getLogger(__name__)


class SearchMode(Enum):
    FUZZY = "fuzzy"
    EXACT = "exact"
    REGEX = "regex"


def _fuzzy_score(query: str, text: str) -> float:
    if query == text:
        return 1.0
    if query in text:
        return 0.9

    # Greedy in-order character match. Partial matches still score, so a typo
    # ranks low instead of disappearing.
    positions = []
    qi = 0
    for ti, ch in enumerate(text):
        if qi < len(query) and ch == query[qi]:
            positions.append(ti)
            qi += 1
    if not positions:
        return 0.0

    match_ratio = len(positions) / len(query)
    length_penalty = 1.0 - abs(len(text) - len(query)) / max(len(text), len(query))
    start_bonus = 1.2 if positions[0] == 0 else 1.0
    return min(match_ratio * length_penalty * start_bonus * 0.8, 1.0)


def search(
    items: list[str], query: str, mode: SearchMode = SearchMode.FUZZY, max_results: int = 100
) -> list[str]:
    if not query.strip():
        return items[:max_results]

    scored: list[tuple[float, str]] = []
    if mode is SearchMode.FUZZY:
        q = query.lower()
        scored = [(s, item) for item in items if (s := _fuzzy_score(q, item.lower())) > 0]
    else:
        if mode is SearchMode.EXACT:
            q = query.lower()

            def score(item: str) -> float | None:
                text = item.lower()
                if q not in text:
                    return None
                return 1.0 if q == text else len(q) / len(text)
        else:
            try:
                pattern = re.compile(query, re.IGNORECASE)
            except re.error as e:
                logger.warning("Invalid regex pattern %r: %s", query, e)
                return []

            def score(item: str) -> float | None:
                # A zero-width match (`x*`) still counts as a hit, scored 0.
                spans = [m.end() - m.start() for m in pattern.finditer(item)]
                return sum(spans) / len(item) if spans else None

        # Exact and regex stop at the first max_results hits, then rank those.
        for item in items:
            if (s := score(item)) is not None:
                scored.append((s, item))
                if len(scored) >= max_results:
                    break

    scored.sort(key=lambda x: (-x[0], x[1].lower()))
    return [item for _, item in scored[:max_results]]
