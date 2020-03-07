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
