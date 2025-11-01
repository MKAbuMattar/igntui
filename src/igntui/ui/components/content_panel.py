#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import curses

from .base_panel import BasePanel


class ContentPanel(BasePanel):
    def __init__(self, stdscr, y: int, x: int, height: int, width: int):
        super().__init__(stdscr, y, x, height, width, "Generated .gitignore")
        self.generated_content = ""
        self.content_scroll = 0
        self.generation_in_progress = False

    def draw(self):
        title = "Generated .gitignore"
        if self.generation_in_progress:
            title += " (Generating...)"

        self.draw_border(title, self.is_active)

        inner_y, inner_x = self.y + 1, self.x + 1
        inner_height, inner_width = self.height - 2, self.width - 2

        if not self.generated_content:
            try:
                self.stdscr.addstr(
                    inner_y + inner_height // 2,
                    inner_x + 2,
                    "Select templates to generate content",
                    curses.color_pair(8),
                )
            except curses.error:
                pass
            return

        lines = self.generated_content.split("\n")
        content_width = inner_width - 2
        show_scrollbar = len(lines) > inner_height
        if show_scrollbar:
            content_width -= 2

        for i in range(inner_height):
            line_idx = self.content_scroll + i
            if line_idx >= len(lines):
                break

            line = lines[line_idx]
            try:
                self.stdscr.addstr(
                    inner_y + i, inner_x + 1, line[:content_width], curses.color_pair(8)
                )
            except curses.error:
                pass

        if show_scrollbar:
            scrollbar_x = inner_x + inner_width - 1
            self.draw_scrollbar(
                inner_y,
                scrollbar_x,
                inner_height,
                len(lines),
                inner_height,
                self.content_scroll,
            )

            scroll_info = f" ({self.content_scroll + 1}-{min(self.content_scroll + inner_height, len(lines))}/{len(lines)})"
            try:
                info_x = self.x + len(title) + 2
                if info_x + len(scroll_info) < self.x + self.width - 1:
                    self.stdscr.addstr(
                        self.y, info_x, scroll_info, curses.color_pair(1)
                    )
            except curses.error:
                pass
