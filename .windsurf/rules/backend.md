---
trigger: model_decision
description:  rules and best practices for Python development within the PixCrawler project, ensuring code consistency and quality.
---

# Python Development Guidelines

This document outlines the best practices and conventions for Python development in the PixCrawler project.

## 1. Code Style

- **PEP 8**: All Python code must adhere to the [PEP 8 style guide](https://www.python.org/dev/peps/pep-0008/).
- **Typing**: All functions and methods must have type hints as per [PEP 484](https://www.python.org/dev/peps/pep-0484/). Use modern type hinting syntax (e.g., `list[int]` instead of `typing.List[int]`).
- **Docstrings**: Use [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#3.8-comments-and-docstrings) for all public modules, classes, functions, and methods.
- **Imports**: Imports should be grouped in the following order: standard library, third-party libraries, and local application imports. Use absolute imports.
- **Linting**: Use `Ruff` for linting and formatting. The configuration is in [pyproject.toml](cci:7://file:///f:/Projects/Languages/Python/WorkingOnIt/PixCrawler/pyproject.toml:0:0-0:0).

## 2. Dependency Management

- **Poetry**: Use [Poetry](https://python-poetry.org/) for dependency management.
- **Adding Dependencies**: Add new dependencies using `poetry add <package>`.
- **Updating Dependencies**: Keep dependencies up to date by running `poetry update` periodically.
- **Lock File**: Always commit the `poetry.lock` file to ensure reproducible builds.

## 3. Testing

- **Framework**: Use `pytest` for writing and running tests.
- **Test Location**: Tests for the `builder` package should be in the `tests/` directory.
- **Coverage**: Aim for a high test coverage. All new features should have corresponding tests.
- **Mocks**: Use `pytest-mock` for mocking objects and dependencies.

## 4. General Practices

- **Configuration**: Store configuration in [pyproject.toml](cci:7://file:///f:/Projects/Languages/Python/WorkingOnIt/PixCrawler/pyproject.toml:0:0-0:0) or dedicated configuration files, not in code.
- **Logging**: Use the `logging` module for logging. Configure it via `logging_config/`.
- **Error Handling**: Catch specific exceptions. Avoid bare `except:` clauses.