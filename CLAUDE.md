# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Running Tests
```bash
# Using Docker wrapper script (recommended)
./scripts/docker-test.sh test        # Run all default sessions
./scripts/docker-test.sh test tests  # Run only pytest
./scripts/docker-test.sh test lint   # Run only linting
./scripts/docker-test.sh shell       # Interactive shell

# Using docker-compose directly
docker-compose run --rm test-runner                    # Run all tests
docker-compose run --rm test-runner nox -s tests      # Run pytest
docker-compose run --rm test-runner nox -s tests-3.11 # Specific Python version

# Local development (if nox installed)
nox              # Run default sessions
nox -s tests     # Run pytest across all Python versions
nox -s lint      # Run flake8 linting
nox -s typecheck # Run mypy
nox -s docs      # Build documentation

# Tests now use SQLite (no PostgreSQL required)
```

### Code Quality & Formatting
```bash
# Using Docker
docker-compose run --rm test-runner nox -s format    # Format with black & isort
docker-compose run --rm test-runner nox -s lint      # Lint with flake8
docker-compose run --rm test-runner nox -s typecheck # Type check with mypy

# Local development (if tools installed)
nox -s format    # Format code
nox -s lint      # Run linting
nox -s typecheck # Run type checking
```

### Documentation
```bash
# Using Docker
docker-compose run --rm test-runner nox -s docs         # Build docs
docker-compose up docs                                  # Build and serve docs

# Local development
nox -s docs         # Build documentation
nox -s docs -- serve # Build and serve on port 8000
```

### Installation
```bash
# Install package in development mode with all dependencies
pip install -e ".[dev]"
```

### Version Management
This project uses automated semantic versioning:
- Commit messages must follow [Conventional Commits](https://www.conventionalcommits.org/) format
- Use `fix:` for patches, `feat:` for minor versions, `feat!:` for major versions
- Production releases from `master` branch, beta releases from `staging` branch
- See `docs/semantic-versioning.md` for detailed guide

### Testing Infrastructure
- **Test Runner**: Nox (replaced tox) for flexible Python-based configuration
- **Database**: SQLite (in-memory) for fast, isolated tests - no PostgreSQL required
- **Containerization**: All tests run in Docker for consistency
- **Python Versions**: Tests run on Python 3.9, 3.10, 3.11, and 3.12
- **Documentation**: See `docs/testing-with-nox.md` for detailed testing guide

## Architecture Overview

This is a data product tracking system built to monitor and manage data products, their dependencies, and environments using PostgreSQL as the backend database.

### Core Components

1. **Database Layer** (`/src/data_product_tracker/models/`)
   - Uses SQLAlchemy 2.0+ with PostgreSQL
   - Key models: DataProducts, Environment, Invocation
   - Base model provides common fields and behaviors
   - Database connection managed via `conn.py` using session factory pattern

2. **Business Logic** (`/src/data_product_tracker/core/` and `/src/data_product_tracker/io/`)
   - `trackers.py` contains main tracking functionality
   - `contracts.py` implements data validation using the `deal` library for design-by-contract
   - `reflection.py` provides database introspection capabilities

3. **CLI Interface** (`/src/data_product_tracker/cli.py`)
   - Built with Click framework
   - Currently a template - main functionality not yet implemented

4. **Configuration Management**
   - Uses external `configurables` package from MIT's internal Git
   - `variables.py` handles configuration variables
   - Database connection strings managed through configuration

### Key Design Patterns

1. **Session Management**: Uses SQLAlchemy's scoped session pattern with a global Session factory configured in `conn.py`

2. **Contract-Based Design**: Employs the `deal` library for runtime contract verification, ensuring data integrity and proper error handling

3. **Testing Strategy**:
   - Uses real PostgreSQL instances via `pytest-postgresql`
   - Property-based testing with `hypothesis`
   - Fixtures defined in `tests/conftest.py` provide database sessions

4. **Code Quality**: Enforced through:
   - Type hints checked by mypy with SQLAlchemy plugin
   - Black formatter with 80-character line limit
   - isort for import organization
   - flake8 for linting with 81-character limit

### External Dependencies

- **Private Git Dependency**: `configurables` package from `tessgit.mit.edu`
  - Required for configuration management
  - Accessed via SSH authentication

### Database Migrations

- Alembic configuration template exists (`alembic.ini.conf`) but is not actively configured
- Database schema is currently managed through SQLAlchemy's `create_all` method
