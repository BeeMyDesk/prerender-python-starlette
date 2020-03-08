"""Starlette middleware for Prerender."""

__version__ = "1.0.0"


from prerender_python_starlette.middleware import (  # noqa: F401
    DEFAULT_CRAWLER_USER_AGENTS,
    DEFAULT_EXTENSIONS_TO_IGNORE,
    PrerenderMiddleware,
)
