# Testing with Nox and Docker

This project has migrated from tox to nox for a more flexible and powerful testing infrastructure, with all tests running in Docker containers for consistency.

## Quick Start

### Using the Docker wrapper script

The easiest way to run tests is using the provided Docker wrapper script:

```bash
# Run all default test sessions
./scripts/docker-test.sh test

# Run specific test session
./scripts/docker-test.sh test tests
./scripts/docker-test.sh test lint
./scripts/docker-test.sh test typecheck

# Open interactive shell
./scripts/docker-test.sh shell

# Build documentation
./scripts/docker-test.sh docs
```

### Using docker-compose directly

```bash
# Run all tests
docker-compose run --rm test-runner

# Run specific nox session
docker-compose run --rm test-runner nox -s tests
docker-compose run --rm test-runner nox -s lint

# Interactive development
docker-compose run --rm dev
```

## Test Environment

### Python Versions
Tests run against Python 3.9, 3.10, 3.11, and 3.12 in isolated Docker containers.

### Database
Tests now use SQLite instead of PostgreSQL:
- **In-memory SQLite**: Default for fast unit tests
- **File-based SQLite**: Available for persistence testing
- No external database service required

## Available Nox Sessions

### Core Testing Sessions

#### `tests` (Python 3.9-3.12)
Run the full test suite with pytest:
```bash
nox -s tests
nox -s tests-3.11  # Specific Python version
```

#### `lint` (Python 3.11)
Run flake8 linting with additional plugins:
```bash
nox -s lint
```

#### `format` (Python 3.11)
Format code with black and isort:
```bash
nox -s format
```

#### `typecheck` (Python 3.11)
Run mypy type checking:
```bash
nox -s typecheck
```

### Documentation and Reporting

#### `docs` (Python 3.11)
Build Sphinx documentation:
```bash
nox -s docs
nox -s docs -- serve  # Build and serve on port 8000
```

#### `coverage` (Python 3.11)
Generate coverage reports:
```bash
nox -s coverage
nox -s coverage -- open  # Open in browser
```

### Utility Sessions

#### `clean` (Python 3.11)
Clean up generated files:
```bash
nox -s clean
```

#### `dev` (Python 3.11)
Install package in development mode:
```bash
nox -s dev
```

#### `safety` (Python 3.9-3.12)
Check for security vulnerabilities:
```bash
nox -s safety
```

## Docker Architecture

### Dockerfile.test
Multi-stage Dockerfile that:
- Installs all Python versions (3.9-3.12) using pyenv
- Sets up nox and development dependencies
- Configures SSH for private Git dependencies

### docker-compose.yml Services
- **test-runner**: Main service for running nox
- **nox**: Flexible service for specific sessions
- **dev**: Interactive development shell
- **docs**: Documentation server

## Migration from Tox

### Key Differences
1. **Configuration**: Python file (`noxfile.py`) instead of INI format
2. **Database**: SQLite instead of PostgreSQL for tests
3. **Docker**: All tests run in containers
4. **Flexibility**: More powerful session management

### Equivalent Commands
| Tox Command | Nox Command |
|-------------|-------------|
| `tox` | `nox` |
| `tox -e py311` | `nox -s tests-3.11` |
| `tox -e flake8` | `nox -s lint` |
| `tox -e mypy` | `nox -s typecheck` |
| `tox -e docs` | `nox -s docs` |
| `tox -e clean` | `nox -s clean` |

## Test Fixtures

### SQLite Fixtures
The project now provides SQLite fixtures in `tests/conftest.py`:

```python
@pytest.fixture
def db_session():
    """In-memory SQLite database session."""
    # Fast, isolated database for each test

@pytest.fixture
def db_session_file(temp_db_file):
    """File-based SQLite database session."""
    # For testing persistence
```

## CI/CD Integration

GitHub Actions workflow uses Docker for consistent testing:
- Builds Docker image with caching
- Runs tests across all Python versions
- Generates coverage reports
- Builds documentation

## Troubleshooting

### Docker Build Issues
```bash
# Rebuild without cache
docker-compose build --no-cache test-runner
```

### Permission Issues
```bash
# Ensure SSH keys are accessible
chmod 600 ~/.ssh/id_rsa
```

### Clean Environment
```bash
# Remove all containers and volumes
./scripts/docker-test.sh clean
```
