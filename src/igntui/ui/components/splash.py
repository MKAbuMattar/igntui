#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import curses
import logging
import threading
import time
from typing import Callable, Optional

logger = logging.getLogger(__name__)

try:
    import pyfiglet

    HAS_PYFIGLET = True
except ImportError:
    HAS_PYFIGLET = False
    logger.warning("pyfiglet not installed - using basic ASCII art")


class SplashScreen:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.loading_complete = False
        self.loading_error: Optional[str] = None
        self.template_count = 0
        self.current_stage = 0
        self.stages = [
            ("🌐", "Connecting to gitignore.io..."),
            ("📡", "Fetching template list..."),
            ("📥", "Loading templates..."),
            ("✅", "Ready!"),
        ]

    def show(self, load_callback: Optional[Callable] = None) -> bool:
        max_y, max_x = self.stdscr.getmaxyx()
        self.stdscr.clear()

        if HAS_PYFIGLET:
            try:
                figlet = pyfiglet.Figlet(font="slant", width=max_x)
                logo_text = figlet.renderText("igntui")
                logo = logo_text.split("\n")
            except Exception as e:
                logger.warning(f"pyfiglet error: {e}, using fallback")
                logo = self._get_fallback_logo()
        else:
            logo = self._get_fallback_logo()

        if load_callback:
            loading_thread = threading.Thread(
                target=self._load_in_background, args=(load_callback,)
            )
            loading_thread.daemon = True
            loading_thread.start()

        start_time = time.time()
        last_stage = -1

        while not self.loading_complete:
            self.stdscr.clear()

            logo_height = len(logo)
            logo_start_y = max(1, (max_y - logo_height - 20) // 2)

            for i, line in enumerate(logo):
                if line.strip():
                    x_pos = max(0, (max_x - len(line)) // 2)
                    try:
                        self.stdscr.addstr(
                            logo_start_y + i,
                            x_pos,
                            line,
                            curses.color_pair(4) | curses.A_BOLD,
                        )
                    except curses.error:
                        pass

            subtitle = "GitIgnore Template Generator"
            sub_y = logo_start_y + logo_height + 1
            sub_x = max(0, (max_x - len(subtitle)) // 2)
            try:
                self.stdscr.addstr(
                    sub_y, sub_x, subtitle, curses.color_pair(6) | curses.A_BOLD
                )
            except curses.error:
                pass

            status_y = sub_y + 3

            if self.current_stage < len(self.stages):
                emoji, message = self.stages[self.current_stage]
                status_msg = f"{emoji}  {message}"

                if self.current_stage != last_stage:
                    last_stage = self.current_stage
                    logger.debug(f"Splash stage: {message}")

                x_pos = max(0, (max_x - len(status_msg)) // 2)
                try:
                    attr = curses.color_pair(2) | curses.A_BOLD
                    if "Ready" in message:
                        attr = curses.color_pair(4) | curses.A_BOLD
                    self.stdscr.addstr(status_y, x_pos, status_msg, attr)
                except curses.error:
                    pass

            progress_y = status_y + 2
            progress_width = min(60, max_x - 10)
            progress_x = max(0, (max_x - progress_width) // 2)

            if load_callback:
                progress = min(0.95, self.current_stage / len(self.stages))
            else:
                elapsed = time.time() - start_time
                progress = min(1.0, elapsed / 1.0)

            filled = int(progress_width * progress)

            try:
                self.stdscr.addstr(
                    progress_y, progress_x - 1, "[", curses.color_pair(1)
                )
                self.stdscr.addstr(
                    progress_y, progress_x + progress_width, "]", curses.color_pair(1)
                )

                for i in range(progress_width):
                    if i < filled:
                        self.stdscr.addch(
                            progress_y, progress_x + i, "█", curses.color_pair(4)
                        )
                    else:
                        self.stdscr.addch(
                            progress_y, progress_x + i, "░", curses.color_pair(1)
                        )

                percent = f"{int(progress * 100)}%"
                percent_x = max(0, (max_x - len(percent)) // 2)
                self.stdscr.addstr(
                    progress_y + 1, percent_x, percent, curses.color_pair(8)
                )
            except curses.error:
                pass

            footer_y = progress_y + 4
            footer = "by Mohammad Abu Mattar • github.com/MKAbuMattar"
            footer_x = max(0, (max_x - len(footer)) // 2)
            try:
                self.stdscr.addstr(
                    footer_y, footer_x, footer, curses.color_pair(1) | curses.A_DIM
                )
            except curses.error:
                pass

            self.stdscr.refresh()

            if not load_callback:
                if time.time() - start_time >= 1.0:
                    self.loading_complete = True

            time.sleep(0.05)

        self.stdscr.clear()

        if self.loading_error:
            error_msg = f"✗ Error: {self.loading_error}"
            x_pos = max(0, (max_x - len(error_msg)) // 2)
            try:
                self.stdscr.addstr(
                    max_y // 2, x_pos, error_msg, curses.color_pair(3) | curses.A_BOLD
                )
                continue_msg = "Press any key to continue anyway..."
                x_pos = max(0, (max_x - len(continue_msg)) // 2)
                self.stdscr.addstr(
                    max_y // 2 + 2, x_pos, continue_msg, curses.color_pair(8)
                )
            except curses.error:
                pass
            self.stdscr.refresh()
            self.stdscr.timeout(5000)
            self.stdscr.getch()
            return False
        else:
            if self.template_count > 0:
                success_msg = f"✓ Loaded {self.template_count} templates"
                x_pos = max(0, (max_x - len(success_msg)) // 2)
                try:
                    self.stdscr.addstr(
                        max_y // 2,
                        x_pos,
                        success_msg,
                        curses.color_pair(4) | curses.A_BOLD,
                    )
                except curses.error:
                    pass

            self.stdscr.refresh()
            time.sleep(0.5)
            return True

    def _load_in_background(self, load_callback: Callable) -> None:
        try:
            self.current_stage = 0
            time.sleep(0.3)
            self.current_stage = 1
            time.sleep(0.3)
            self.current_stage = 2
            success, count, error = load_callback()

            if not success:
                self.loading_error = error
            else:
                self.template_count = count
                self.current_stage = 3
                time.sleep(0.3)

        except Exception as e:
            logger.error(f"Error in splash loading: {e}", exc_info=True)
            self.loading_error = str(e)
        finally:
            self.loading_complete = True

    def _get_fallback_logo(self) -> list:
        return [
            "  _                   _         _ ",
            " (_)   __ _   _ __   | |_  _   (_)",
            " | |  / _` | | '_ \\  | __|| | | | ",
            " | | | (_| | | | | | | |_ | |_| | ",
            " |_|  \\__, | |_| |_|  \\__| \\__,_| ",
            "      |___/                       ",
        ]
        self.stdscr.timeout(100)
        self.stdscr.clear()
        self.stdscr.refresh()
