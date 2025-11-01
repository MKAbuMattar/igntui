#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import curses

from .base_dialog import BaseDialog


class HelpDialog(BaseDialog):
    def __init__(self, stdscr):
        super().__init__(stdscr, "Help - Keyboard Shortcuts")
        self.scroll_position = 0
        self.help_content = [
            "NAVIGATION:",
            "  Tab / Shift+Tab    - Switch between panels",
            "  Arrow Keys         - Navigate within panels",
            "  Page Up/Down       - Scroll content",
            "  Home/End           - Go to top/bottom",
            "",
            "SEARCH PANEL:",
            "  F1                 - Fuzzy search mode",
            "  F2                 - Exact search mode",
            "  F3                 - Regex search mode",
            "  Ctrl+U             - Clear search",
            "  Enter              - Apply search",
            "",
            "TEMPLATES PANEL:",
            "  Space              - Select/deselect template",
            "  a                  - Select all filtered templates",
            "  x                  - Clear all selections",
            "  F5                 - Refresh templates list",
            "",
            "SELECTED PANEL:",
            "  Space              - Remove selected template",
            "  c                  - Clear all selections",
            "",
            "CONTENT PANEL:",
            "  Up/Down Arrows     - Scroll content",
            "  Page Up/Down       - Fast scroll",
            "",
            "GLOBAL ACTIONS:",
            "  s                  - Save to .gitignore",
            "  e                  - Export to file",
            "  g                  - Generate content",
            "  h                  - Show this help",
            "  q / Ctrl+C         - Quit application",
            "",
            "TIPS:",
            "  • Fuzzy search matches partial words",
            "  • Exact search requires complete matches",
            "  • Regex search supports patterns like 'python|node'",
            "  • Selected templates are automatically generated",
            "  • Use Ctrl+U to quickly clear search and see all templates",
        ]

    def show(self):
        width = 70
        height = 20
        y, x = self.calculate_position(width, height)

        while True:
            self.draw_background(y, x, height, width)
            self.draw_border(y, x, height, width, self.title)

            content_height = height - 4
            content_width = width - 4
            visible_lines = self.help_content[
                self.scroll_position : self.scroll_position + content_height
            ]

            for i, line in enumerate(visible_lines):
                content_y = y + 2 + i
                content_x = x + 2

                try:
                    if line.startswith("  "):
                        self.stdscr.addstr(
                            content_y,
                            content_x,
                            line[:content_width],
                            curses.color_pair(8),
                        )
                    elif line.endswith(":"):
                        self.stdscr.addstr(
                            content_y,
                            content_x,
                            line[:content_width],
                            curses.color_pair(2) | curses.A_BOLD,
                        )
                    elif line.startswith("  •"):
                        self.stdscr.addstr(
                            content_y,
                            content_x,
                            line[:content_width],
                            curses.color_pair(4),
                        )
                    else:
                        self.stdscr.addstr(
                            content_y,
                            content_x,
                            line[:content_width],
                            curses.color_pair(8),
                        )
                except curses.error:
                    pass

            if len(self.help_content) > content_height:
                scrollbar_x = x + width - 2
                for i in range(content_height):
                    try:
                        if i == 0 and self.scroll_position > 0:
                            self.stdscr.addch(
                                y + 2 + i, scrollbar_x, "▲", curses.color_pair(1)
                            )
                        elif (
                            i == content_height - 1
                            and self.scroll_position + content_height
                            < len(self.help_content)
                        ):
                            self.stdscr.addch(
                                y + 2 + i, scrollbar_x, "▼", curses.color_pair(1)
                            )
                        else:
                            self.stdscr.addch(
                                y + 2 + i, scrollbar_x, "│", curses.color_pair(1)
                            )
                    except curses.error:
                        pass

            try:
                footer = "Use Up/Down to scroll, ESC or q to close"
                footer_y = y + height - 2
                footer_x = x + (width - len(footer)) // 2
                self.stdscr.addstr(footer_y, footer_x, footer, curses.color_pair(1))
            except curses.error:
                pass

            self.stdscr.refresh()

            key = self.stdscr.getch()

            if key in [ord("q"), ord("Q"), 27, curses.KEY_F10]:
                break
            elif key == curses.KEY_UP:
                self.scroll_position = max(0, self.scroll_position - 1)
            elif key == curses.KEY_DOWN:
                max_scroll = max(0, len(self.help_content) - content_height)
                self.scroll_position = min(max_scroll, self.scroll_position + 1)
            elif key == curses.KEY_PPAGE:
                self.scroll_position = max(0, self.scroll_position - content_height)
            elif key == curses.KEY_NPAGE:
                max_scroll = max(0, len(self.help_content) - content_height)
                self.scroll_position = min(
                    max_scroll, self.scroll_position + content_height
                )
            elif key == curses.KEY_HOME:
                self.scroll_position = 0
            elif key == curses.KEY_END:
                max_scroll = max(0, len(self.help_content) - content_height)
                self.scroll_position = max_scroll
