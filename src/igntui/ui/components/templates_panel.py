#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import curses
from typing import List, Set

from .base_panel import BasePanel


class TemplatesPanel(BasePanel):
    def __init__(self, stdscr, y: int, x: int, height: int, width: int):
        super().__init__(stdscr, y, x, height, width, "Available Templates")
        self.templates: List[str] = []
        self.filtered_templates: List[str] = []
        self.selected_templates: Set[str] = set()
        self.template_selected = 0
        self.template_scroll = 0
        self.loading = False
        self.filter_text = ""
        self.current_search_mode = "fuzzy"

    def draw(self):
        title = "Available Templates"

        scroll_info = ""
        if self.filtered_templates:
            visible_count = self.height - 4
            if len(self.filtered_templates) > visible_count:
                first_visible = self.template_scroll + 1
                last_visible = min(
                    self.template_scroll + visible_count, len(self.filtered_templates)
                )
                scroll_info = (
                    f" ({first_visible}-{last_visible}/{len(self.filtered_templates)})"
                )
                if len(title) + len(scroll_info) > self.width - 6:
                    scroll_info = f" ({first_visible}-{last_visible})"
                    if len(title) + len(scroll_info) > self.width - 6:
                        scroll_info = ""

        full_title = title + scroll_info
        self.draw_border(full_title, self.is_active)
        inner_y, inner_x = self.y + 1, self.x + 1
        inner_height, inner_width = self.height - 2, self.width - 2

        if self.loading:
            try:
                self.stdscr.addstr(
                    inner_y + inner_height // 2,
                    inner_x + 2,
                    "Loading templates...",
                    curses.color_pair(8),
                )
            except curses.error:
                pass
            return

        self._draw_list_view(inner_y, inner_x, inner_height, inner_width)

    def _draw_list_view(self, y: int, x: int, height: int, width: int):
        if self.filter_text:
            count_text = (
                f"[{len(self.filtered_templates)}/{len(self.templates)} templates]"
            )
            search_info = f" '{self.filter_text}' ({self.current_search_mode})"
        else:
            count_text = f"[{len(self.filtered_templates)} templates]"
            search_info = ""

        try:
            self.stdscr.addstr(y, x + 1, count_text, curses.color_pair(1))
            if search_info and len(count_text + search_info) < width - 4:
                self.stdscr.addstr(
                    y, x + 1 + len(count_text), search_info, curses.color_pair(2)
                )
            y += 1
            height -= 1
        except curses.error:
            pass

        if not self.filtered_templates:
            try:
                if self.filter_text:
                    no_match_text = f"No matches for '{self.filter_text}' in {self.current_search_mode} mode"
                    help_text = "Try F1 (fuzzy), F2 (exact), or F3 (regex)"
                    self.stdscr.addstr(
                        y + height // 2,
                        x + 2,
                        no_match_text[: width - 4],
                        curses.color_pair(7),
                    )
                    if height // 2 + 1 < height:
                        self.stdscr.addstr(
                            y + height // 2 + 1,
                            x + 2,
                            help_text[: width - 4],
                            curses.color_pair(1),
                        )
                else:
                    no_match_text = "No templates found"
                    self.stdscr.addstr(
                        y + height // 2, x + 2, no_match_text, curses.color_pair(7)
                    )
            except curses.error:
                pass
            return

        visible_count = height
        show_scrollbar = len(self.filtered_templates) > visible_count
        content_width = width - 2
        if show_scrollbar:
            content_width -= 2

        if self.template_selected < self.template_scroll:
            self.template_scroll = self.template_selected
        elif self.template_selected >= self.template_scroll + visible_count:
            self.template_scroll = self.template_selected - visible_count + 1

        for i in range(visible_count):
            template_idx = self.template_scroll + i
            if template_idx >= len(self.filtered_templates):
                break

            template = self.filtered_templates[template_idx]
            display_y = y + i

            is_selected = template_idx == self.template_selected and self.is_active
            is_checked = template in self.selected_templates

            attr = curses.color_pair(8)
            if is_selected:
                attr = curses.color_pair(3)

            prefix = "✓ " if is_checked else "  "
            display_text = prefix + template

            try:
                display_line = display_text[:content_width].ljust(content_width)
                self.stdscr.addstr(display_y, x + 1, display_line, attr)
            except curses.error:
                pass

        if show_scrollbar:
            scrollbar_x = x + width - 1
            self.draw_scrollbar(
                y,
                scrollbar_x,
                height,
                len(self.filtered_templates),
                visible_count,
                self.template_scroll,
            )
