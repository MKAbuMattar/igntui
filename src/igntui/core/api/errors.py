#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from typing import Optional


class APIError(Exception):
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        retry_after: Optional[int] = None,
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
