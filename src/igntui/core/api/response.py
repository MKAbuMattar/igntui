#!/usr/bin/env python3


from dataclasses import dataclass, replace
from typing import Any


@dataclass(frozen=True)
class APIResponse:
    success: bool
    data: Any
    error_message: str | None = None
    status_code: int | None = None
    response_time: float | None = None
    from_cache: bool = False

    def with_data(self, data: Any) -> "APIResponse":
        """Return a copy with `data` replaced — use instead of mutating in place."""
        return replace(self, data=data)
