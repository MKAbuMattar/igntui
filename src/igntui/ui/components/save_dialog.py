#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import curses
from typing import Optional

from .base_dialog import BaseDialog


class SaveDialog(BaseDialog):
    def __init__(self, stdscr, default_path: str = ".gitignore"):
        super().__init__(stdscr, "Save .gitignore File")
        self.file_path = default_path
        self.cursor_pos = len(self.file_path)

    def show(self) -> Optional[str]:
        width = 60
        height = 8
        y, x = self.calculate_position(width, height)

        while True:
            self.draw_background(y, x, height, width)
            self.draw_border(y, x, height, width, self.title)

            try:
                prompt = "Enter file path:"
                self.stdscr.addstr(y + 2, x + 2, prompt, curses.color_pair(8))

                input_y = y + 3
                input_x = x + 2
                input_width = width - 4

                self.stdscr.addstr(
                    input_y, input_x, " " * input_width, curses.color_pair(3)
                )

                display_path = self.file_path[: input_width - 1]
                self.stdscr.addstr(input_y, input_x, display_path, curses.color_pair(3))

                cursor_display_pos = min(self.cursor_pos, input_width - 1)
                if cursor_display_pos < len(display_path):
                    cursor_char = display_path[cursor_display_pos]
                else:
                    cursor_char = " "
                self.stdscr.addch(
                    input_y,
                    input_x + cursor_display_pos,
                    cursor_char,
                    curses.color_pair(3) | curses.A_REVERSE,
                )

                button_y = y + 5
                save_btn = " Save "
                cancel_btn = " Cancel "

                save_x = x + width // 2 - len(save_btn) - 2
                cancel_x = x + width // 2 + 2

                self.stdscr.addstr(
                    button_y, save_x, save_btn, curses.color_pair(4) | curses.A_BOLD
                )
                self.stdscr.addstr(button_y, cancel_x, cancel_btn, curses.color_pair(7))

                help_text = "Enter: Save | ESC: Cancel"
                help_x = x + (width - len(help_text)) // 2
                self.stdscr.addstr(y + 6, help_x, help_text, curses.color_pair(1))

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
