import asyncio
import pytest
from base64 import b64encode
from typing import Awaitable, Callable, List, Optional

import respx
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from prerender_python_starlette.middleware import PrerenderMiddleware


@pytest.fixture
def get_test_client():
    def _get_test_client(
        whitelist: List[str] = None,
        blacklist: List[str] = None,
        before_render: Callable[[Request], Awaitable[Optional[HTMLResponse]]] = None,
        after_render: Callable[[Request, HTMLResponse], Awaitable[None]] = None,
        username: str = None,
        password: str = None,
        token: str = None,
    ) -> TestClient:
        def main_get(r):
            return HTMLResponse("<html><body>RAW</body></html>")

        def main_post(r):
            return HTMLResponse("<html><body>RAW</body></html>")

        def js_get(r):
            return HTMLResponse("<html><body>RAW</body></html>")

        def whitelisted_url1(r):
            return HTMLResponse("<html><body>RAW</body></html>")

        def blacklisted_url1(r):
            return HTMLResponse("<html><body>RAW</body></html>")

        def whitelisted_blacklisted_url(r):
            return HTMLResponse("<html><body>RAW</body></html>")

        routes = [
            Route("/", endpoint=main_get, methods=["GET"]),
            Route("/", endpoint=main_post, methods=["POST"]),
            Route("/file.js", endpoint=js_get, methods=["GET"]),
            Route("/whitelisted-url1", endpoint=whitelisted_url1, methods=["GET"]),
            Route("/blacklisted-url1", endpoint=blacklisted_url1, methods=["GET"]),
            Route(
                "/whitelisted-url-blacklisted-url",
                endpoint=whitelisted_blacklisted_url,
                methods=["GET"],
            ),
        ]

        middleware = [
            Middleware(
                PrerenderMiddleware,
                prerender_service_url="http://prerender.bar.com",
                prerender_service_username=username,
                prerender_service_password=password,
                prerender_service_token=token,
                whitelist=whitelist,
                blacklist=blacklist,
                before_render=before_render,
                after_render=after_render,
            ),
        ]

        app = Starlette(routes=routes, middleware=middleware)

        return TestClient(app)

    return _get_test_client


@respx.mock
@pytest.mark.parametrize(
    "whitelist,blacklist,user_agent,buffer_agent,prerender_agent,method,path,prerendered",
    [
        (None, None, None, None, None, "GET", "/", False),
        (None, None, "Chrome", None, None, "GET", "/", False),
        (None, None, "googlebot", None, None, "GET", "/", True),
        (None, None, "LinkedInBot/1.0", None, None, "GET", "/", True),
        (None, None, "Chrome", "Buffer", None, "GET", "/", True),
        (None, None, "Chrome", None, "Prerender", "GET", "/", False),
        (None, None, "googlebot", None, None, "POST", "/", False),
        (None, None, "googlebot", None, None, "GET", "/file.js", False),
        (
            ["^/whitelisted-url"],
            None,
            "googlebot",
            None,
            None,
            "GET",
            "/whitelisted-url1",
            True,
        ),
        (["^/whitelisted-url"], None, "googlebot", None, None, "GET", "/", False),
        (
            None,
            ["^/blacklisted-url"],
            "googlebot",
            None,
            None,
            "GET",
            "/blacklisted-url1",
            False,
        ),
        (None, ["^/blacklisted-url"], "googlebot", None, None, "GET", "/", True),
        (
            ["^/whitelisted-url"],
            [".*blacklisted-url$"],
            "googlebot",
            None,
            None,
            "GET",
            "/whitelisted-url-blacklisted-url",
            False,
        ),
    ],
)
def test_prerender(
    get_test_client,
    whitelist,
    blacklist,
    user_agent,
    buffer_agent,
    prerender_agent,
    method,
    path,
    prerendered,
):
    request = respx.request(
        method,
        f"http://prerender.bar.com/http://testserver{path}",
        content="<html><body>PRERENDERED</body></html>",
    )

    test_client = get_test_client(whitelist, blacklist)

    headers = {}
    if user_agent:
        headers["user-agent"] = user_agent
    if buffer_agent:
        headers["x-bufferbot"] = buffer_agent
    if prerender_agent:
        headers["x-prerender"] = prerender_agent

    response = test_client.request(method, path, headers=headers)

    if prerendered:
        assert request.called
        assert response.text == "<html><body>PRERENDERED</body></html>"
        assert response.headers.get("content-type") == "text/html; charset=utf-8"
    else:
        assert request.called is False
        assert response.text == "<html><body>RAW</body></html>"


def test_before_render(mocker, get_test_client):
    future = asyncio.Future()
    future.set_result(HTMLResponse("<html><body>PRERENDERED</body></html>"))
    get_prerendered_response_mock = mocker.patch(
        "prerender_python_starlette.middleware.PrerenderMiddleware._get_prerendered_response",
        return_value=future,
    )

    async def before_render(request: Request) -> Optional[HTMLResponse]:
        return HTMLResponse("<html><body>CACHED</body></html>")

    test_client = get_test_client(before_render=before_render)
    response = test_client.request("GET", "/", headers={"user-agent": "googlebot"})

    assert get_prerendered_response_mock.called is False
    assert response.text == "<html><body>CACHED</body></html>"
    assert response.headers.get("content-type") == "text/html; charset=utf-8"


@respx.mock
def test_basic_auth(get_test_client):
    request = respx.get(
        f"http://prerender.bar.com/http://testserver/",
        content="<html><body>PRERENDERED</body></html>",
    )

    test_client = get_test_client(username="foo", password="bar")
    test_client.request("GET", "/", headers={"user-agent": "googlebot"})

    assert request.called
    encoded_auth = b64encode(b"foo:bar").decode("latin-1")
    assert request.calls[0][0].headers["Authorization"] == f"Basic {encoded_auth}"


@respx.mock
def test_token(get_test_client):
    request = respx.get(
        f"http://prerender.bar.com/http://testserver/",
        content="<html><body>PRERENDERED</body></html>",
    )

    test_client = get_test_client(token="foo")
    test_client.request("GET", "/", headers={"user-agent": "googlebot"})

    assert request.called
    assert request.calls[0][0].headers["x-prerender-token"] == "foo"


@respx.mock
def test_after_render(mocker, get_test_client):
    request = respx.get(
        f"http://prerender.bar.com/http://testserver/",
        content="<html><body>PRERENDERED</body></html>",
    )

    future = asyncio.Future()
    future.set_result(None)
    after_render = mocker.MagicMock(return_value=future)

    test_client = get_test_client(after_render=after_render)
    response = test_client.request("GET", "/", headers={"user-agent": "googlebot"})

    assert after_render.called
    assert type(after_render.call_args[0][0]) == Request
    assert type(after_render.call_args[0][1]) == HTMLResponse
    assert after_render.call_args[0][2] is False

    assert request.called
    assert response.text == "<html><body>PRERENDERED</body></html>"
    assert response.headers.get("content-type") == "text/html; charset=utf-8"


@respx.mock
def test_before_after_render(mocker, get_test_client):
    request = respx.get(
        f"http://prerender.bar.com/http://testserver/",
        content="<html><body>PRERENDERED</body></html>",
    )

    before_future = asyncio.Future()
    before_future.set_result(HTMLResponse("<html><body>CACHED</body></html>"))
    before_render = mocker.MagicMock(return_value=before_future)

    future = asyncio.Future()
    future.set_result(None)
    after_render = mocker.MagicMock(return_value=future)

    test_client = get_test_client(
        before_render=before_render, after_render=after_render
    )
    response = test_client.request("GET", "/", headers={"user-agent": "googlebot"})

    assert before_render.called

    assert after_render.called
    assert type(after_render.call_args[0][0]) == Request
    assert type(after_render.call_args[0][1]) == HTMLResponse
    assert after_render.call_args[0][2] is True

    assert request.called is False
    assert response.text == "<html><body>CACHED</body></html>"
    assert response.headers.get("content-type") == "text/html; charset=utf-8"
