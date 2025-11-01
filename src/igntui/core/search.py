#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SearchMode(Enum):
    FUZZY = "fuzzy"
    EXACT = "exact"
    REGEX = "regex"


@dataclass
class SearchResult:
    item: str
    score: float
    match_positions: List[Tuple[int, int]]
    search_mode: SearchMode


@dataclass
class SearchResults:
    results: List[SearchResult]
    query: str
    search_mode: SearchMode
    search_time: float
    total_items: int

    def get_items(self) -> List[str]:
        return [result.item for result in self.results]


class SearchEngine(ABC):
    def __init__(self):
        self.stats = {
            "searches_performed": 0,
            "total_search_time": 0.0,
            "items_processed": 0,
        }

    @abstractmethod
    def search(
        self, items: List[str], query: str, max_results: int = 100
    ) -> SearchResults:
        pass

    def get_stats(self) -> Dict[str, Any]:
        avg_search_time = self.stats["total_search_time"] / max(
            1, self.stats["searches_performed"]
        )

        return {
            "searches_performed": self.stats["searches_performed"],
            "avg_search_time": avg_search_time,
            "total_items_processed": self.stats["items_processed"],
        }


class FuzzySearchEngine(SearchEngine):
    def __init__(self, case_sensitive: bool = False):
        super().__init__()
        self.case_sensitive = case_sensitive

    def search(
        self, items: List[str], query: str, max_results: int = 100
    ) -> SearchResults:
        start_time = time.time()

        if not query.strip():
            results = [
                SearchResult(item, 1.0, [], SearchMode.FUZZY)
                for item in items[:max_results]
            ]
        else:
            scored_results = []
            search_query = query if self.case_sensitive else query.lower()

            for item in items:
                search_item = item if self.case_sensitive else item.lower()
                score, positions = self._fuzzy_match(search_query, search_item)

                if score > 0:
                    scored_results.append(
                        SearchResult(item, score, positions, SearchMode.FUZZY)
                    )

            scored_results.sort(key=lambda x: (-x.score, x.item.lower()))
            results = scored_results[:max_results]

        search_time = time.time() - start_time

        self.stats["searches_performed"] += 1
        self.stats["total_search_time"] += search_time
        self.stats["items_processed"] += len(items)

        logger.debug(
            f"Fuzzy search for '{query}' found {len(results)} matches in {search_time:.3f}s"
        )

        return SearchResults(
            results=results,
            query=query,
            search_mode=SearchMode.FUZZY,
            search_time=search_time,
            total_items=len(items),
        )

    def _fuzzy_match(
        self, query: str, text: str
    ) -> Tuple[float, List[Tuple[int, int]]]:
        if not query:
            return 1.0, []

        if not text:
            return 0.0, []

        if query == text:
            return 1.0, [(0, len(text))]

        if query in text:
            start_pos = text.find(query)
            return 0.9, [(start_pos, start_pos + len(query))]

        query_chars = list(query)
        text_chars = list(text)

        matches = 0
        query_idx = 0
        positions = []

        for text_idx, text_char in enumerate(text_chars):
            if query_idx < len(query_chars) and text_char == query_chars[query_idx]:
                matches += 1
                positions.append((text_idx, text_idx + 1))
                query_idx += 1

        if matches == 0:
            return 0.0, []

        match_ratio = matches / len(query)
        length_penalty = 1.0 - (
            abs(len(text) - len(query)) / max(len(text), len(query))
        )

        start_bonus = 1.0
        if positions and positions[0][0] == 0:
            start_bonus = 1.2

        score = match_ratio * length_penalty * start_bonus * 0.8

        return min(score, 1.0), positions


class ExactSearchEngine(SearchEngine):
    def __init__(self, case_sensitive: bool = False):
        super().__init__()
        self.case_sensitive = case_sensitive

    def search(
        self, items: List[str], query: str, max_results: int = 100
    ) -> SearchResults:
        start_time = time.time()

        if not query.strip():
            results = [
                SearchResult(item, 1.0, [], SearchMode.EXACT)
                for item in items[:max_results]
            ]
        else:
            results = []
            search_query = query if self.case_sensitive else query.lower()

            for item in items:
                search_item = item if self.case_sensitive else item.lower()

                if search_query in search_item:
                    positions = []
                    start = 0
                    while True:
                        pos = search_item.find(search_query, start)
                        if pos == -1:
                            break
                        positions.append((pos, pos + len(search_query)))
                        start = pos + 1

                    score = len(search_query) / len(search_item)

                    if search_query == search_item:
                        score = 1.0

                    results.append(
                        SearchResult(item, score, positions, SearchMode.EXACT)
                    )

                if len(results) >= max_results:
                    break

            results.sort(key=lambda x: (-x.score, x.item.lower()))

        search_time = time.time() - start_time

        self.stats["searches_performed"] += 1
        self.stats["total_search_time"] += search_time
        self.stats["items_processed"] += len(items)

        logger.debug(
            f"Exact search for '{query}' found {len(results)} matches in {search_time:.3f}s"
        )

        return SearchResults(
            results=results,
            query=query,
            search_mode=SearchMode.EXACT,
            search_time=search_time,
            total_items=len(items),
        )


class RegexSearchEngine(SearchEngine):
    def __init__(self, case_sensitive: bool = False):
        super().__init__()
        self.case_sensitive = case_sensitive
        self._compiled_patterns = {}

    def search(
        self, items: List[str], query: str, max_results: int = 100
    ) -> SearchResults:
        start_time = time.time()

        if not query.strip():
            results = [
                SearchResult(item, 1.0, [], SearchMode.REGEX)
                for item in items[:max_results]
            ]
        else:
            results = []

            try:
                pattern = self._get_compiled_pattern(query)

                for item in items:
                    matches = list(pattern.finditer(item))

                    if matches:
                        positions = [(match.start(), match.end()) for match in matches]
                        total_match_length = sum(
                            end - start for start, end in positions
                        )
                        score = total_match_length / len(item)

                        results.append(
                            SearchResult(item, score, positions, SearchMode.REGEX)
                        )

                    if len(results) >= max_results:
                        break

                results.sort(key=lambda x: (-x.score, x.item.lower()))

            except re.error as e:
                logger.warning(f"Invalid regex pattern '{query}': {e}")
                results = []

        search_time = time.time() - start_time

        self.stats["searches_performed"] += 1
        self.stats["total_search_time"] += search_time
        self.stats["items_processed"] += len(items)

        logger.debug(
            f"Regex search for '{query}' found {len(results)} matches in {search_time:.3f}s"
        )

        return SearchResults(
            results=results,
            query=query,
            search_mode=SearchMode.REGEX,
            search_time=search_time,
            total_items=len(items),
        )

    def _get_compiled_pattern(self, pattern_str: str) -> re.Pattern:
        cache_key = (pattern_str, self.case_sensitive)

        if cache_key not in self._compiled_patterns:
            flags = 0 if self.case_sensitive else re.IGNORECASE
            self._compiled_patterns[cache_key] = re.compile(pattern_str, flags)

        return self._compiled_patterns[cache_key]


class SearchManager:
    def __init__(self, case_sensitive: bool = False):
        self.case_sensitive = case_sensitive

        self.engines = {
            SearchMode.FUZZY: FuzzySearchEngine(case_sensitive),
            SearchMode.EXACT: ExactSearchEngine(case_sensitive),
            SearchMode.REGEX: RegexSearchEngine(case_sensitive),
        }

        self.current_mode = SearchMode.FUZZY

        logger.debug(f"Initialized search manager with {len(self.engines)} engines")

    def search(
        self,
        items: List[str],
        query: str,
        mode: Optional[SearchMode] = None,
        max_results: int = 100,
    ) -> SearchResults:
        search_mode = mode or self.current_mode
        engine = self.engines[search_mode]

        return engine.search(items, query, max_results)

    def set_mode(self, mode: SearchMode) -> None:
        if mode in self.engines:
            self.current_mode = mode
            logger.debug(f"Switched to {mode.value} search mode")
        else:
            logger.warning(f"Unknown search mode: {mode}")

    def get_mode(self) -> SearchMode:
        return self.current_mode

    def get_stats(self) -> Dict[str, Any]:
        stats = {
            "current_mode": self.current_mode.value,
            "case_sensitive": self.case_sensitive,
            "engines": {},
        }

        for mode, engine in self.engines.items():
            stats["engines"][mode.value] = engine.get_stats()

        return stats

    def clear_caches(self) -> None:
        for engine in self.engines.values():
            if hasattr(engine, "_compiled_patterns"):
                engine._compiled_patterns.clear()

        logger.debug("Cleared search engine caches")
