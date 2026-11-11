import logging
import time
import urllib.error
import urllib.request

from .errors import APIError, NetworkError, RateLimitError, ServiceUnavailableError
from .response import APIResponse

logger = logging.getLogger(__name__)


class RequestHandler:
    def __init__(self, user_agent: str, timeout: float = 30.0, retry_attempts: int = 3):
        self.user_agent = user_agent
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self._last_request = 0.0

    def make_request(self, url: str, timeout: float | None = None) -> APIResponse:
        # At most one request per 100 ms.
        time.sleep(max(0.0, self._last_request + 0.1 - time.time()))

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

                self._last_request = time.time()

                logger.debug("API request to %s took %.3fs", url, response_time)

                return APIResponse(
                    success=True,
                    data=content,
                    status_code=response.getcode(),
                    response_time=response_time,
                )

        except urllib.error.HTTPError as e:
            # The error is also the response and holds its socket open.
            e.close()

            error_msg = f"HTTP {e.code}: {e.reason}"

            if e.code == 429:
                retry_after = int(e.headers.get("Retry-After", 60))
                raise RateLimitError(error_msg, e.code, retry_after) from e
            elif e.code >= 500:
                raise ServiceUnavailableError(error_msg, e.code) from e
            else:
                raise APIError(error_msg, e.code) from e

        except urllib.error.URLError as e:
            if "timeout" in str(e.reason).lower():
                raise NetworkError(f"Request timeout after {timeout}s") from e
            else:
                raise NetworkError(f"Network error: {e.reason}") from e

        except Exception as e:
            raise APIError(f"Unexpected error: {e}") from e

    def make_request_with_retry(self, url: str) -> APIResponse:
        last_exception = None

        for attempt in range(self.retry_attempts):
            try:
                return self.make_request(url)

            except RateLimitError as e:
                if attempt < self.retry_attempts - 1:
                    wait_time = e.retry_after or (2**attempt)
                    logger.warning(
                        "Rate limited, waiting %ds before retry %d", wait_time, attempt + 1
                    )
                    time.sleep(wait_time)
                    last_exception = e
                else:
                    raise

            except (NetworkError, ServiceUnavailableError) as e:
                if attempt < self.retry_attempts - 1:
                    wait_time = 2**attempt
                    logger.warning(
                        "Request failed, retrying in %ds (attempt %d)", wait_time, attempt + 1
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
