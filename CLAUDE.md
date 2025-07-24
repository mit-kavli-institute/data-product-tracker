# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Running Tests
```bash
# Run all tests with coverage
pytest --cov --cov-report=term-missing

# Run tests using tox (includes mypy, flake8, and tests)
tox

# Run specific test environments
tox -e py311  # Run tests for Python 3.11
tox -e mypy   # Run mypy type checking
tox -e flake8 # Run flake8 linting

# Run a single test file
pytest tests/test_specific.py

# Run tests with PostgreSQL database (via tox-docker)
tox  # This automatically starts a PostgreSQL container
```

### Code Quality & Formatting
```bash
# Format code with black
black data_product_tracker tests

# Sort imports
isort data_product_tracker tests

# Type checking
mypy data_product_tracker

# Linting
flake8 data_product_tracker tests
```

### Documentation
```bash
# Build HTML documentation
tox -e docs

# Build docs manually
sphinx-build -M html docs/source docs/build
```

### Installation
```bash
# Install package in development mode with all dependencies
pip install -e ".[dev]"
```

## Architecture Overview

This is a data product tracking system built to monitor and manage data products, their dependencies, and environments using PostgreSQL as the backend database.

### Core Components

1. **Database Layer** (`/data_product_tracker/models/`)
   - Uses SQLAlchemy 2.0+ with PostgreSQL
   - Key models: DataProducts, Environment, Invocation
   - Base model provides common fields and behaviors
   - Database connection managed via `conn.py` using session factory pattern

2. **Business Logic** (`/data_product_tracker/core/` and `/data_product_tracker/io/`)
   - `trackers.py` contains main tracking functionality
   - `contracts.py` implements data validation using the `deal` library for design-by-contract
   - `reflection.py` provides database introspection capabilities

3. **CLI Interface** (`/data_product_tracker/cli.py`)
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
