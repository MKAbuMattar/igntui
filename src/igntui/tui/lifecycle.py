#!/usr/bin/env python3


import logging
import queue
import threading

from ..core.api import GitIgnoreAPI
from ..core.config import config
from ..core.search import SearchManager, SearchMode
from ..core.usage import UsageTracker
from .updates import (
    ContentGenerated,
    ContentGenerationFailed,
    GenerationCompleted,
    LoadCompleted,
    StateUpdate,
    TemplatesLoaded,
    TemplatesLoadFailed,
)

logger = logging.getLogger(__name__)


class TemplateLifecycle:
    def __init__(self, api: GitIgnoreAPI, search_manager: SearchManager):
        self.api = api
        self.search_manager = search_manager
        self.usage = UsageTracker()

    def load_templates_async(self, updates: "queue.Queue[StateUpdate]") -> None:
        def load_templates():
            try:
                logger.info("Loading templates from API")
                response = self.api.list_templates()
                if response.success:
                    templates = sorted(response.data, key=str.lower)
                    logger.info("Loaded %d templates", len(templates))
                    updates.put(TemplatesLoaded(templates))
                else:
                    msg = response.error_message or "Unknown error"
                    logger.error("Failed to load templates: %s", msg)
                    updates.put(TemplatesLoadFailed(f"Failed to load templates: {msg}"))
            except Exception as e:
                logger.error("Exception loading templates: %s", e)
                updates.put(TemplatesLoadFailed(f"Error: {e}"))
            finally:
                updates.put(LoadCompleted())

        threading.Thread(target=load_templates, daemon=True).start()

    def generate_content_async(
        self,
        templates: list[str],
        updates: "queue.Queue[StateUpdate]",
    ) -> None:
        if not templates:
            updates.put(ContentGenerationFailed("No templates selected", []))
            updates.put(GenerationCompleted())
            return

        def generate_content():
            try:
                logger.info("Generating content for %d templates", len(templates))
                response = self.api.get_templates(templates)
                if response.success:
                    logger.info("Generated %d chars", len(response.data))
                    updates.put(
                        ContentGenerated(response.data, response.from_cache, len(templates))
                    )
                else:
                    msg = response.error_message or "Unknown error"
                    logger.error("Failed to generate content: %s", msg)
                    updates.put(
                        ContentGenerationFailed(f"Generation failed: {msg}", list(templates))
                    )
            except Exception as e:
                logger.error("Exception generating content: %s", e)
                updates.put(ContentGenerationFailed(f"Error: {e}", list(templates)))
            finally:
                updates.put(GenerationCompleted())

        threading.Thread(target=generate_content, daemon=True).start()

    def filter_templates(
        self, templates: list[str], filter_text: str, search_mode: str = "fuzzy"
    ) -> list[str]:
        if not filter_text:
            return self._pin_recents(templates[:])

        try:
            mode = SearchMode(search_mode) if search_mode else SearchMode.FUZZY
            results = self.search_manager.search(templates, filter_text, mode=mode)
            return self._pin_recents(results.get_items())

        except ValueError:
            logger.warning("Unknown search mode %r; using fuzzy", search_mode)
            results = self.search_manager.search(templates, filter_text, mode=SearchMode.FUZZY)
            return self._pin_recents(results.get_items())
        except Exception as e:
            logger.error("Error filtering templates: %s", e, exc_info=True)
            filter_lower = filter_text.lower()
            return self._pin_recents(
                [t for t in templates if filter_lower in t.lower()]
            )

    def _pin_recents(self, items: list[str]) -> list[str]:
        """Reorder so recent templates surface at the top of the filter result."""
        max_recent = config.get("behavior", "max_recent_templates", default=10)
        if not max_recent:
            return items
        recents = self.usage.top(int(max_recent))
        if not recents:
            return items
        recent_set = set(recents)
        in_filter_recents = [t for t in recents if t in items]
        rest = [t for t in items if t not in recent_set]
        return in_filter_recents + rest

    def record_usage(self, template: str) -> None:
        self.usage.record(template)
