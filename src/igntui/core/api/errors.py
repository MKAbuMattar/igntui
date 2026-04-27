#!/usr/bin/env python3




class APIError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        retry_after: int | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


class NetworkError(APIError):
    pass


class RateLimitError(APIError):
    pass


class ServiceUnavailableError(APIError):
    pass
