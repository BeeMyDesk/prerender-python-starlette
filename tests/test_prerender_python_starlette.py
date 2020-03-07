from prerender_python_starlette import (
    PrerenderMiddleware,
    DEFAULT_CRAWLER_USER_AGENTS,
    DEFAULT_EXTENSIONS_TO_IGNORE,
)


def test_default_imports():
    assert PrerenderMiddleware is not None
    assert type(DEFAULT_CRAWLER_USER_AGENTS) == list
    assert type(DEFAULT_EXTENSIONS_TO_IGNORE) == list
