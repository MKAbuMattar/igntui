#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class APIResponse:
    success: bool
    data: Any
    error_message: Optional[str] = None
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    from_cache: bool = False
