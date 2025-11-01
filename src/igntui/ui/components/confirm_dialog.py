#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import curses

from .base_dialog import BaseDialog


class ConfirmDialog(BaseDialog):
    def __init__(
        self,
        stdscr,
        title: str,
        message: str,
        confirm_text: str = "Yes",
        cancel_text: str = "No",
    ):
        super().__init__(stdscr, title)
        self.message = message
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
        self.selected_button = 0

    def show(self) -> bool:
        lines = self.message.split("\n")
        content_width = max(len(line) for line in lines) + 4
        content_width = max(
            content_width, len(self.confirm_text) + len(self.cancel_text) + 10
        )
        width = min(60, max(30, content_width))
        height = len(lines) + 6

        y, x = self.calculate_position(width, height)

        while True:
            self.draw_background(y, x, height, width)
            self.draw_border(y, x, height, width, self.title)

            try:
                for i, line in enumerate(lines):
                    msg_y = y + 2 + i
                    msg_x = x + (width - len(line)) // 2
                    self.stdscr.addstr(msg_y, msg_x, line, curses.color_pair(8))

                button_y = y + height - 3
                confirm_btn = f" {self.confirm_text} "
                cancel_btn = f" {self.cancel_text} "

                total_btn_width = len(confirm_btn) + len(cancel_btn) + 4
                start_x = x + (width - total_btn_width) // 2

                confirm_x = start_x
                cancel_x = start_x + len(confirm_btn) + 4

                confirm_attr = (
                    curses.color_pair(4) | curses.A_BOLD
                    if self.selected_button == 0
                    else curses.color_pair(1)
                )
                cancel_attr = (
                    curses.color_pair(7) | curses.A_BOLD
                    if self.selected_button == 1
                    else curses.color_pair(1)
                )

                self.stdscr.addstr(button_y, confirm_x, confirm_btn, confirm_attr)
                self.stdscr.addstr(button_y, cancel_x, cancel_btn, cancel_attr)

                help_text = "Tab: Navigate | Enter: Select | ESC: Cancel"
                help_x = x + (width - len(help_text)) // 2
                self.stdscr.addstr(
                    y + height - 2, help_x, help_text, curses.color_pair(1)
                )

            except curses.error:
                pass

            self.stdscr.refresh()

            key = self.stdscr.getch()

            if key == 27:
                return False
            elif key in [curses.KEY_ENTER, ord("\n"), ord("\r")]:
                return self.selected_button == 0
            elif key == ord("\t"):
                self.selected_button = 1 - self.selected_button
            elif key == curses.KEY_LEFT:
                self.selected_button = 0
            elif key == curses.KEY_RIGHT:
                self.selected_button = 1
            elif key in [ord("y"), ord("Y")] and self.confirm_text.lower().startswith(
                "y"
            ):
                return True
            elif key in [ord("n"), ord("N")] and self.cancel_text.lower().startswith(
                "n"
            ):
                return False
