#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import curses

from .base_panel import BasePanel


class SearchPanel(BasePanel):
    def __init__(self, stdscr, y: int, x: int, height: int, width: int):
        super().__init__(stdscr, y, x, height, width, "Search")
        self.filter_text = ""
        self.current_search_mode = "fuzzy"

    def draw(self, cursor_position=0):
        mode_indicator = f"Search ({self.current_search_mode.upper()})"
        self.draw_border(mode_indicator, self.is_active)

        inner_y, inner_x = self.y + 1, self.x + 1
        inner_width = self.width - 2

        search_text = self.filter_text
        prompt = "> "
        display_text = prompt + search_text

        try:
            if self.is_active:
                attr = curses.color_pair(3) | curses.A_BOLD
            else:
                attr = curses.color_pair(8)

            self.stdscr.addstr(inner_y, inner_x, " " * (inner_width - 1), attr)
            
            max_display_len = inner_width - 1
            if len(display_text) <= max_display_len:
                self.stdscr.addstr(inner_y, inner_x, display_text, attr)
            else:
                visible_start = max(0, cursor_position + len(prompt) - max_display_len + 1)
                visible_text = display_text[visible_start:visible_start + max_display_len]
                self.stdscr.addstr(inner_y, inner_x, visible_text, attr)

            if self.is_active:
                cursor_x = inner_x + len(prompt) + cursor_position
                if len(display_text) > max_display_len:
                    visible_start = max(0, cursor_position + len(prompt) - max_display_len + 1)
                    cursor_x = inner_x + len(prompt) + cursor_position - visible_start
                
                if inner_x <= cursor_x < inner_x + inner_width - 1:
                    try:
                        char_at_cursor = search_text[cursor_position] if cursor_position < len(search_text) else " "
                        self.stdscr.addstr(inner_y, cursor_x, char_at_cursor, attr | curses.A_REVERSE)
                    except curses.error:
                        pass

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
