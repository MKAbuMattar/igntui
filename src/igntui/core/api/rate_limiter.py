#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, min_interval: float = 0.1):
        self.min_interval = min_interval
        self._last_request_time = 0

    def wait_if_needed(self) -> None:
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.3f}s")
            time.sleep(sleep_time)

    def mark_request(self) -> None:
        self._last_request_time = time.time()

    def reset(self) -> None:
        self._last_request_time = 0
