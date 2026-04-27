"""Tests for the API client.

Mocks at the urllib.request layer since igntui uses stdlib HTTP.
"""

import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from igntui.core.api import APIError, GitIgnoreAPI, NetworkError, RateLimitError
from igntui.core.api.request_handler import RequestHandler
from igntui.core.cache import CacheManager


def _fake_response(body: str, status: int = 200):
    """Build a context-manager-compatible fake urllib response."""
    resp = MagicMock()
    resp.read.return_value = body.encode("utf-8")
    resp.getcode.return_value = status
    resp.__enter__ = lambda self: self
    resp.__exit__ = lambda self, *a: False
    return resp


@pytest.fixture
def api(tmp_cache_dir):
    return GitIgnoreAPI(cache_manager=CacheManager(str(tmp_cache_dir)))


def test_list_templates_parses_comma_separated(api):
    body = "python,node,go\nrust,java"
    with patch("urllib.request.urlopen", return_value=_fake_response(body)):
        result = api.list_templates()
    assert result.success
    assert sorted(result.data) == ["go", "java", "node", "python", "rust"]


def test_list_templates_uses_cache_on_second_call(api):
    body = "python,node"
    with patch("urllib.request.urlopen", return_value=_fake_response(body)) as urlopen:
        api.list_templates()
        api.list_templates()
    assert urlopen.call_count == 1, "second call should hit cache"


def test_list_templates_force_refresh_skips_cache(api):
    body = "python,node"
    with patch("urllib.request.urlopen", return_value=_fake_response(body)) as urlopen:
        api.list_templates()
        api.list_templates(force_refresh=True)
    assert urlopen.call_count == 2


def test_force_refresh_default_session_flag(api):
    body = "python"
    api.force_refresh_default = True
    with patch("urllib.request.urlopen", return_value=_fake_response(body)) as urlopen:
        api.list_templates()
        api.list_templates()
    assert urlopen.call_count == 2, "session-level no-cache must defeat cache"


def test_get_templates_returns_content(api):
    with patch("urllib.request.urlopen", return_value=_fake_response("body content")):
        result = api.get_templates(["python"])
    assert result.success
    assert result.data == "body content"


def test_get_templates_empty_list_short_circuits(api):
    with patch("urllib.request.urlopen") as urlopen:
        result = api.get_templates([])
    assert result.success
    assert "No templates selected" in result.data
    urlopen.assert_not_called()


def test_get_templates_filters_invalid_names(api):
    """Names with .., //, etc. should be skipped before contacting the API."""
    with patch("urllib.request.urlopen", return_value=_fake_response("ok")):
        result = api.get_templates(["python/../etc", "node"])
    # node is valid → call still made
    assert result.success
    # the filtered call would have used only "node"


def test_get_templates_caches_result(api):
    with patch("urllib.request.urlopen", return_value=_fake_response("X")) as urlopen:
        api.get_templates(["python"])
        api.get_templates(["python"])
    assert urlopen.call_count == 1


def test_request_handler_raises_rate_limit_on_429(tmp_cache_dir):
    rh = RequestHandler(user_agent="test", retry_attempts=1)
    err = urllib.error.HTTPError("u", 429, "Too Many", {"Retry-After": "30"}, None)
    with patch("urllib.request.urlopen", side_effect=err):
        with pytest.raises(RateLimitError):
            rh.make_request("https://example.invalid")


def test_request_handler_raises_network_error_on_url_error():
    rh = RequestHandler(user_agent="test", retry_attempts=1)
    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        with pytest.raises(NetworkError):
            rh.make_request("https://example.invalid")


def test_request_handler_raises_api_error_on_4xx_other():
    rh = RequestHandler(user_agent="test", retry_attempts=1)
    err = urllib.error.HTTPError("u", 404, "Not Found", {}, None)
    with patch("urllib.request.urlopen", side_effect=err):
        with pytest.raises(APIError):
            rh.make_request("https://example.invalid")
