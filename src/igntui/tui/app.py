#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import curses
import logging
import time
from typing import Optional

from ..core.api import GitIgnoreAPI
from ..core.search import SearchManager
from ..ui import (
    ContentPanel,
    SearchPanel,
    SelectedPanel,
    SplashScreen,
    StatusBar,
    TemplatesPanel,
)
from .actions import TUIActions
from .curses_setup import CursesSetup
from .event_handler import EventHandler
from .lifecycle import TemplateLifecycle
from .renderer import TUIRenderer
from .state import TUIState

logger = logging.getLogger(__name__)


class GitIgnoreTUI:
    def __init__(self, stdscr, show_splash: bool = True):
        self.stdscr = stdscr
        self.show_splash = show_splash
        self.api = GitIgnoreAPI()
        self.search_manager = SearchManager()
        self.state = TUIState()

        CursesSetup.setup_curses(stdscr)

        if self.show_splash:
            try:
                splash = SplashScreen(self.stdscr)
                success = splash.show(load_callback=self._load_templates_sync)
                self.state.loading = False
                if success and self.state.templates:
                    logger.info(
                        f"Splash loaded {len(self.state.templates)} templates successfully"
                    )
            except Exception as e:
                logger.warning(f"Could not show splash screen: {e}")
                self.state.loading = False

        self._init_ui_components()
        self.lifecycle = TemplateLifecycle(self.api, self.search_manager)
        self.actions = TUIActions(self.stdscr, self.state)
        self.event_handler = EventHandler(self.state, self.lifecycle)
        self._setup_event_callbacks()
        self.renderer = TUIRenderer(
            self.stdscr,
            self.state,
            {
                "search_panel": self.search_panel,
                "templates_panel": self.templates_panel,
                "selected_panel": self.selected_panel,
                "content_panel": self.content_panel,
                "status_bar": self.status_bar,
            },
        )

        if not self.state.templates:
            self._load_templates_async()

        logger.info("GitIgnoreTUI initialized successfully")

    def _init_ui_components(self) -> None:
        max_y, max_x = self.stdscr.getmaxyx()

        try:
            left_width = max_x // 3
            right_width = max_x - left_width
            bottom_height = 6
            search_height = 3
            templates_height = max_y - bottom_height - search_height - 1

            self.search_panel = SearchPanel(
                self.stdscr, y=0, x=0, height=search_height, width=left_width
            )

            self.templates_panel = TemplatesPanel(
                self.stdscr,
                y=search_height,
                x=0,
                height=templates_height,
                width=left_width,
            )

            self.selected_panel = SelectedPanel(
                self.stdscr,
                y=max_y - bottom_height - 1,
                x=0,
                height=bottom_height,
                width=max_x,
            )

            self.content_panel = ContentPanel(
                self.stdscr,
                y=0,
                x=left_width,
                height=max_y - bottom_height - 1,
                width=right_width,
            )

            self.status_bar = StatusBar(self.stdscr)

            logger.debug("UI components initialized")

        except Exception as e:
            logger.error(f"Error initializing UI components: {e}")
            raise

    def _setup_event_callbacks(self) -> None:
        self.event_handler.on_quit = self._handle_quit
        self.event_handler.on_help = self.actions.show_help_dialog
        self.event_handler.on_info = self.actions.show_info_dialog
        self.event_handler.on_save = self.actions.save_gitignore
        self.event_handler.on_export = self.actions.export_templates
        self.event_handler.on_refresh = self._load_templates_async
        self.event_handler.on_generate = self._generate_content_async

    def _handle_quit(self) -> None:
        self.state.running = False
        logger.info("Quit requested")

    def _load_templates_sync(self) -> tuple:
        try:
            response = self.api.list_templates()
            if response.success and response.data:
                templates = response.data
                self.state.templates = templates
                self.state.filtered_templates = templates[:]
                logger.info(f"Loaded {len(templates)} templates during splash")
                return (True, len(templates), "")
            else:
                error_msg = response.error_message or "No templates returned from API"
                return (False, 0, error_msg)
        except Exception as e:
            error_msg = f"Failed to load templates: {e}"
            logger.error(error_msg, exc_info=True)
            return (False, 0, error_msg)

    def _load_templates_async(self) -> None:
        self.state.loading = True
        self.state.set_status_message("Loading templates...")

        def on_success(templates):
            self.state.templates = templates
            self.state.filtered_templates = templates[:]
            self.state.set_status_message(f"✓ Loaded {len(templates)} templates")

        def on_error(error_msg):
            self.state.set_status_message(error_msg, is_error=True)

        def on_complete():
            self.state.loading = False

        self.lifecycle.load_templates_async(on_success, on_error, on_complete)

    def _generate_content_async(self) -> None:
        if not self.state.selected_templates:
            self.state.generated_content = "# No templates selected\n# Select templates from the Available Templates panel"
            return

        self.state.generation_in_progress = True
        selected_list = self.state.get_selected_templates_list()
        self.state.set_status_message(
            f"Generating content for {len(selected_list)} templates..."
        )

        def on_success(content, from_cache):
            self.state.generated_content = content
            cache_info = " (cached)" if from_cache else ""
            self.state.set_status_message(
                f"✓ Generated content for {len(selected_list)} templates{cache_info}"
            )

        def on_error(error_msg):
            self.state.generated_content = f"# Error generating content: {error_msg}\n# Selected templates: {selected_list}"
            self.state.set_status_message(error_msg, is_error=True)

        def on_complete():
            self.state.generation_in_progress = False

        self.lifecycle.generate_content_async(
            selected_list, on_success, on_error, on_complete
        )

    def run(self) -> int:
        logger.info("Starting TUI main loop")

        try:
            while self.state.running:
                self.state.clear_status_message()
                self.renderer.render()

                try:
                    key = self.stdscr.getch()
                    if key != -1:
                        should_continue = self.event_handler.handle_input(key)
                        if not should_continue:
                            break
                except curses.error:
                    pass

                time.sleep(0.01)

            logger.info("TUI main loop ended normally")
            return 0

        except KeyboardInterrupt:
            logger.info("TUI interrupted by user")
            return 0
        except Exception as e:
            logger.error(f"Error in TUI main loop: {e}", exc_info=True)
            return 1
        finally:
            CursesSetup.cleanup(self.stdscr)


def main() -> int:
    try:
        exit_code = curses.wrapper(lambda stdscr: GitIgnoreTUI(stdscr).run())
        print("\n✓ igntui closed successfully")
        return exit_code
    except KeyboardInterrupt:
        print("\n✓ igntui interrupted by user")
        return 0
    except Exception as e:
        print(f"\n✗ Error running igntui: {e}")
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
