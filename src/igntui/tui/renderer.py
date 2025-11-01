#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import curses
import logging

logger = logging.getLogger(__name__)


class TUIRenderer:
    def __init__(self, stdscr, state, ui_components):
        self.stdscr = stdscr
        self.state = state
        self.search_panel = ui_components.get("search_panel")
        self.templates_panel = ui_components.get("templates_panel")
        self.selected_panel = ui_components.get("selected_panel")
        self.content_panel = ui_components.get("content_panel")
        self.status_bar = ui_components.get("status_bar")

    def render(self) -> None:
        try:
            self.stdscr.clear()
            max_y, max_x = self.stdscr.getmaxyx()

            left_width = max_x // 3
            right_width = max_x - left_width
            bottom_height = 6
            search_height = 3
            templates_height = max_y - bottom_height - search_height - 1
            self._render_search_panel(0, 0, search_height, left_width)
            self._render_templates_panel(search_height, 0, templates_height, left_width)
            self._render_content_panel(
                0, left_width, max_y - bottom_height - 1, right_width
            )
            self._render_selected_panel(
                max_y - bottom_height - 1, 0, bottom_height, max_x
            )
            self._render_status_bar()
            self.stdscr.refresh()

        except curses.error as e:
            logger.debug(f"Curses error during render: {e}")

    def _render_search_panel(self, y: int, x: int, height: int, width: int) -> None:
        if self.search_panel:
            try:
                self.search_panel.filter_text = self.state.filter_text
                self.search_panel.current_search_mode = self.state.current_search_mode
                self.search_panel.is_active = self.state.current_panel == 0
                self.search_panel.draw()
            except Exception as e:
                logger.error(f"Error rendering search panel: {e}")

    def _render_templates_panel(self, y: int, x: int, height: int, width: int) -> None:
        if self.templates_panel:
            try:
                display_templates = self.state.get_display_templates()
                self.templates_panel.templates = self.state.templates
                self.templates_panel.filtered_templates = display_templates
                self.templates_panel.selected_templates = self.state.selected_templates
                self.templates_panel.template_selected = self.state.template_selected
                self.templates_panel.template_scroll = self.state.template_scroll
                self.templates_panel.is_active = self.state.current_panel == 1
                self.templates_panel.loading = self.state.loading
                self.templates_panel.filter_text = self.state.filter_text
                self.templates_panel.current_search_mode = (
                    self.state.current_search_mode
                )

                self.templates_panel.draw()
            except Exception as e:
                logger.error(f"Error rendering templates panel: {e}")

    def _render_selected_panel(self, y: int, x: int, height: int, width: int) -> None:
        if self.selected_panel:
            try:
                self.selected_panel.selected_templates = self.state.selected_templates
                self.selected_panel.selected_index = self.state.selected_index
                self.selected_panel.selected_scroll = self.state.selected_scroll
                self.selected_panel.is_active = self.state.current_panel == 2
                self.selected_panel.draw()
            except Exception as e:
                logger.error(f"Error rendering selected panel: {e}")

    def _render_content_panel(self, y: int, x: int, height: int, width: int) -> None:
        if self.content_panel:
            try:
                self.content_panel.generated_content = self.state.generated_content
                self.content_panel.content_scroll = self.state.content_scroll
                self.content_panel.is_active = self.state.current_panel == 3
                self.content_panel.generation_in_progress = (
                    self.state.generation_in_progress
                )
                self.content_panel.draw()
            except Exception as e:
                logger.error(f"Error rendering content panel: {e}")

    def _render_status_bar(self) -> None:
        if self.status_bar:
            try:
                self.status_bar.status_message = self.state.status_message
                self.status_bar.error_message = self.state.error_message
                self.status_bar.draw(
                    self.state.current_panel, self.state.current_search_mode
                )
            except Exception as e:
                logger.error(f"Error rendering status bar: {e}")
