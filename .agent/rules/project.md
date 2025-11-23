---
trigger: model_decision
description: This file defines the project-wide conventions for version control, commit messages, and the monorepo structure, ensuring a smooth and consistent development workflow for all contributors.
---

# Project-Wide Guidelines

This document outlines the conventions and best practices for the PixCrawler monorepo.

## 1. Version Control

- **Branching Strategy**:
    - `main`: The main branch, which should always be stable and deployable.
    - `develop`: The development branch, where new features are integrated.
    - `feature/<feature-name>`: Branches for developing new features.
    - `fix/<issue-name>`: Branches for bug fixes.
- **Pull Requests**: All changes must be submitted through a pull request (PR). PRs must be reviewed and approved by at least one other team member before merging.
- **Code Reviews**: Code reviews should be constructive and focus on code quality, correctness, and adherence to project guidelines.

## 2. Commit Messages

- **Semantic Commits**: Use [semantic commit messages](https://www.conventionalcommits.org/en/v1.0.0/) to ensure a clear and descriptive commit history.
- **Format**: `<type>(<scope>): <subject>`
    - **type**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
    - **scope**: The part of the project affected (e.g., `backend`, `frontend`, `builder`).
    - **subject**: A concise description of the change.

## 3. Monorepo Structure

- **`backend/`**: The Python backend application.
- **`frontend/`**: The Next.js frontend application.
- **`builder/`**: The Python web crawler and data processing engine.
- **`logging_config/`**: Shared logging configuration.
- **`tests/`**: Tests for the Python packages.
- **`.windsurf/`**: Contains workspace rules and other development-related configurations.

## 4. Working in the Monorepo

- **Dependencies**: Each package (`backend`, `frontend`, `builder`) manages its own dependencies.
- **Shared Code**: There is currently no shared code between the `frontend` and `backend`. If this changes, a `packages/shared` directory should be created.
- **Environment Variables**: Do not commit [.env](cci:7://file:///f:/Projects/Languages/Python/WorkingOnIt/PixCrawler/frontend/.env:0:0-0:0) files. Instead, use `.env.example` files to provide a template for required environment variables.