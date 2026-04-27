#!/usr/bin/env python3


import logging
import time

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
            logger.debug("Rate limiting: sleeping for %.3fs", sleep_time)
            time.sleep(sleep_time)

    def mark_request(self) -> None:
        self._last_request_time = time.time()

    def reset(self) -> None:
        self._last_request_time = 0
