#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
import time
import urllib.error
import urllib.request
from typing import Optional

from .errors import APIError, NetworkError, RateLimitError, ServiceUnavailableError
from .rate_limiter import RateLimiter
from .response import APIResponse

logger = logging.getLogger(__name__)


class RequestHandler:
    def __init__(self, user_agent: str, timeout: float = 30.0, retry_attempts: int = 3):
        self.user_agent = user_agent
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.rate_limiter = RateLimiter(min_interval=0.1)
        self.stats = {"requests_made": 0, "errors": 0, "total_response_time": 0.0}

    def make_request(self, url: str, timeout: Optional[float] = None) -> APIResponse:
        self.rate_limiter.wait_if_needed()

        start_time = time.time()
        timeout = timeout or self.timeout

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "text/plain",
                    "Accept-Encoding": "identity",
                },
            )

            with urllib.request.urlopen(req, timeout=timeout) as response:
                content = response.read().decode("utf-8")
                response_time = time.time() - start_time

                self.rate_limiter.mark_request()
                self.stats["requests_made"] += 1
                self.stats["total_response_time"] += response_time

                logger.debug(f"API request to {url} took {response_time:.3f}s")

                return APIResponse(
                    success=True,
                    data=content,
                    status_code=response.getcode(),
                    response_time=response_time,
                )

        except urllib.error.HTTPError as e:
            response_time = time.time() - start_time
            self.stats["errors"] += 1

            error_msg = f"HTTP {e.code}: {e.reason}"

            if e.code == 429:
                retry_after = int(e.headers.get("Retry-After", 60))
                raise RateLimitError(error_msg, e.code, retry_after)
            elif e.code >= 500:
                raise ServiceUnavailableError(error_msg, e.code)
            else:
                raise APIError(error_msg, e.code)

        except urllib.error.URLError as e:
            response_time = time.time() - start_time
            self.stats["errors"] += 1

            if "timeout" in str(e.reason).lower():
                raise NetworkError(f"Request timeout after {timeout}s")
            else:
                raise NetworkError(f"Network error: {e.reason}")

        except Exception as e:
            response_time = time.time() - start_time
            self.stats["errors"] += 1
            raise APIError(f"Unexpected error: {str(e)}")

    def make_request_with_retry(self, url: str) -> APIResponse:
        last_exception = None

        for attempt in range(self.retry_attempts):
            try:
                return self.make_request(url)

            except RateLimitError as e:
                if attempt < self.retry_attempts - 1:
                    wait_time = e.retry_after or (2**attempt)
                    logger.warning(
                        f"Rate limited, waiting {wait_time}s before retry {attempt + 1}"
                    )
                    time.sleep(wait_time)
                    last_exception = e
                else:
                    raise

            except (NetworkError, ServiceUnavailableError) as e:
                if attempt < self.retry_attempts - 1:
                    wait_time = 2**attempt
                    logger.warning(
                        f"Request failed, retrying in {wait_time}s (attempt {attempt + 1})"
                    )
                    time.sleep(wait_time)
                    last_exception = e
                else:
                    raise

            except APIError:
                raise

        if last_exception:
            raise last_exception
        raise APIError("All retry attempts failed")

    def get_stats(self) -> dict:
        return self.stats.copy()
