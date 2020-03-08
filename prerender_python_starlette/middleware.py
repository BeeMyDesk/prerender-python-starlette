import os
import re
from typing import Awaitable, Callable, List, Optional

import httpx
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response
from starlette.types import ASGIApp

DEFAULT_CRAWLER_USER_AGENTS = [
    "googlebot",
    "yahoo",
    "bingbot",
    "baiduspider",
    "facebookexternalhit",
    "twitterbot",
    "rogerbot",
    "linkedinbot",
    "embedly",
    "bufferbot",
    "quora link preview",
    "showyoubot",
    "outbrain",
    "pinterest/0.",
    "developers.google.com/+/web/snippet",
    "www.google.com/webmasters/tools/richsnippets",
    "slackbot",
    "vkshare",
    "w3c_validator",
    "redditbot",
    "applebot",
    "whatsapp",
    "flipboard",
    "tumblr",
    "bitlybot",
    "skypeuripreview",
    "nuzzel",
    "discordbot",
    "google page speed",
    "qwantify",
    "chrome-lighthouse",
]

DEFAULT_EXTENSIONS_TO_IGNORE = [
    ".js",
    ".css",
    ".xml",
    ".less",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".pdf",
    ".doc",
    ".txt",
    ".ico",
    ".rss",
    ".zip",
    ".mp3",
    ".rar",
    ".exe",
    ".wmv",
    ".doc",
    ".avi",
    ".ppt",
    ".mpg",
    ".mpeg",
    ".tif",
    ".wav",
    ".mov",
    ".psd",
    ".ai",
    ".xls",
    ".mp4",
    ".m4a",
    ".swf",
    ".dat",
    ".dmg",
    ".iso",
    ".flv",
    ".m4v",
    ".torrent",
]

PRERENDER_SERVICE_URL = os.environ.get(
    "PRERENDER_SERVICE_URL", "http://service.prerender.io/"
)
PRERENDER_SERVICE_USERNAME = os.environ.get("PRERENDER_SERVICE_USERNAME")
PRERENDER_SERVICE_PASSWORD = os.environ.get("PRERENDER_SERVICE_PASSWORD")
PRERENDER_SERVICE_TOKEN = os.environ.get("PRERENDER_SERVICE_TOKEN")


def is_matching_user_agent(user_agent: str, crawler_user_agents: List[str]) -> bool:
    normalized_user_agent = user_agent.lower()

    for crawler_user_agent in crawler_user_agents:
        if crawler_user_agent in normalized_user_agent:
            return True

    return False


def compile_patterns(patterns: List[str]) -> List[re.Pattern]:
    compiled_patterns: List[re.Pattern] = []
    for pattern in patterns:
        compiled_patterns.append(re.compile(pattern))
    return compiled_patterns


def has_matching_pattern(patterns: List[re.Pattern], string: str) -> bool:
    for pattern in patterns:
        if pattern.match(string):
            return True
    return False


class PrerenderMiddleware(BaseHTTPMiddleware):
    """
    Middleware intercepting requests made by crawler \
    bots to prerender them against a Prerender server.

    :param app: ASGI app.

    :param prerender_service_url: URL of Prerender server.
    Defaults to PRERENDER_SERVICE_URL environment variable.

    :param prerender_service_username: HTTP basic auth username of Prerender server.
    Defaults to PRERENDER_SERVICE_USERNAME environment variable.

    :param prerender_service_password: HTTP basic auth password of Prerender server.
    Defaults to PRERENDER_SERVICE_PASSWORD environment variable.

    :param prerender_service_token: Token set in X-Prerender-Token header.
    Defaults to PRERENDER_SERVICE_TOKEN environment variable.

    :param crawler_user_agents: List of crawler user agents to intercept.
    Defaults to DEFAULT_CRAWLER_USER_AGENTS list.

    :param extensions_to_ignore: List of file extensions to ignore.
    Defaults to DEFAULT_EXTENSIONS_TO_IGNORE list.

    :param whitelist: List of path patterns to whitelist.
    Path not matching a pattern in the list won't be prerendered.
    Defaults to None.

    :param blacklist: List of path patterns to blacklist.
    Path matching a pattern in the list won't be prerendered.
    Defaults to None.

    :param before_render: Async function called before the prerendering.
    If it returns an `HTMLResponse`, it will be considered as cache
    and will bypass the call to the Prerender server.
    Defaults to None.

    :param after_render: Async function called after the prerendering.
    Defaults to None.
    """

    prerender_service_url: str
    prerender_service_username: Optional[str]
    prerender_service_password: Optional[str]
    prerender_service_token: Optional[str]
    crawler_user_agents: List[str]
    extensions_to_ignore: List[str]
    whitelist: Optional[List[re.Pattern]] = None
    blacklist: Optional[List[re.Pattern]] = None
    before_render: Optional[
        Callable[[Request], Awaitable[Optional[HTMLResponse]]]
    ] = None
    after_render: Optional[
        Callable[[Request, HTMLResponse, bool], Awaitable[None]]
    ] = None

    def __init__(
        self,
        app: ASGIApp,
        prerender_service_url: str = PRERENDER_SERVICE_URL,
        prerender_service_username: Optional[str] = PRERENDER_SERVICE_USERNAME,
        prerender_service_password: Optional[str] = PRERENDER_SERVICE_PASSWORD,
        prerender_service_token: Optional[str] = PRERENDER_SERVICE_TOKEN,
        crawler_user_agents: List[str] = None,
        extensions_to_ignore: List[str] = None,
        whitelist: List[str] = None,
        blacklist: List[str] = None,
        before_render: Callable[[Request], Awaitable[Optional[HTMLResponse]]] = None,
        after_render: Callable[[Request, HTMLResponse, bool], Awaitable[None]] = None,
    ):
        super().__init__(app)
        self.prerender_service_url = prerender_service_url
        self.prerender_service_username = prerender_service_username
        self.prerender_service_password = prerender_service_password
        self.prerender_service_token = prerender_service_token
        self.crawler_user_agents = (
            crawler_user_agents if crawler_user_agents else DEFAULT_CRAWLER_USER_AGENTS
        )
        self.extensions_to_ignore = (
            extensions_to_ignore
            if extensions_to_ignore
            else DEFAULT_EXTENSIONS_TO_IGNORE
        )

        if whitelist:
            self.whitelist = compile_patterns(whitelist)

        if blacklist:
            self.blacklist = compile_patterns(blacklist)

        self.before_render = before_render
        self.after_render = after_render

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if self._should_prerender(request):
            response = None
            cached = True

            if self.before_render:
                response = await self.before_render(request)

            if not response:
                response = await self._get_prerendered_response(request)
                cached = False

            if self.after_render:
                await self.after_render(request, response, cached)

            return response
        else:
            return await call_next(request)

    def _should_prerender(self, request: Request) -> bool:
        method = request.method
        user_agent = request.headers.get("user-agent")
        buffer_agent = request.headers.get("x-bufferbot")
        prerender_agent = request.headers.get("x-prerender")

        if method != "GET" or not user_agent or prerender_agent:
            return False

        if buffer_agent or is_matching_user_agent(user_agent, self.crawler_user_agents):
            request_path = request.url.path

            # Check ignored extensions
            for extension in self.extensions_to_ignore:
                if request_path.endswith(extension):
                    return False

            # Check whitelist
            if self.whitelist:
                whitelist_match = has_matching_pattern(self.whitelist, request_path)
                if not whitelist_match:
                    return False

            # Check blacklist
            if self.blacklist:
                blacklist_match = has_matching_pattern(self.blacklist, request_path)
                if blacklist_match:
                    return False

            return True

        return False

    async def _get_prerendered_response(self, request: Request) -> HTMLResponse:
        auth = None
        if self.prerender_service_username and self.prerender_service_password:
            auth = (self.prerender_service_username, self.prerender_service_password)

        headers = {}
        if self.prerender_service_token:
            headers["x-prerender-token"] = self.prerender_service_token

        async with httpx.AsyncClient(
            base_url=self.prerender_service_url, timeout=30, auth=auth, headers=headers
        ) as client:
            response = await client.get(f"/{request.url}")
        return HTMLResponse(response.text)
