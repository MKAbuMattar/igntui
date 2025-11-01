#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
import threading
from typing import Callable, List, Optional

from ..core.api import GitIgnoreAPI
from ..core.search import SearchManager

logger = logging.getLogger(__name__)


class TemplateLifecycle:
    def __init__(self, api: GitIgnoreAPI, search_manager: SearchManager):
        self.api = api
        self.search_manager = search_manager

    def load_templates_async(
        self,
        on_success: Callable[[List[str]], None],
        on_error: Callable[[str], None],
        on_complete: Callable[[], None],
    ) -> None:
        def load_templates():
            try:
                logger.info("Loading templates from API")
                response = self.api.list_templates()

                if response.success:
                    templates = sorted(response.data, key=str.lower)
                    logger.info(f"Successfully loaded {len(templates)} templates")
                    on_success(templates)
                else:
                    error_msg = response.error_message or "Unknown error"
                    logger.error(f"Failed to load templates: {error_msg}")
                    on_error(f"Failed to load templates: {error_msg}")

            except Exception as e:
                logger.error(f"Exception loading templates: {e}")
                on_error(f"Error: {str(e)}")
            finally:
                on_complete()

        thread = threading.Thread(target=load_templates, daemon=True)
        thread.start()

    def generate_content_async(
        self,
        templates: List[str],
        on_success: Callable[[str, bool], None],
        on_error: Callable[[str], None],
        on_complete: Callable[[], None],
    ) -> None:
        if not templates:
            on_error("No templates selected")
            on_complete()
            return

        def generate_content():
            try:
                logger.info(f"Generating content for {len(templates)} templates")
                response = self.api.get_templates(templates)

                if response.success:
                    logger.info(
                        f"Successfully generated content ({len(response.data)} chars)"
                    )
                    on_success(response.data, response.from_cache)
                else:
                    error_msg = response.error_message or "Unknown error"
                    logger.error(f"Failed to generate content: {error_msg}")
                    on_error(f"Generation failed: {error_msg}")

            except Exception as e:
                logger.error(f"Exception generating content: {e}")
                on_error(f"Error: {str(e)}")
            finally:
                on_complete()

        thread = threading.Thread(target=generate_content, daemon=True)
        thread.start()

    def filter_templates(
        self, templates: List[str], filter_text: str, search_mode: str = "fuzzy"
    ) -> List[str]:
        if not filter_text:
            return templates[:]

        try:
            mode_map = {"fuzzy": "fuzzy", "exact": "exact", "regex": "regex"}
            mode = mode_map.get(search_mode, "fuzzy")

            results = self.search_manager.search(filter_text, templates, mode=mode)

            return [r.item for r in results]

        except Exception as e:
            logger.error(f"Error filtering templates: {e}")
            filter_lower = filter_text.lower()
            return [t for t in templates if filter_lower in t.lower()]
