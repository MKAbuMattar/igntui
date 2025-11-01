#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import time
from dataclasses import dataclass, field
from typing import List, Optional, Set


@dataclass
class TUIState:
    running: bool = True
    loading: bool = True
    generation_in_progress: bool = False
    templates: List[str] = field(default_factory=list)
    selected_templates: Set[str] = field(default_factory=set)
    generated_content: str = ""
    filter_text: str = ""
    filtered_templates: List[str] = field(default_factory=list)
    current_search_mode: str = "fuzzy"  # fuzzy, exact, regex
    current_panel: int = 1  # 0=search, 1=templates, 2=selected, 3=content
    template_scroll: int = 0
    template_selected: int = 0
    selected_scroll: int = 0
    selected_index: int = 0
    content_scroll: int = 0
    search_active: bool = False
    status_message: str = ""
    error_message: str = ""
    message_timestamp: float = field(default_factory=time.time)

    def reset_template_selection(self) -> None:
        self.template_scroll = 0
        self.template_selected = 0

    def reset_selected_panel(self) -> None:
        self.selected_scroll = 0
        self.selected_index = 0

    def reset_content_scroll(self) -> None:
        self.content_scroll = 0

    def set_status_message(self, message: str, is_error: bool = False) -> None:
        if is_error:
            self.error_message = message
            self.status_message = ""
        else:
            self.status_message = message
            self.error_message = ""
        self.message_timestamp = time.time()

    def clear_status_message(self) -> None:
        if time.time() - self.message_timestamp > 5:
            self.status_message = ""
            self.error_message = ""

    def get_display_templates(self) -> List[str]:
        return self.filtered_templates if self.filter_text else self.templates

    def get_selected_templates_list(self) -> List[str]:
        return sorted(self.selected_templates)

    def toggle_template_selection(self, template: str) -> None:
        if template in self.selected_templates:
            self.selected_templates.remove(template)
        else:
            self.selected_templates.add(template)

    def clear_all_selections(self) -> None:
        self.selected_templates.clear()
        self.reset_selected_panel()

    def has_selections(self) -> bool:
        return len(self.selected_templates) > 0

    def get_selection_count(self) -> int:
        return len(self.selected_templates)
