# Multi-Database Testing Guide

This guide explains how to run tests against multiple database types in the Data Product Tracker project.

## Overview

The testing infrastructure supports running tests against:
- SQLite (in-memory and file-based) - default for fast local testing
- PostgreSQL 16 and 14
- MySQL 8
- MariaDB 11

## Quick Start

### Running Tests with SQLite (Default)

```bash
# Run all tests with SQLite (fast, no setup required)
./scripts/docker-test.sh test tests

# Or run specific test files
./scripts/docker-test.sh test tests -- tests/test_reflection.py
```

### Running Tests with PostgreSQL

```bash
# Start PostgreSQL services
./scripts/start-test-databases.sh

# Run tests against PostgreSQL
./scripts/docker-test.sh test tests-postgres

# Run specific tests against PostgreSQL 16 only
docker compose run --rm test-runner pytest --database=postgres-16 tests/
```

### Running Tests with All Databases

```bash
# Start all database services
./scripts/start-test-databases.sh

# Run tests against all databases
./scripts/docker-test.sh test tests-all-databases

# Stop database services when done
docker compose down
```

## Test Fixtures

### Multi-Database Fixtures

The test suite provides parameterized fixtures that work with any database:

- `database_type`: Parameter that specifies which database to use
- `database_config`: Configuration for the current database
- `multi_db_engine`: SQLAlchemy engine for the current database
- `multi_db_session`: Database session for the current database

Example usage:

```python
def test_with_multi_db(multi_db_session, database_config):
    """This test runs once for each configured database."""
    print(f"Testing with {database_config.name}")
    # Your test code here
```

### Original Fixtures (Backward Compatible)

The original fixtures still work and default to SQLite:
- `db_session`: SQLite in-memory session
- `db_session_file`: SQLite file-based session

## Database Markers

Use pytest markers to control which databases run specific tests:

```python
@pytest.mark.postgres
def test_postgres_only(multi_db_session):
    """This test only runs on PostgreSQL."""
    pass

@pytest.mark.sqlite
def test_sqlite_only(db_session):
    """This test only runs on SQLite."""
    pass

@pytest.mark.slow
def test_slow_on_some_dbs(multi_db_session):
    """Mark tests that might be slow on certain databases."""
    pass
```

## Command Line Options

### pytest options:
- `--database=<type>`: Test against specific database (can be used multiple times)
- `--all-databases`: Test against all configured databases

### Environment Variables:
- `TEST_DATABASES`: Set to `all`, `sqlite`, `postgres`, or comma-separated list
- `IN_DOCKER`: Set to `true` when running in Docker
- `FORCE_DATABASE_TESTS`: Set to `true` to force database tests even if services aren't detected

## Database Services

The `docker-compose.yml` defines the following services:

| Service | Database | Port | Username | Password | Database |
|---------|----------|------|----------|----------|----------|
| postgres-16 | PostgreSQL 16 | 5433 | testuser | testpass | testdb |
| postgres-14 | PostgreSQL 14 | 5434 | testuser | testpass | testdb |
| mysql-8 | MySQL 8 | 3307 | testuser | testpass | testdb |
| mariadb-11 | MariaDB 11 | 3308 | testuser | testpass | testdb |

## Writing Multi-Database Tests

### Best Practices

1. **Use multi_db_session for new tests**: This ensures tests work across all databases.

2. **Handle database differences**: Some features work differently across databases:
   ```python
   def test_with_db_differences(multi_db_session, database_config):
       if database_config.dialect == "postgresql":
           # PostgreSQL-specific code
       elif database_config.dialect == "mysql":
           # MySQL-specific code
       else:
           # SQLite code
   ```

3. **Use markers appropriately**: Mark database-specific tests to avoid failures.

4. **Test isolation**: Each test gets a fresh database/schema to ensure isolation.

## Troubleshooting

### Database services won't start
```bash
# Check if ports are already in use
lsof -i :5433  # PostgreSQL 16
lsof -i :3307  # MySQL 8

# View logs
docker compose logs postgres-16
docker compose logs mysql-8
```

### Tests fail with connection errors
```bash
# Ensure services are healthy
docker compose ps

# Restart services
docker compose restart postgres-16
```

### Slow test performance
- Use SQLite for rapid development cycles
- Run multi-database tests in CI or before merging
- Use the `@pytest.mark.slow` marker for expensive tests

## CI/CD Integration

In GitHub Actions or other CI systems:

```yaml
# Start database services
- name: Start databases
  run: docker compose up -d postgres-16 postgres-14 mysql-8 mariadb-11

# Wait for services
- name: Wait for databases
  run: ./scripts/start-test-databases.sh

# Run tests
- name: Test PostgreSQL
  run: docker compose run --rm test-runner nox -s tests-postgres
  env:
    CI: true
```

## Adding New Database Types

To add support for a new database:

1. Add service to `docker-compose.yml`
2. Add configuration to `tests/database_configs.py`
3. Update nox sessions if needed
4. Add appropriate markers in `pyproject.toml`
5. Document any database-specific considerations

## Performance Considerations

- **tmpfs**: Database services use tmpfs for data directories (faster, but data is lost on restart)
- **Connection pooling**: Configured appropriately for each database type
- **Parallel testing**: SQLite tests can run in parallel with proper isolation
- **Resource limits**: Database services have resource constraints to prevent excessive memory usage
