"""Keyboard handling: the biggest module in the tree, and the least covered.

`handle_input` is a pure function of (key, state) plus optional callbacks — no
curses calls on any path except the mouse one. So the keymap is testable without
a terminal, which matters because a broken binding is invisible: the TUI keeps
running and simply stops responding to that key.

Panel indices: 0=search, 1=templates, 2=selected, 3=content.
"""

import curses

import pytest

from igntui.tui.event_handler import EventHandler
from igntui.tui.state import TUIState

TEMPLATES = ["python", "node", "macos", "windows", "rust"]


class FakeLifecycle:
    """The two things the handler asks of the lifecycle: filtering and usage."""

    def __init__(self):
        self.calls = 0
        self.recorded: list[str] = []

    def filter_templates(self, templates, filter_text, search_mode="fuzzy"):
        self.calls += 1
        if not filter_text:
            return list(templates)
        return [t for t in templates if filter_text.lower() in t.lower()]

    def record_usage(self, template):
        self.recorded.append(template)


@pytest.fixture
def handler():
    state = TUIState()
    state.templates = list(TEMPLATES)
    state.filtered_templates = list(TEMPLATES)
    state.loading = False
    state.current_panel = 1
    return EventHandler(state, FakeLifecycle(), stdscr=None)


def press(handler, *keys) -> bool:
    result = True
    for key in keys:
        result = handler.handle_input(key)
    return result


def test_quit_outside_search_stops_the_loop(handler):
    fired = []
    handler.on_quit = lambda: fired.append(True)

    assert press(handler, ord("q")) is False
    assert fired == [True]


@pytest.mark.parametrize("key", [ord("q"), ord("Q"), 27])
def test_q_and_escape_all_quit_outside_search(handler, key):
    handler.on_quit = lambda: None
    assert handler.handle_input(key) is False


def test_escape_inside_search_leaves_search_instead_of_quitting(handler):
    """Regression: Esc in the search box used to kill the app mid-typing."""
    handler.state.current_panel = 0
    quit_called = []
    handler.on_quit = lambda: quit_called.append(True)

    assert handler.handle_input(27) is True
    assert handler.state.current_panel == 1
    assert quit_called == []


@pytest.mark.parametrize("key", [ord("q"), ord("Q")])
def test_q_inside_search_is_typed_as_a_letter(handler, key):
    handler.state.current_panel = 0

    assert handler.handle_input(key) is True
    assert handler.state.filter_text == chr(key)


def test_tab_cycles_panels_forward_and_back(handler):
    handler.state.current_panel = 0
    for expected in (1, 2, 3, 0):
        handler.handle_input(ord("\t"))
        assert handler.state.current_panel == expected

    handler.handle_input(curses.KEY_BTAB)
    assert handler.state.current_panel == 3


@pytest.mark.parametrize(
    "key,mode",
    [(curses.KEY_F1, "fuzzy"), (curses.KEY_F2, "exact"), (curses.KEY_F3, "regex")],
)
def test_function_keys_switch_search_mode_and_refilter(handler, key, mode):
    before = handler.lifecycle.calls

    handler.handle_input(key)

    assert handler.state.current_search_mode == mode
    assert handler.lifecycle.calls == before + 1
    assert mode.upper() in handler.state.status_message


@pytest.mark.parametrize(
    "key,callback",
    [
        (ord("i"), "on_info"),
        (ord("h"), "on_help"),
        (ord("?"), "on_help"),
        (ord("s"), "on_save"),
        (ord("e"), "on_export"),
        (ord("r"), "on_refresh"),
        (curses.KEY_F5, "on_refresh"),
        (curses.KEY_F12, "on_help"),
    ],
)
def test_action_keys_reach_their_callback(handler, key, callback):
    fired = []
    setattr(handler, callback, lambda: fired.append(callback))

    assert handler.handle_input(key) is True
    assert fired == [callback]


@pytest.mark.parametrize("key", [ord("i"), ord("h"), ord("s"), ord("e"), ord("r"), curses.KEY_F5])
def test_action_keys_are_safe_with_no_callback_wired(handler, key):
    """Every callback is Optional; an unwired one must not raise."""
    assert handler.handle_input(key) is True


def test_slash_focuses_search(handler):
    handler.handle_input(ord("/"))
    assert handler.state.current_panel == 0


def test_space_toggles_the_highlighted_template(handler):
    handler.state.template_selected = 1  # "node"

    handler.handle_input(ord(" "))
    assert "node" in handler.state.selected_templates
    # Selecting is what feeds the recently-used list that pins rows to the top.
    assert handler.lifecycle.recorded == ["node"]

    handler.handle_input(ord(" "))
    assert "node" not in handler.state.selected_templates


@pytest.mark.parametrize("key", [ord("\n"), ord("\r")])
def test_enter_selects_too(handler, key):
    handler.state.template_selected = 0

    handler.handle_input(key)

    assert "python" in handler.state.selected_templates


def test_a_selects_every_visible_template_and_x_removes_them(handler):
    handler.handle_input(ord("a"))
    assert handler.state.selected_templates == set(TEMPLATES)

    handler.handle_input(ord("x"))
    assert handler.state.selected_templates == set()


def test_c_clears_selections_and_content(handler):
    handler.state.selected_templates = {"python"}
    handler.state.generated_content = "old content"

    handler.handle_input(ord("c"))

    assert handler.state.selected_templates == set()
    assert handler.state.generated_content == ""


def test_arrows_move_the_highlight_without_leaving_bounds(handler):
    handler.handle_input(curses.KEY_UP)
    assert handler.state.template_selected == 0

    for _ in range(len(TEMPLATES) + 5):
        handler.handle_input(curses.KEY_DOWN)
    assert handler.state.template_selected <= len(TEMPLATES) - 1

    handler.handle_input(curses.KEY_HOME)
    assert handler.state.template_selected == 0
    handler.handle_input(curses.KEY_END)
    assert handler.state.template_selected == len(TEMPLATES) - 1


def test_page_keys_do_not_escape_the_list(handler):
    handler.handle_input(curses.KEY_NPAGE)
    assert 0 <= handler.state.template_selected < len(TEMPLATES)

    handler.handle_input(curses.KEY_PPAGE)
    assert handler.state.template_selected >= 0


def test_typing_filters_and_backspace_undoes_it(handler):
    handler.state.current_panel = 0

    press(handler, ord("p"), ord("y"))
    assert handler.state.filter_text == "py"
    assert handler.state.filtered_templates == ["python"]

    handler.handle_input(curses.KEY_BACKSPACE)
    assert handler.state.filter_text == "p"

    press(handler, 127)  # the other backspace encoding
    assert handler.state.filter_text == ""
    assert handler.state.filtered_templates == TEMPLATES


def test_cursor_editing_inserts_mid_string(handler):
    handler.state.current_panel = 0
    press(handler, ord("p"), ord("n"))

    handler.handle_input(curses.KEY_LEFT)
    handler.handle_input(ord("y"))

    assert handler.state.filter_text == "pyn"
    assert handler.state.cursor_position == 2


def test_delete_key_removes_forward(handler):
    handler.state.current_panel = 0
    press(handler, ord("a"), ord("b"))
    handler.handle_input(curses.KEY_HOME)

    handler.handle_input(curses.KEY_DC)

    assert handler.state.filter_text == "b"


def test_ctrl_u_clears_the_whole_query(handler):
    handler.state.current_panel = 0
    press(handler, ord("n"), ord("o"), ord("d"), ord("e"))

    handler.handle_input(21)  # Ctrl-U

    assert handler.state.filter_text == ""
    assert handler.state.cursor_position == 0
    assert handler.state.filtered_templates == TEMPLATES


def test_ctrl_a_and_ctrl_e_jump_to_the_ends(handler):
    handler.state.current_panel = 0
    press(handler, ord("r"), ord("s"))

    handler.handle_input(1)  # Ctrl-A
    assert handler.state.cursor_position == 0
    handler.handle_input(5)  # Ctrl-E
    assert handler.state.cursor_position == 2


def test_cursor_cannot_run_off_either_end(handler):
    handler.state.current_panel = 0

    for _ in range(3):
        handler.handle_input(curses.KEY_LEFT)
    assert handler.state.cursor_position == 0

    handler.handle_input(ord("x"))
    for _ in range(3):
        handler.handle_input(curses.KEY_RIGHT)
    assert handler.state.cursor_position == len(handler.state.filter_text)


def test_unhandled_key_keeps_the_loop_running(handler):
    assert handler.handle_input(curses.KEY_F9) is True
    assert handler.handle_input(0) is True


def test_mouse_event_without_a_screen_is_ignored(handler):
    """stdscr is Optional; the mouse path must not raise when it is None."""
    assert handler.handle_input(curses.KEY_MOUSE) is True
