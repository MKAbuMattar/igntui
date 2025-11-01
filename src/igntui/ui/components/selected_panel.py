#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import curses
from typing import Set

from .base_panel import BasePanel


class SelectedPanel(BasePanel):
    def __init__(self, stdscr, y: int, x: int, height: int, width: int):
        super().__init__(stdscr, y, x, height, width, "Selected Templates")
        self.selected_templates: Set[str] = set()
        self.selected_index = 0
        self.selected_scroll = 0

    def draw(self):
        title = "Selected Templates"

        selected_list = sorted(list(self.selected_templates))
        scroll_info = ""
        if selected_list:
            visible_count = self.height - 2
            if len(selected_list) > visible_count:
                first_visible = self.selected_scroll + 1
                last_visible = min(
                    self.selected_scroll + visible_count, len(selected_list)
                )
                scroll_info = f" ({first_visible}-{last_visible}/{len(selected_list)})"
                if len(title) + len(scroll_info) > self.width - 6:
                    scroll_info = f" ({first_visible}-{last_visible})"
                    if len(title) + len(scroll_info) > self.width - 6:
                        scroll_info = ""

        full_title = title + scroll_info
        self.draw_border(full_title, self.is_active)

        inner_y, inner_x = self.y + 1, self.x + 1
        inner_height, inner_width = self.height - 2, self.width - 2

        if not selected_list:
            try:
                self.stdscr.addstr(
                    inner_y + 1,
                    inner_x + 2,
                    "No templates selected",
                    curses.color_pair(8),
                )
                self.stdscr.addstr(
                    inner_y + 2,
                    inner_x + 2,
                    "Select templates from the left panel",
                    curses.color_pair(8),
                )
            except curses.error:
                pass
            return

        visible_count = inner_height
        show_scrollbar = len(selected_list) > visible_count
        content_width = inner_width - 2
        if show_scrollbar:
            content_width -= 2

        if self.selected_index < self.selected_scroll:
            self.selected_scroll = self.selected_index
        elif self.selected_index >= self.selected_scroll + visible_count:
            self.selected_scroll = self.selected_index - visible_count + 1

        if self.selected_index >= len(selected_list):
            self.selected_index = max(0, len(selected_list) - 1)

        for i in range(visible_count):
            item_idx = self.selected_scroll + i
            if item_idx >= len(selected_list):
                break

            template = selected_list[item_idx]
            display_y = inner_y + i

            is_highlighted = item_idx == self.selected_index and self.is_active

            if is_highlighted:
                attr = curses.color_pair(3)
                prefix = "► "
            else:
                attr = curses.color_pair(4)
                prefix = "• "

            try:
                display_text = prefix + template
                display_line = display_text[:content_width].ljust(content_width)
                self.stdscr.addstr(display_y, inner_x + 1, display_line, attr)
            except curses.error:
                pass

        if show_scrollbar:
            scrollbar_x = inner_x + inner_width - 1
            self.draw_scrollbar(
                inner_y,
                scrollbar_x,
                inner_height,
                len(selected_list),
                visible_count,
                self.selected_scroll,
            )
