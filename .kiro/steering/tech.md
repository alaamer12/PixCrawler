# PixCrawler Technology Stack

## Build System & Package Management
- **Python**: UV package manager with workspace configuration
- **Frontend**: Bun/PNPM for Node.js dependencies
- **Build Backend**: Hatchling for Python package building

## Backend Stack
- **Language**: Python 3.11+ (supports 3.11, 3.12, 3.13)
- **Package Manager**: UV with workspace support
- **Logging**: Loguru-based centralized logging system
- **Image Processing**: PIL (Pillow) for image validation and manipulation
- **Web Crawling**: icrawler with multiple engine support (Google, Bing, Baidu, DuckDuckGo)
- **Data Validation**: jsonschema for configuration validation

## Frontend Stack
- **Framework**: Next.js 15.4.0 (canary) with React 19.1.0
- **Runtime**: Node.js with TypeScript 5.8.3
- **Database**: Drizzle ORM with PostgreSQL
- **Authentication**: Supabase Auth with SSR support
- **Styling**: Tailwind CSS 4.1.7 with PostCSS
- **UI Components**: Lucide React icons, class-variance-authority for component variants
- **Validation**: Zod for schema validation

## Development Tools
- **Linting**: Ruff (primary linter and formatter)
- **Type Checking**: MyPy with strict configuration
- **Testing**: Pytest with coverage reporting
- **Pre-commit**: Configured hooks for code quality

## Common Commands

### Backend Development
```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Lint and format
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy .
```

### Frontend Development
```bash
# Development server
npm run dev
# or
bun dev

# Build for production
npm run build

# Database operations
npm run db:generate    # Generate migrations
npm run db:migrate     # Run migrations
npm run db:studio      # Open Drizzle Studio
npm run db:seed        # Seed database
```

### Project Management
```bash
# Install all workspace dependencies
uv sync --all-extras

# Build all packages
uv build

# Run tests across workspace
uv run pytest tests/
```

## Code Quality Standards
- **Line Length**: 88 characters (Black/Ruff standard)
- **Python Version**: Minimum 3.11, target 3.11
- **Import Sorting**: isort configuration with first-party packages
- **Type Hints**: Required for all function definitions (MyPy strict mode)
- **Documentation**: Comprehensive docstrings for all public APIs