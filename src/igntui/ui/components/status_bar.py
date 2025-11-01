#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import curses


class StatusBar:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.status_message = ""
        self.error_message = ""

    def draw(self, current_panel: int, current_search_mode: str):
        max_y, max_x = self.stdscr.getmaxyx()
        status_y = max_y - 1

        try:
            self.stdscr.addstr(status_y, 0, " " * (max_x - 1), curses.color_pair(5))
        except curses.error:
            pass

        panel_names = ["Search", "Templates", "Selected", "Content"]
        active_panel = panel_names[current_panel]

        if current_panel == 0:
            controls = f"[{active_panel}] Mode:{current_search_mode.upper()} | F1-F3:Switch | Ctrl+U:Clear"
        elif current_panel == 1:
            controls = f"[{active_panel}] Space:Select | a:All | x:Clear | F5:Refresh"
        elif current_panel == 2:
            controls = f"[{active_panel}] Space:Remove | s:Save | e:Export | c:Clear"
        else:
            controls = f"[{active_panel}] s:Save | e:Export | PgUp/Dn:Scroll"

        controls += " | h:Help | q:Quit"

        message = self.error_message if self.error_message else self.status_message

        controls_len = len(controls)
        message_len = len(message) if message else 0
        available_space = max_x - 4

        if controls_len + message_len > available_space:
            if message_len > available_space // 2:
                max_msg_len = available_space // 2
                message = (
                    message[: max_msg_len - 3] + "..."
                    if len(message) > max_msg_len
                    else message
                )

            remaining_space = available_space - len(message) - 3
            if controls_len > remaining_space:
                controls = controls[: remaining_space - 3] + "..."

        try:
            self.stdscr.addstr(status_y, 1, controls, curses.color_pair(5))

            if message:
                msg_x = max_x - len(message) - 2
                if msg_x > len(controls) + 3:
                    if self.error_message:
                        msg_attr = curses.color_pair(7) | curses.A_BOLD
                    elif "✓" in message or "Saved" in message:
                        msg_attr = curses.color_pair(4) | curses.A_BOLD
                    else:
                        msg_attr = curses.color_pair(2)

                    self.stdscr.addstr(status_y, msg_x, message, msg_attr)
        except curses.error:
            pass

    def set_message(self, message: str, is_error: bool = False):
        if is_error:
            self.error_message = message
            self.status_message = ""
        else:
            self.status_message = message
            self.error_message = ""
