# PixCrawler Project Structure

## Repository Organization
This is a monorepo using UV workspace configuration with multiple Python packages and a Next.js frontend.

## Root Level Structure
```
pixcrawler/
├── .kiro/                    # Kiro AI assistant configuration
├── backend/                  # Backend API package
├── builder/                  # Core image dataset generation engine
├── frontend/                 # Next.js web application
├── logging_config/           # Centralized logging package (pixcrawler-logging)
├── src/                      # Main package source (currently minimal)
├── tests/                    # Cross-package integration tests
├── pyproject.toml           # Root workspace configuration
└── uv.lock                  # UV lockfile for reproducible builds
```

## Package Structure

### Backend Package (`backend/`)
- **Purpose**: API server and business logic
- **Type**: Python package using Hatchling
- **Current State**: Minimal implementation (README only)

### Builder Package (`builder/`)
- **Purpose**: Core image crawling and dataset generation engine
- **Key Modules**:
  - `_generator.py`: Main dataset generation orchestration
  - `_config.py`: Configuration management and validation
  - `_downloader.py`: Multi-engine image downloading
  - `_utilities.py`: Helper functions and utilities
  - `_constants.py`: Application constants
  - `_exceptions.py`: Custom exception classes

### Frontend Package (`frontend/`)
- **Purpose**: Next.js web application with Supabase integration
- **Structure**:
  - `app/`: Next.js 13+ app router structure
  - `lib/`: Shared utilities and database configuration
  - `node_modules/`: NPM dependencies
  - Database configuration with Drizzle ORM

### Logging Config Package (`logging_config/`)
- **Purpose**: Centralized logging system using Loguru
- **Package Name**: `pixcrawler-logging`
- **Scope**: Shared across all workspace packages

## Naming Conventions

### Python Packages
- **Module Names**: Snake_case with descriptive prefixes (`_generator.py`, `_config.py`)
- **Private Modules**: Prefix with underscore for internal implementation
- **Package Names**: Lowercase with hyphens (`pixcrawler-logging`)

### File Organization
- **Configuration Files**: Root level for workspace-wide settings
- **Package-Specific**: Each package maintains its own `pyproject.toml`
- **Tests**: Centralized in `/tests` for integration, package-level for unit tests

## Workspace Dependencies
The root `pyproject.toml` defines workspace members and manages inter-package dependencies:
- `backend` → workspace dependency
- `builder` → workspace dependency  
- `pixcrawler-logging` → workspace dependency

## Development Workflow
1. **Root Level**: Workspace management, cross-package operations
2. **Package Level**: Individual package development and testing
3. **Frontend**: Independent Next.js development with database integration

## Import Patterns
- **Internal Imports**: Use relative imports within packages
- **Cross-Package**: Import via workspace dependency names
- **First-Party Packages**: Configured in Ruff as `["pixcrawler-backend", "pixcrawler-builder", "pixcrawler-logging", "pixcrawler-celery-core", "pixcrawler-validator"]`

## Configuration Management
- **Root**: Workspace-wide linting, formatting, and build configuration
- **Package**: Individual package metadata and dependencies
- **Frontend**: Separate Node.js ecosystem with TypeScript configuration