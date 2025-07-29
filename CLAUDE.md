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

# Using docker compose directly (Note: use 'docker-compose' for older Docker versions)
docker compose run --rm test-runner                    # Run all tests
docker compose run --rm test-runner nox -s tests      # Run pytest
docker compose run --rm test-runner nox -s tests-3.11 # Specific Python version

# Local development (if nox installed)
nox              # Run default sessions
nox -s tests     # Run pytest across all Python versions
nox -s lint      # Run flake8 linting
nox -s typecheck # Run mypy
nox -s docs      # Build documentation

# Notes:
# - Tests default to SQLite (no external services required)
# - Multi-database testing available (PostgreSQL, MySQL)
# - Docker image based on thekevjames/nox with all Python versions pre-installed

# Multi-database testing
./scripts/start-test-databases.sh            # Start database services
./scripts/docker-test.sh test tests-postgres # Test with PostgreSQL
./scripts/docker-test.sh test tests-all-databases # Test all databases
```

### Code Quality & Formatting
```bash
# Using Docker
docker compose run --rm test-runner nox -s format    # Format with black & isort
docker compose run --rm test-runner nox -s lint      # Lint with flake8
docker compose run --rm test-runner nox -s typecheck # Type check with mypy

# Local development (if tools installed)
nox -s format    # Format code
nox -s lint      # Run linting
nox -s typecheck # Run type checking
```

### Documentation
```bash
# Using Docker
docker compose run --rm test-runner nox -s docs         # Build docs
docker compose up docs                                  # Build and serve docs

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
- **Database Support**:
  - SQLite (default) for fast, isolated tests - no external services required
  - PostgreSQL 16 & 14 for production-like testing
  - MySQL 8 & MariaDB 11 (optional, for compatibility testing)
  - Multi-database testing via parameterized fixtures
- **Containerization**: All tests run in Docker using the `thekevjames/nox` image
  - Simplified Dockerfile.test uses pre-built nox image with all Python versions
  - Database services defined in docker-compose.yml
  - No need for complex multi-stage builds or pyenv setup
- **Python Versions**: Tests run on Python 3.9, 3.10, 3.11, and 3.12
- **Documentation**:
  - See `docs/testing-with-nox.md` for general testing guide
  - See `docs/testing-multi-db.md` for multi-database testing guide

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
   - Default tests use SQLite for speed and simplicity
   - Multi-database testing available with PostgreSQL and MySQL via Docker
   - Property-based testing with `hypothesis`
   - Parameterized fixtures in `tests/conftest.py` provide database sessions
   - Database type can be selected via command line options

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
