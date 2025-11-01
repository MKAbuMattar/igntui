#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import curses
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class EventHandler:
    def __init__(self, state, lifecycle):
        self.state = state
        self.lifecycle = lifecycle
        self.on_quit: Optional[Callable[[], None]] = None
        self.on_help: Optional[Callable[[], None]] = None
        self.on_info: Optional[Callable[[], None]] = None
        self.on_save: Optional[Callable[[], None]] = None
        self.on_export: Optional[Callable[[], None]] = None
        self.on_refresh: Optional[Callable[[], None]] = None
        self.on_generate: Optional[Callable[[], None]] = None

    def handle_input(self, key: int) -> bool:
        if key == curses.KEY_F1:
            self.state.current_search_mode = "fuzzy"
            self._apply_filter()
            self.state.set_status_message(f"Search mode: FUZZY")
            return True

        elif key == curses.KEY_F2:
            self.state.current_search_mode = "exact"
            self._apply_filter()
            self.state.set_status_message(f"Search mode: EXACT")
            return True

        elif key == curses.KEY_F3:
            self.state.current_search_mode = "regex"
            self._apply_filter()
            self.state.set_status_message(f"Search mode: REGEX")
            return True

        elif key == curses.KEY_F5:
            if self.on_refresh:
                self.on_refresh()
            return True

        elif key == curses.KEY_F12:
            if self.on_help:
                self.on_help()
            return True

        if key in (ord("q"), ord("Q"), 27):
            if self.state.current_panel != 0:
                if self.on_quit:
                    self.on_quit()
                return False
            else:
                if key == ord("q") or key == ord("Q"):
                    self._handle_search_input(key)
            return True

        if key == ord("\t"):
            self.state.current_panel = (self.state.current_panel + 1) % 4
            return True

        elif key == 353:
            self.state.current_panel = (self.state.current_panel - 1) % 4
            return True

        if self.state.current_panel == 0:
            return self._handle_search_input(key)

        if key == ord("i"):
            if self.on_info:
                self.on_info()
            return True

        elif key == ord("h") or key == ord("?"):
            if self.on_help:
                self.on_help()
            return True

        elif key == ord("s"):
            if self.on_save:
                self.on_save()
            return True

        elif key == ord("e"):
            if self.on_export:
                self.on_export()
            return True

        elif key == ord("r"):
            if self.on_refresh:
                self.on_refresh()
            return True

        elif key == ord("c"):
            self.state.clear_all_selections()
            self.state.generated_content = ""
            self.state.set_status_message("Cleared all selections")
            return True

        elif key == ord("/"):
            self.state.current_panel = 0
            self.state.set_status_message("Search mode - Type to filter templates")
            return True

        elif key == ord("a"):
            self._select_all_visible()
            return True

        elif key == ord("x"):
            self._remove_all_visible()
            return True

        elif key == curses.KEY_UP:
            self._handle_up()
            return True

        elif key == curses.KEY_DOWN:
            self._handle_down()
            return True

        elif key == curses.KEY_PPAGE:
            self._handle_page_up()
            return True

        elif key == curses.KEY_NPAGE:
            self._handle_page_down()
            return True

        elif key == curses.KEY_HOME:
            self._handle_home()
            return True

        elif key == curses.KEY_END:
            self._handle_end()
            return True

        elif key in (ord(" "), ord("\n"), ord("\r")):
            self._handle_selection()
            return True

        return True

    def _handle_search_input(self, key: int) -> bool:
        if key in (8, 127):
            if self.state.filter_text:
                self.state.filter_text = self.state.filter_text[:-1]
                self._apply_filter()
                self.state.reset_template_selection()

        elif key == 21:
            self.state.filter_text = ""
            self._apply_filter()
            self.state.reset_template_selection()
            self.state.set_status_message("Search cleared")

        elif 32 <= key <= 126:
            char = chr(key)
            self.state.filter_text += char
            self._apply_filter()
            self.state.reset_template_selection()

        return True

    def _apply_filter(self) -> None:
        self.state.filtered_templates = self.lifecycle.filter_templates(
            self.state.templates, self.state.filter_text, self.state.current_search_mode
        )

    def _select_all_visible(self) -> None:
        if not self.state.filtered_templates:
            return

        added_count = 0
        for template in self.state.filtered_templates:
            if template not in self.state.selected_templates:
                self.state.selected_templates.add(template)
                added_count += 1

        if added_count > 0:
            self.state.set_status_message(f"Added {added_count} templates")
            if self.on_generate:
                self.on_generate()
        else:
            self.state.set_status_message("All visible templates already selected")

    def _remove_all_visible(self) -> None:
        if not self.state.filtered_templates:
            return

        removed_count = 0
        for template in self.state.filtered_templates:
            if template in self.state.selected_templates:
                self.state.selected_templates.remove(template)
                removed_count += 1

        if removed_count > 0:
            self.state.set_status_message(f"Removed {removed_count} templates")
            if self.on_generate:
                self.on_generate()
        else:
            self.state.set_status_message("No visible templates were selected")

    def _handle_up(self) -> None:
        if self.state.current_panel == 1:
            self.state.template_selected = max(0, self.state.template_selected - 1)
        elif self.state.current_panel == 2:
            self.state.selected_index = max(0, self.state.selected_index - 1)
        elif self.state.current_panel == 3:
            self.state.content_scroll = max(0, self.state.content_scroll - 1)

    def _handle_down(self) -> None:
        if self.state.current_panel == 1:
            display_templates = self.state.get_display_templates()
            if display_templates:
                self.state.template_selected = min(
                    len(display_templates) - 1, self.state.template_selected + 1
                )
        elif self.state.current_panel == 2:
            selected_count = self.state.get_selection_count()
            if selected_count > 0:
                self.state.selected_index = min(
                    selected_count - 1, self.state.selected_index + 1
                )
        elif self.state.current_panel == 3:
            content_lines = len(self.state.generated_content.split("\n"))
            self.state.content_scroll = min(
                max(0, content_lines - 10), self.state.content_scroll + 1
            )

    def _handle_page_up(self) -> None:
        if self.state.current_panel == 1:
            self.state.template_selected = max(0, self.state.template_selected - 10)
        elif self.state.current_panel == 2:
            self.state.selected_index = max(0, self.state.selected_index - 10)
        elif self.state.current_panel == 3:
            self.state.content_scroll = max(0, self.state.content_scroll - 10)

    def _handle_page_down(self) -> None:
        if self.state.current_panel == 1:
            display_templates = self.state.get_display_templates()
            if display_templates:
                self.state.template_selected = min(
                    len(display_templates) - 1, self.state.template_selected + 10
                )
        elif self.state.current_panel == 2:
            selected_count = self.state.get_selection_count()
            if selected_count > 0:
                self.state.selected_index = min(
                    selected_count - 1, self.state.selected_index + 10
                )
        elif self.state.current_panel == 3:
            self.state.content_scroll += 10

    def _handle_home(self) -> None:
        if self.state.current_panel == 1:
            self.state.reset_template_selection()
        elif self.state.current_panel == 2:
            self.state.reset_selected_panel()
        elif self.state.current_panel == 3:
            self.state.reset_content_scroll()

    def _handle_end(self) -> None:
        if self.state.current_panel == 1:
            display_templates = self.state.get_display_templates()
            if display_templates:
                self.state.template_selected = len(display_templates) - 1
        elif self.state.current_panel == 2:
            selected_count = self.state.get_selection_count()
            if selected_count > 0:
                self.state.selected_index = selected_count - 1
        elif self.state.current_panel == 3:
            content_lines = len(self.state.generated_content.split("\n"))
            self.state.content_scroll = max(0, content_lines - 10)

    def _handle_selection(self) -> None:
        if self.state.current_panel == 1:
            display_templates = self.state.get_display_templates()
            if display_templates and self.state.template_selected < len(
                display_templates
            ):
                template = display_templates[self.state.template_selected]
                self.state.toggle_template_selection(template)

                if template in self.state.selected_templates:
                    self.state.set_status_message(f"Added: {template}")
                else:
                    self.state.set_status_message(f"Removed: {template}")

                if self.on_generate:
                    self.on_generate()

        elif self.state.current_panel == 2:
            selected_list = self.state.get_selected_templates_list()
            if selected_list and self.state.selected_index < len(selected_list):
                template_to_remove = selected_list[self.state.selected_index]
                self.state.selected_templates.remove(template_to_remove)
                self.state.set_status_message(f"Removed: {template_to_remove}")

                if self.state.selected_index >= self.state.get_selection_count():
                    self.state.selected_index = max(
                        0, self.state.get_selection_count() - 1
                    )

                if self.on_generate:
                    self.on_generate()
