#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import curses
from typing import Optional


class BaseDialog:
    def __init__(self, stdscr, title: str = "Dialog"):
        self.stdscr = stdscr
        self.title = title
        self.result = None
        self.cancelled = False

    def calculate_position(self, width: int, height: int):
        max_y, max_x = self.stdscr.getmaxyx()
        y = max(0, (max_y - height) // 2)
        x = max(0, (max_x - width) // 2)
        return y, x

    def draw_background(self, y: int, x: int, height: int, width: int):
        max_y, max_x = self.stdscr.getmaxyx()
        for row in range(max_y):
            for col in range(max_x):
                try:
                    self.stdscr.addch(
                        row, col, " ", curses.color_pair(1) | curses.A_DIM
                    )
                except curses.error:
                    pass

    def draw_border(self, y: int, x: int, height: int, width: int, title: str = ""):
        for i in range(1, height + 1):
            for j in range(2, width + 2):
                shadow_y, shadow_x = y + i, x + j
                try:
                    if (
                        shadow_y < self.stdscr.getmaxyx()[0]
                        and shadow_x < self.stdscr.getmaxyx()[1]
                    ):
                        self.stdscr.addch(
                            shadow_y, shadow_x, " ", curses.color_pair(1) | curses.A_DIM
                        )
                except curses.error:
                    pass

        try:
            border_attr = curses.color_pair(6) | curses.A_BOLD

            self.stdscr.addch(y, x, "┌", border_attr)
            self.stdscr.addch(y, x + width - 1, "┐", border_attr)
            self.stdscr.addch(y + height - 1, x, "└", border_attr)
            self.stdscr.addch(y + height - 1, x + width - 1, "┘", border_attr)

            for i in range(1, width - 1):
                self.stdscr.addch(y, x + i, "─", border_attr)
                self.stdscr.addch(y + height - 1, x + i, "─", border_attr)

            for i in range(1, height - 1):
                self.stdscr.addch(y + i, x, "│", border_attr)
                self.stdscr.addch(y + i, x + width - 1, "│", border_attr)

            for i in range(1, height - 1):
                for j in range(1, width - 1):
                    self.stdscr.addch(y + i, x + j, " ", curses.color_pair(8))

            if title:
                title_text = f" {title} "
                title_x = x + (width - len(title_text)) // 2
                self.stdscr.addstr(
                    y, title_x, title_text, curses.color_pair(2) | curses.A_BOLD
                )
        except curses.error:
            pass
