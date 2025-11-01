#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
from typing import Any, Dict, List, Optional

from ..cache import CacheManager, TemplateCache
from ..config import config
from .request_handler import RequestHandler
from .response import APIResponse

logger = logging.getLogger(__name__)


class GitIgnoreAPI:
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.base_url = config.get("api", "base_url")
        self.timeout = config.get("api", "timeout")
        self.user_agent = config.get("api", "user_agent")
        self.retry_attempts = config.get("api", "retry_attempts")
        self.cache_ttl = config.get("api", "cache_ttl")
        self.request_handler = RequestHandler(
            user_agent=self.user_agent,
            timeout=self.timeout,
            retry_attempts=self.retry_attempts,
        )
        self.cache_manager = cache_manager or CacheManager(
            cache_dir=config.get_cache_dir(), default_ttl=self.cache_ttl
        )
        self.template_cache = TemplateCache(self.cache_manager)
        self.stats = {"cache_hits": 0, "cache_misses": 0}

    def list_templates(self, force_refresh: bool = False) -> APIResponse:
        if not force_refresh:
            cached_templates = self.template_cache.get_template_list()
            if cached_templates is not None:
                logger.debug("Using cached template list")
                self.stats["cache_hits"] += 1
                return APIResponse(success=True, data=cached_templates, from_cache=True)

        self.stats["cache_misses"] += 1
        url = f"{self.base_url}/list"

        try:
            response = self.request_handler.make_request_with_retry(url)

            if response.success:
                templates = self._parse_template_list(response.data)

                self.template_cache.set_template_list(templates)

                response.data = templates
                logger.info(f"Fetched {len(templates)} templates from API")

            return response

        except Exception as e:
            logger.error(f"Failed to fetch template list: {e}")
            return APIResponse(success=False, data=[], error_message=str(e))

    def get_templates(
        self, technologies: List[str], force_refresh: bool = False
    ) -> APIResponse:
        if not technologies:
            return APIResponse(
                success=True,
                data="# No templates selected\n# Select templates from the Available Templates panel",
            )

        clean_techs = self._clean_technology_names(technologies)
        if not clean_techs:
            return APIResponse(
                success=False, data="", error_message="No valid templates provided"
            )

        if not force_refresh:
            cached_content = self.template_cache.get_template_content(clean_techs)
            if cached_content is not None:
                logger.debug(f"Using cached content for {len(clean_techs)} templates")
                self.stats["cache_hits"] += 1
                return APIResponse(success=True, data=cached_content, from_cache=True)

        self.stats["cache_misses"] += 1
        tech_string = ",".join(clean_techs).lower()
        url = f"{self.base_url}/{tech_string}"

        try:
            response = self.request_handler.make_request_with_retry(url)

            if response.success:
                self.template_cache.set_template_content(clean_techs, response.data)
                logger.info(f"Fetched content for templates: {', '.join(clean_techs)}")

            return response

        except Exception as e:
            logger.error(f"Failed to fetch template content: {e}")

            fallback_content = f"""# Error generating content: {str(e)}
# Selected templates: {', '.join(clean_techs)}
#
# This error typically means:
# - Network connectivity issues
# - Invalid template names
# - API service temporarily unavailable
#
# Try refreshing the template list or check your internet connection."""

            return APIResponse(
                success=False, data=fallback_content, error_message=str(e)
            )

    def test_connection(self) -> APIResponse:
        try:
            logger.info("Testing API connectivity...")

            response = self.request_handler.make_request(
                f"{self.base_url}/list?limit=1"
            )

            if response.success:
                test_results = {
                    "status": "connected",
                    "response_time": response.response_time,
                    "api_url": self.base_url,
                    "cache_stats": self.cache_manager.get_stats(),
                }

                return APIResponse(success=True, data=test_results)
            else:
                return APIResponse(
                    success=False,
                    data={"status": "failed"},
                    error_message="API test request failed",
                )

        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return APIResponse(
                success=False, data={"status": "error"}, error_message=str(e)
            )

    def get_stats(self) -> Dict[str, Any]:
        request_stats = self.request_handler.get_stats()
        total_requests = request_stats["requests_made"]
        avg_response_time = (
            request_stats["total_response_time"] / total_requests
            if total_requests > 0
            else 0.0
        )

        cache_stats = self.cache_manager.get_stats()

        return {
            "api_stats": {
                "requests_made": total_requests,
                "avg_response_time": avg_response_time,
                "error_rate": request_stats["errors"] / max(1, total_requests),
                "base_url": self.base_url,
                "timeout": self.timeout,
                "retry_attempts": self.retry_attempts,
            },
            "cache_stats": cache_stats,
            "performance_stats": {
                "cache_hit_rate": (
                    self.stats["cache_hits"]
                    / max(1, self.stats["cache_hits"] + self.stats["cache_misses"])
                ),
                "total_cache_operations": self.stats["cache_hits"]
                + self.stats["cache_misses"],
            },
        }

    def clear_cache(self) -> None:
        self.cache_manager.clear()
        logger.info("Cleared all API cache data")

    def invalidate_template(self, template_name: str) -> int:
        return self.template_cache.invalidate_template_content(template_name)

    def _parse_template_list(self, response_text: str) -> List[str]:
        all_templates = []

        for line in response_text.strip().split("\n"):
            for template in line.split(","):
                clean_template = template.strip()
                if clean_template and self._is_valid_template_name(clean_template):
                    all_templates.append(clean_template)

        unique_templates = sorted(set(all_templates), key=str.lower)

        logger.debug(f"Parsed {len(unique_templates)} unique templates")
        return unique_templates

    def _clean_technology_names(self, technologies: List[str]) -> List[str]:
        clean_techs = []

        for tech in technologies:
            clean_tech = str(tech).strip()

            clean_tech = "".join(c for c in clean_tech if c.isalnum() or c in "-_+.")

            if clean_tech and self._is_valid_template_name(clean_tech):
                clean_techs.append(clean_tech)
            else:
                logger.warning(f"Skipping invalid template name: {tech}")

        return clean_techs

    def _is_valid_template_name(self, name: str) -> bool:
        if not name or len(name) > 100:
            return False

        if not any(c.isalnum() for c in name):
            return False

        suspicious_patterns = ["..", "//", "\\\\", "<", ">", "|"]
        if any(pattern in name for pattern in suspicious_patterns):
            return False

        return True
