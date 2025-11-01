#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import curses
from typing import Optional


class CursesSetup:
    COLOR_BORDER = 1
    COLOR_HIGHLIGHT = 2
    COLOR_SELECTED = 3
    COLOR_SUCCESS = 4
    COLOR_STATUS_BAR = 5
    COLOR_TITLE = 6
    COLOR_ERROR = 7
    COLOR_NORMAL = 8

    @staticmethod
    def setup_curses(stdscr) -> None:
        curses.curs_set(0)
        stdscr.keypad(True)
        stdscr.timeout(100)
        CursesSetup.setup_colors()

    @staticmethod
    def setup_colors() -> None:
        if not curses.has_colors():
            return

        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(CursesSetup.COLOR_BORDER, curses.COLOR_CYAN, -1)
        curses.init_pair(CursesSetup.COLOR_HIGHLIGHT, curses.COLOR_YELLOW, -1)
        curses.init_pair(
            CursesSetup.COLOR_SELECTED, curses.COLOR_BLACK, curses.COLOR_CYAN
        )
        curses.init_pair(CursesSetup.COLOR_SUCCESS, curses.COLOR_GREEN, -1)
        curses.init_pair(CursesSetup.COLOR_STATUS_BAR, curses.COLOR_GREEN, -1)
        curses.init_pair(CursesSetup.COLOR_TITLE, curses.COLOR_MAGENTA, -1)
        curses.init_pair(CursesSetup.COLOR_ERROR, curses.COLOR_RED, -1)
        curses.init_pair(CursesSetup.COLOR_NORMAL, curses.COLOR_WHITE, -1)

    @staticmethod
    def get_color_pair(color_id: int) -> int:
        return curses.color_pair(color_id)

    @staticmethod
    def cleanup(stdscr: Optional = None) -> None:
        try:
            if stdscr:
                stdscr.keypad(False)
            curses.curs_set(1)
            curses.endwin()
        except:
            pass


def get_border_color() -> int:
    return CursesSetup.get_color_pair(CursesSetup.COLOR_BORDER)


def get_highlight_color() -> int:
    return CursesSetup.get_color_pair(CursesSetup.COLOR_HIGHLIGHT)


def get_selected_color() -> int:
    return CursesSetup.get_color_pair(CursesSetup.COLOR_SELECTED)


def get_success_color() -> int:
    return CursesSetup.get_color_pair(CursesSetup.COLOR_SUCCESS)


def get_status_bar_color() -> int:
    return CursesSetup.get_color_pair(CursesSetup.COLOR_STATUS_BAR)


def get_title_color() -> int:
    return CursesSetup.get_color_pair(CursesSetup.COLOR_TITLE)


def get_error_color() -> int:
    return CursesSetup.get_color_pair(CursesSetup.COLOR_ERROR)


def get_normal_color() -> int:
    return CursesSetup.get_color_pair(CursesSetup.COLOR_NORMAL)
