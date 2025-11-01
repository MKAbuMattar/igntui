#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import curses


class BasePanel:
    def __init__(
        self, stdscr, y: int, x: int, height: int, width: int, title: str = ""
    ):
        self.stdscr = stdscr
        self.y = y
        self.x = x
        self.height = height
        self.width = width
        self.title = title
        self.is_active = False

    def draw_border(self, title: str = "", is_active: bool = False):
        try:
            if is_active:
                border_attr = curses.color_pair(2) | curses.A_BOLD
            else:
                border_attr = curses.color_pair(1)

            self.stdscr.addch(self.y, self.x, "┌", border_attr)
            self.stdscr.addch(self.y, self.x + self.width - 1, "┐", border_attr)
            self.stdscr.addch(self.y + self.height - 1, self.x, "└", border_attr)
            self.stdscr.addch(
                self.y + self.height - 1, self.x + self.width - 1, "┘", border_attr
            )

            for i in range(1, self.width - 1):
                self.stdscr.addch(self.y, self.x + i, "─", border_attr)
                self.stdscr.addch(
                    self.y + self.height - 1, self.x + i, "─", border_attr
                )

            for i in range(1, self.height - 1):
                self.stdscr.addch(self.y + i, self.x, "│", border_attr)
                self.stdscr.addch(self.y + i, self.x + self.width - 1, "│", border_attr)

            if title:
                title_text = f" {title} "
                title_x = self.x + (self.width - len(title_text)) // 2
                if is_active:
                    title_attr = curses.color_pair(2) | curses.A_BOLD
                else:
                    title_attr = curses.color_pair(6) | curses.A_BOLD
                self.stdscr.addstr(self.y, title_x, title_text, title_attr)
        except curses.error:
            pass

    def draw_scrollbar(
        self,
        y: int,
        x: int,
        height: int,
        total_items: int,
        visible_items: int,
        scroll_position: int,
    ):
        if total_items <= visible_items:
            return

        bar_height = height
        thumb_height = max(1, int((visible_items / total_items) * bar_height))
        thumb_position = int(
            (scroll_position / max(1, total_items - visible_items))
            * (bar_height - thumb_height)
        )

        for i in range(bar_height):
            track_y = y + i
            try:
                if i >= thumb_position and i < thumb_position + thumb_height:
                    self.stdscr.addch(track_y, x, "█", curses.color_pair(2))
                else:
                    self.stdscr.addch(track_y, x, "░", curses.color_pair(1))
            except curses.error:
                pass

    def draw(self):
        raise NotImplementedError
