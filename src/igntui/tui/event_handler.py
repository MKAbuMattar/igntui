#!/usr/bin/env python3


import curses
import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)


class EventHandler:
    def __init__(self, state, lifecycle, stdscr=None):
        self.state = state
        self.lifecycle = lifecycle
        self.stdscr = stdscr
        self.on_quit: Callable[[], None] | None = None
        self.on_help: Callable[[], None] | None = None
        self.on_info: Callable[[], None] | None = None
        self.on_save: Callable[[], None] | None = None
        self.on_export: Callable[[], None] | None = None
        self.on_refresh: Callable[[], None] | None = None
        self.on_generate: Callable[[], None] | None = None

    def handle_input(self, key: int) -> bool:
        if key == curses.KEY_MOUSE:
            return self._handle_mouse()

        if key == curses.KEY_F1:
            self.state.current_search_mode = "fuzzy"
            self._apply_filter()
            self.state.set_status_message("Search mode: FUZZY")
            return True

        elif key == curses.KEY_F2:
            self.state.current_search_mode = "exact"
            self._apply_filter()
            self.state.set_status_message("Search mode: EXACT")
            return True

        elif key == curses.KEY_F3:
            self.state.current_search_mode = "regex"
            self._apply_filter()
            self.state.set_status_message("Search mode: REGEX")
            return True

        elif key == curses.KEY_F5:
            if self.on_refresh:
                self.on_refresh()
            return True

        elif key == curses.KEY_F12:
            if self.on_help:
                self.on_help()
            return True

        # Quit / leave-search semantics:
        # - In any panel except Search: q / Q / Esc → quit the app
        # - In Search panel:
        #     • Esc → exit search mode (focus Templates instead)
        #     • q / Q → typed as letters into the search box
        if key in (ord("q"), ord("Q"), 27):
            if self.state.current_panel != 0:
                if self.on_quit:
                    self.on_quit()
                return False
            if key == 27:
                self.state.current_panel = 1
                self.state.set_status_message("Exited search mode")
                return True
            # q / Q while focused on Search — fall through to typing
            self._handle_search_input(key)
            return True

        if key == ord("\t"):
            self.state.current_panel = (self.state.current_panel + 1) % 4
            return True

        elif key == curses.KEY_BTAB:
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
        if key in (8, 127, curses.KEY_BACKSPACE):
            if self.state.cursor_position > 0:
                self.state.filter_text = (
                    self.state.filter_text[:self.state.cursor_position - 1] +
                    self.state.filter_text[self.state.cursor_position:]
                )
                self.state.cursor_position -= 1
                self._apply_filter()
                self.state.adjust_template_selection_bounds()

        elif key == curses.KEY_DC:
            if self.state.cursor_position < len(self.state.filter_text):
                self.state.filter_text = (
                    self.state.filter_text[:self.state.cursor_position] +
                    self.state.filter_text[self.state.cursor_position + 1:]
                )
                self._apply_filter()
                self.state.adjust_template_selection_bounds()

        elif key == curses.KEY_LEFT:
            self.state.cursor_position = max(0, self.state.cursor_position - 1)

        elif key == curses.KEY_RIGHT:
            self.state.cursor_position = min(len(self.state.filter_text), self.state.cursor_position + 1)

        elif key == curses.KEY_HOME:
            self.state.cursor_position = 0

        elif key == curses.KEY_END:
            self.state.cursor_position = len(self.state.filter_text)

        elif key == 21:
            self.state.filter_text = ""
            self.state.cursor_position = 0
            self._apply_filter()
            self.state.reset_template_selection()
            self.state.set_status_message("Search cleared")

        elif key == 1:
            self.state.cursor_position = 0

        elif key == 5:
            self.state.cursor_position = len(self.state.filter_text)

        elif 32 <= key <= 126:
            char = chr(key)
            self.state.filter_text = (
                self.state.filter_text[:self.state.cursor_position] +
                char +
                self.state.filter_text[self.state.cursor_position:]
            )
            self.state.cursor_position += 1
            self._apply_filter()
            self.state.adjust_template_selection_bounds()

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

    def _handle_mouse(self) -> bool:
        if self.stdscr is None:
            return True
        try:
            _, mx, my, _, bstate = curses.getmouse()
        except curses.error:
            return True

        panel, panel_top = self._panel_at(mx, my)

        # Scroll wheel events scroll the panel under the cursor WITHOUT changing focus.
        scroll_up = getattr(curses, "BUTTON4_PRESSED", 0)
        scroll_down = getattr(curses, "BUTTON5_PRESSED", 0)
        if scroll_up and (bstate & scroll_up):
            self._scroll_panel(panel, direction=-1)
            return True
        if scroll_down and (bstate & scroll_down):
            self._scroll_panel(panel, direction=+1)
            return True

        # Anything else (click / press) focuses the panel under the cursor.
        if panel is None:
            return True
        self.state.current_panel = panel

        # In the Templates panel, also pick the row under the cursor and toggle
        # selection on a click.
        if panel == 1 and panel_top is not None:
            row = my - panel_top - 1  # account for 1-line border
            display = self.state.get_display_templates()
            if 0 <= row:
                target = self.state.template_scroll + row
                if target < len(display):
                    self.state.template_selected = target
                    if bstate & curses.BUTTON1_CLICKED:
                        self._handle_selection()
        return True

    def _panel_at(self, mx: int, my: int) -> tuple[int | None, int | None]:
        """Return (panel_index, panel_top_y) for the panel at the given coords."""
        max_y, max_x = self.stdscr.getmaxyx()
        left_width = max_x // 3
        bottom_height = 6
        search_height = 3
        templates_top = search_height
        selected_top = max_y - bottom_height - 1

        # Selected panel (bottom strip, full width) wins because it overlays
        # the bottom of the templates/content columns.
        if my >= selected_top:
            return (2, selected_top)
        if my < search_height and mx < left_width:
            return (0, 0)
        if templates_top <= my < selected_top and mx < left_width:
            return (1, templates_top)
        if mx >= left_width:
            return (3, 0)
        return (None, None)

    def _scroll_panel(self, panel: int | None, direction: int) -> None:
        """Scroll the panel under the cursor without changing focus.

        `direction` is +1 (wheel down) or -1 (wheel up).

        For list panels we move the scroll offset *and* drag the selection
        into the new visible window so the renderer's auto-snap (which keeps
        the selected row on-screen) doesn't undo the scroll on the next frame.
        """
        if panel == 1:
            display = self.state.get_display_templates()
            if not display:
                return
            visible = self._templates_visible_count()
            max_scroll = max(0, len(display) - visible)
            new_scroll = max(
                0, min(max_scroll, self.state.template_scroll + direction)
            )
            self.state.template_scroll = new_scroll
            sel = self.state.template_selected
            if sel < new_scroll:
                self.state.template_selected = new_scroll
            elif sel >= new_scroll + visible:
                self.state.template_selected = max(0, new_scroll + visible - 1)
        elif panel == 2:
            count = self.state.get_selection_count()
            if count == 0:
                return
            visible = self._selected_visible_count()
            max_scroll = max(0, count - visible)
            new_scroll = max(
                0, min(max_scroll, self.state.selected_scroll + direction)
            )
            self.state.selected_scroll = new_scroll
            idx = self.state.selected_index
            if idx < new_scroll:
                self.state.selected_index = new_scroll
            elif idx >= new_scroll + visible:
                self.state.selected_index = max(0, new_scroll + visible - 1)
        elif panel == 3:
            content_lines = len(self.state.generated_content.split("\n"))
            self.state.content_scroll = max(
                0, min(max(0, content_lines - 1), self.state.content_scroll + direction)
            )

    def _templates_visible_count(self) -> int:
        """Visible rows in the Templates panel (matches templates_panel.py geometry)."""
        if self.stdscr is None:
            return 1
        max_y, _ = self.stdscr.getmaxyx()
        bottom_height = 6
        search_height = 3
        templates_height = max_y - bottom_height - search_height - 1
        # 2 lines borders + 1 line count header = 3 reserved lines.
        return max(1, templates_height - 3)

    def _selected_visible_count(self) -> int:
        if self.stdscr is None:
            return 1
        bottom_height = 6
        # 2 lines borders inside the bottom strip.
        return max(1, bottom_height - 2)

    def _handle_selection(self) -> None:
        if self.state.current_panel == 1:
            display_templates = self.state.get_display_templates()
            if display_templates and self.state.template_selected < len(
                display_templates
            ):
                template = display_templates[self.state.template_selected]
                was_selected = template in self.state.selected_templates
                self.state.toggle_template_selection(template)

                if not was_selected:
                    self.state.set_status_message(f"Added: {template}")
                    self.lifecycle.record_usage(template)
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
