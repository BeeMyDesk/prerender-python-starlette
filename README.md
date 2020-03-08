# Prerender Python Starlette

<p align="center">
    <em>Starlette middleware for Prerender</em>
</p>

[![build](https://github.com/BeeMyDesk/prerender-python-starlette/workflows/Build/badge.svg)](https://github.com/BeeMyDesk/prerender-python-starlette/actions)
[![codecov](https://codecov.io/gh/BeeMyDesk/prerender-python-starlette/branch/master/graph/badge.svg)](https://codecov.io/gh/BeeMyDesk/prerender-python-starlette)
[![Dependabot Status](https://api.dependabot.com/badges/status?host=github&repo=BeeMyDesk/prerender-python-starlette)](https://dependabot.com)
[![PyPI version](https://badge.fury.io/py/prerender-python-starlette.svg)](https://badge.fury.io/py/prerender-python-starlette)

---

**Documentation**: <a href="https://BeeMyDesk.github.io/prerender-python-starlette/" target="_blank">https://BeeMyDesk.github.io/prerender-python-starlette/</a>

**Source Code**: <a href="https://github.com/BeeMyDesk/prerender-python-starlette" target="_blank">https://github.com/BeeMyDesk/prerender-python-starlette</a>

---

## Introduction

> Google, Facebook, Twitter, and Bing are constantly trying to view your website... but Google is the only crawler that executes a meaningful amount of JavaScript and Google even admits that they can execute JavaScript weeks after actually crawling. Prerender allows you to serve the full HTML of your website back to Google and other crawlers so that they don't have to execute any JavaScript. [Google recommends using Prerender.io](https://developers.google.com/search/docs/guides/dynamic-rendering) to prevent indexation issues on sites with large amounts of JavaScript.
>
> Prerender is perfect for Angular SEO, React SEO, Vue SEO, and any other JavaScript framework.
>
> This middleware intercepts requests to your Node.js website from crawlers, and then makes a call to the (external) Prerender Service to get the static HTML instead of the JavaScript for that page. That HTML is then returned to the crawler.

*README of [prerender_rails](https://github.com/prerender/prerender_rails)*

This library is a Python implementation of a Prerender middleware for [Starlette](https://www.starlette.io). It should work flawlessly with [FastAPI](https://fastapi.tiangolo.com/) and, probably, with any ASGI framework.

## Installation

```bash
pip install prerender-python-starlette
```

## Usage

```py
from starlette.applications import Starlette
from starlette.middleware import Middleware
from prerender_python_starlette import PrerenderMiddleware

routes = ...

middleware = [
  Middleware(PrerenderMiddleware),
]

app = Starlette(routes=routes, middleware=middleware)
```

### Parameters

* `prerender_service_url`: URL of Prerender server. Defaults to `PRERENDER_SERVICE_URL` environment variable.
* `prerender_service_username`: HTTP basic auth username of Prerender server. Defaults to `PRERENDER_SERVICE_USERNAME` environment variable.
* `prerender_service_password`: HTTP basic auth password of Prerender server. Defaults to `PRERENDER_SERVICE_PASSWORD` environment variable.
* `prerender_service_token`: Token set in `X-Prerender-Token` header. Defaults to `PRERENDER_SERVICE_TOKEN` environment variable.
* `crawler_user_agents`: List of crawler user agents to intercept. Defaults to `DEFAULT_CRAWLER_USER_AGENTS` list.
* `extensions_to_ignore`: List of file extensions to ignore. Defaults to `DEFAULT_EXTENSIONS_TO_IGNORE` list.
* `whitelist`: List of path patterns to whitelist. Path not matching a pattern in the list won't be prerendered. Defaults to `None`.
* `blacklist`: List of path patterns to blacklist. Path matching a pattern in the list won't be prerendered. Defaults to `None`.
* `before_render`: Async function called before the prerendering. If it returns an `HTMLResponse`, it will be considered as cache and will bypass the call to the Prerender server. Defaults to `None`.
* `after_render`: Async function called after the prerendering. Defaults to `None`.

### Cache example

```py
from starlette.applications import Starlette
from starlette.middleware import Middleware
from prerender_python_starlette import PrerenderMiddleware


async def before_render(request: Request) -> Optional[HTMLResponse]:
    cached_response = await cache.get(f"prerender:{request.url.path}")
    if cached_response:
        return HTMLResponse(cached_response)
    return None


async def after_render(
    request: Request, response: HTMLResponse, cached: bool
) -> None:
    if not cached:
        await cache.set(
            f"prerender:{request.url.path}", response.body.decode(response.charset)
        )


routes = ...

middleware = [
  Middleware(PrerenderMiddleware, before_render=before_render, after_render=after_render),
]

app = Starlette(routes=routes, middleware=middleware)
```

## Development

### Setup environement

You should have [Pipenv](https://pipenv.readthedocs.io/en/latest/) installed. Then, you can install the dependencies with:

```bash
pipenv install --dev
```

After that, activate the virtual environment:

```bash
pipenv shell
```

### Run unit tests

You can run all the tests with:

```bash
make test
```

Alternatively, you can run `pytest` yourself:

```bash
pytest
```

### Format the code

Execute the following command to apply `isort` and `black` formatting:

```bash
make format
```

## License

This project is licensed under the terms of the MIT license.
