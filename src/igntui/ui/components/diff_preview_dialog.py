#!/usr/bin/env python3
"""Diff-preview dialog shown before overwriting an existing file (Phase 5.4)."""

import curses
import difflib

from .base_dialog import BaseDialog


class DiffPreviewDialog(BaseDialog):
    """Show a unified diff between current and proposed file contents.

    Returns True if the user confirms (apply), False on cancel.
    Scrollable with arrow keys / PgUp / PgDn. y/n / Enter / Esc as shortcuts.
    """

    def __init__(self, stdscr, current: str, proposed: str, filename: str = ""):
        super().__init__(stdscr, title=f"Diff preview: {filename}" if filename else "Diff preview")
        self.diff_lines = list(
            difflib.unified_diff(
                current.splitlines(keepends=False),
                proposed.splitlines(keepends=False),
                fromfile=f"current/{filename}" if filename else "current",
                tofile=f"new/{filename}" if filename else "new",
                lineterm="",
            )
        )
        self.scroll = 0
        self.selected_button = 0  # 0 = Apply, 1 = Cancel

    def is_empty(self) -> bool:
        return len(self.diff_lines) == 0

    def show(self) -> bool:
        if self.is_empty():
            return True  # nothing to confirm — let caller short-circuit

        max_y, max_x = self.stdscr.getmaxyx()
        width = min(max_x - 4, max(60, max(len(line) for line in self.diff_lines) + 4))
        height = min(max_y - 4, max(15, len(self.diff_lines) + 8))

        y, x = self.calculate_position(width, height)
        diff_height = height - 6  # 2 borders + 1 title-pad + 2 buttons + 1 help

        while True:
            self._draw_frame(y, x, height, width)
            self._draw_diff(y + 2, x + 2, diff_height, width - 4)
            self._draw_buttons(y + height - 3, x, width)
            self._draw_help(y + height - 2, x, width)
            self.stdscr.refresh()

            key = self.stdscr.getch()
            max_scroll = max(0, len(self.diff_lines) - diff_height)

            if key == 27:  # Esc
                return False
            elif key in (ord("y"), ord("Y")):
                return True
            elif key in (ord("n"), ord("N")):
                return False
            elif key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
                return self.selected_button == 0
            elif key == ord("\t"):
                self.selected_button = 1 - self.selected_button
            elif key in (curses.KEY_LEFT, curses.KEY_RIGHT):
                self.selected_button = 1 - self.selected_button
            elif key == curses.KEY_UP:
                self.scroll = max(0, self.scroll - 1)
            elif key == curses.KEY_DOWN:
                self.scroll = min(max_scroll, self.scroll + 1)
            elif key == curses.KEY_PPAGE:
                self.scroll = max(0, self.scroll - diff_height)
            elif key == curses.KEY_NPAGE:
                self.scroll = min(max_scroll, self.scroll + diff_height)
            elif key == curses.KEY_HOME:
                self.scroll = 0
            elif key == curses.KEY_END:
                self.scroll = max_scroll

    def _draw_frame(self, y: int, x: int, height: int, width: int) -> None:
        self.draw_background(y, x, height, width)
        self.draw_border(y, x, height, width, self.title)

    def _draw_diff(self, y: int, x: int, height: int, width: int) -> None:
        for row in range(height):
            idx = self.scroll + row
            if idx >= len(self.diff_lines):
                break
            line = self.diff_lines[idx]
            attr = self._color_for_line(line)
            try:
                self.stdscr.addstr(y + row, x, line[:width].ljust(width), attr)
            except curses.error:
                pass

    def _color_for_line(self, line: str) -> int:
        if line.startswith("+++") or line.startswith("---"):
            return curses.color_pair(6) | curses.A_BOLD
        if line.startswith("@@"):
            return curses.color_pair(2) | curses.A_BOLD
        if line.startswith("+"):
            return curses.color_pair(4)  # success / green
        if line.startswith("-"):
            return curses.color_pair(7)  # error / red
        return curses.color_pair(8) | curses.A_DIM

    def _draw_buttons(self, y: int, x: int, width: int) -> None:
        apply_btn = " Apply "
        cancel_btn = " Cancel "
        gap = 4
        total = len(apply_btn) + len(cancel_btn) + gap
        start = x + (width - total) // 2
        try:
            apply_attr = (
                curses.color_pair(4) | curses.A_BOLD
                if self.selected_button == 0
                else curses.color_pair(1)
            )
            cancel_attr = (
                curses.color_pair(7) | curses.A_BOLD
                if self.selected_button == 1
                else curses.color_pair(1)
            )
            self.stdscr.addstr(y, start, apply_btn, apply_attr)
            self.stdscr.addstr(y, start + len(apply_btn) + gap, cancel_btn, cancel_attr)
        except curses.error:
            pass

    def _draw_help(self, y: int, x: int, width: int) -> None:
        help_text = "↑↓ scroll · PgUp/PgDn · y/n · Tab+Enter · Esc cancels"
        try:
            self.stdscr.addstr(y, x + (width - len(help_text)) // 2, help_text, curses.color_pair(1))
        except curses.error:
            pass
