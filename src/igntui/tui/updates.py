"""State updates posted from background threads.

Background workers (lifecycle template-load / content-generate) post one of
these to a `queue.Queue` instead of mutating `TUIState` directly. The main
loop drains the queue between renders and applies each update.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TemplatesLoaded:
    templates: list[str]


@dataclass(frozen=True)
class TemplatesLoadFailed:
    message: str


@dataclass(frozen=True)
class ContentGenerated:
    content: str
    from_cache: bool
    selected_count: int


@dataclass(frozen=True)
class ContentGenerationFailed:
    message: str
    selected_templates: list[str]


@dataclass(frozen=True)
class LoadCompleted:
    """Workers post this in their `finally` block to clear the loading flag."""


@dataclass(frozen=True)
class GenerationCompleted:
    """Same, for generation flows."""


StateUpdate = (
    TemplatesLoaded
    | TemplatesLoadFailed
    | ContentGenerated
    | ContentGenerationFailed
    | LoadCompleted
    | GenerationCompleted
)
