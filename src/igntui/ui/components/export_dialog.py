#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import curses
import os
from typing import Optional

from .base_dialog import BaseDialog


class ExportDialog(BaseDialog):
    def __init__(self, stdscr, default_path: str = ""):
        super().__init__(stdscr, "Export .gitignore Content")
        if not default_path:
            self.file_path = os.path.join(
                os.path.expanduser("~"), "gitignore_export.txt"
            )
        else:
            self.file_path = default_path
        self.cursor_pos = len(self.file_path)

    def show(self) -> Optional[str]:
        width = 70
        height = 10
        y, x = self.calculate_position(width, height)

        while True:
            self.draw_background(y, x, height, width)
            self.draw_border(y, x, height, width, self.title)

            try:
                desc_lines = [
                    "Export the generated .gitignore content to a file.",
                    "This will create a new file with the complete content.",
                ]

                for i, line in enumerate(desc_lines):
                    self.stdscr.addstr(y + 2 + i, x + 2, line, curses.color_pair(8))

                label = "Export file path:"
                self.stdscr.addstr(y + 5, x + 2, label, curses.color_pair(8))

                input_y = y + 6
                input_x = x + 2
                input_width = width - 4

                self.stdscr.addstr(
                    input_y, input_x, " " * input_width, curses.color_pair(3)
                )

                display_path = self.file_path
                if len(display_path) > input_width - 1:
                    display_start = len(display_path) - (input_width - 4)
                    display_path = "..." + display_path[display_start:]

                self.stdscr.addstr(
                    input_y,
                    input_x,
                    display_path[: input_width - 1],
                    curses.color_pair(3),
                )

                cursor_display_pos = min(self.cursor_pos, input_width - 1)
                if len(self.file_path) > input_width - 1:
                    visible_start = max(0, len(self.file_path) - (input_width - 4))
                    cursor_display_pos = self.cursor_pos - visible_start + 3
                    cursor_display_pos = max(
                        3, min(cursor_display_pos, input_width - 1)
                    )

                if cursor_display_pos < len(display_path):
                    cursor_char = display_path[cursor_display_pos]
                else:
                    cursor_char = " "

                try:
                    self.stdscr.addch(
                        input_y,
                        input_x + cursor_display_pos,
                        cursor_char,
                        curses.color_pair(3) | curses.A_REVERSE,
                    )
                except curses.error:
                    pass

                button_y = y + 8
                export_btn = " Export "
                cancel_btn = " Cancel "

                export_x = x + width // 2 - len(export_btn) - 2
                cancel_x = x + width // 2 + 2

                self.stdscr.addstr(
                    button_y, export_x, export_btn, curses.color_pair(4) | curses.A_BOLD
                )
                self.stdscr.addstr(button_y, cancel_x, cancel_btn, curses.color_pair(7))

            except curses.error:
                pass

            self.stdscr.refresh()

            key = self.stdscr.getch()

            if key == 27:
                return None
            elif key in [curses.KEY_ENTER, ord("\n"), ord("\r")]:
                if self.file_path.strip():
                    return self.file_path.strip()
            elif key == curses.KEY_BACKSPACE or key == 127:
                if self.cursor_pos > 0:
                    self.file_path = (
                        self.file_path[: self.cursor_pos - 1]
                        + self.file_path[self.cursor_pos :]
                    )
                    self.cursor_pos -= 1
            elif key == curses.KEY_DC:
                if self.cursor_pos < len(self.file_path):
                    self.file_path = (
                        self.file_path[: self.cursor_pos]
                        + self.file_path[self.cursor_pos + 1 :]
                    )
            elif key == curses.KEY_LEFT:
                self.cursor_pos = max(0, self.cursor_pos - 1)
            elif key == curses.KEY_RIGHT:
                self.cursor_pos = min(len(self.file_path), self.cursor_pos + 1)
            elif key == curses.KEY_HOME:
                self.cursor_pos = 0
            elif key == curses.KEY_END:
                self.cursor_pos = len(self.file_path)
            elif 32 <= key <= 126:
                char = chr(key)
                self.file_path = (
                    self.file_path[: self.cursor_pos]
                    + char
                    + self.file_path[self.cursor_pos :]
                )
                self.cursor_pos += 1
