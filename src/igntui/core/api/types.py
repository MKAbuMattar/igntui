#!/usr/bin/env python3
"""Domain primitive types for the API layer."""

from typing import NewType

TemplateName = NewType("TemplateName", str)
"""A gitignore.io template identifier (e.g. ``"python"``, ``"node"``).

Use the `NewType` so the type checker treats these distinctly from arbitrary
strings even though they have no runtime overhead.
"""
