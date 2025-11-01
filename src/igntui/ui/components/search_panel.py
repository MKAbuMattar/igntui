#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import curses

from .base_panel import BasePanel


class SearchPanel(BasePanel):
    def __init__(self, stdscr, y: int, x: int, height: int, width: int):
        super().__init__(stdscr, y, x, height, width, "Search")
        self.filter_text = ""
        self.current_search_mode = "fuzzy"

    def draw(self):
        mode_indicator = f"Search ({self.current_search_mode.upper()})"
        self.draw_border(mode_indicator, self.is_active)

        inner_y, inner_x = self.y + 1, self.x + 1
        inner_width = self.width - 2

        search_text = self.filter_text
        prompt = "> "
        display_text = prompt + search_text

        if self.is_active:
            display_text += "_"

        try:
            if self.is_active:
                attr = curses.color_pair(3) | curses.A_BOLD
            else:
                attr = curses.color_pair(8)

            self.stdscr.addstr(inner_y, inner_x, " " * (inner_width - 1), attr)
            self.stdscr.addstr(inner_y, inner_x, display_text[: inner_width - 1], attr)

            if self.height > 3:
                mode_help = "F1:Fuzzy F2:Exact F3:Regex"
                if len(mode_help) < inner_width - 1:
                    try:
                        mode_attr = (
                            curses.color_pair(1)
                            if self.is_active
                            else curses.color_pair(5)
                        )
                        self.stdscr.addstr(inner_y + 1, inner_x, mode_help, mode_attr)
                    except curses.error:
                        pass
        except curses.error:
            pass
