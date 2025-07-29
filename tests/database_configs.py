"""Database configuration for multi-database testing."""

import os
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class DatabaseConfig:
    """Configuration for a test database."""

    name: str
    url: str
    docker_service: Optional[str] = None
    requires_service: bool = False
    dialect: str = "sqlite"


# Database configurations
DATABASES: Dict[str, DatabaseConfig] = {
    # SQLite databases (no external service required)
    "sqlite-memory": DatabaseConfig(
        name="SQLite In-Memory",
        url="sqlite:///:memory:",
        dialect="sqlite",
    ),
    "sqlite-file": DatabaseConfig(
        name="SQLite File",
        url="sqlite:///test.db",
        dialect="sqlite",
    ),
    # PostgreSQL databases
    "postgres-16": DatabaseConfig(
        name="PostgreSQL 16",
        url="postgresql+psycopg://testuser:testpass@localhost:5433/testdb",
        docker_service="postgres-16",
        requires_service=True,
        dialect="postgresql",
    ),
    "postgres-16-docker": DatabaseConfig(
        name="PostgreSQL 16 (Docker Network)",
        url="postgresql+psycopg://testuser:testpass@postgres-16:5432/testdb",
        docker_service="postgres-16",
        requires_service=True,
        dialect="postgresql",
    ),
    "postgres-14": DatabaseConfig(
        name="PostgreSQL 14",
        url="postgresql+psycopg://testuser:testpass@localhost:5434/testdb",
        docker_service="postgres-14",
        requires_service=True,
        dialect="postgresql",
    ),
    # MySQL databases (if support is added)
    "mysql-8": DatabaseConfig(
        name="MySQL 8",
        url="mysql+pymysql://testuser:testpass@localhost:3307/testdb",
        docker_service="mysql-8",
        requires_service=True,
        dialect="mysql",
    ),
    "mariadb-11": DatabaseConfig(
        name="MariaDB 11",
        url="mysql+pymysql://testuser:testpass@localhost:3308/testdb",
        docker_service="mariadb-11",
        requires_service=True,
        dialect="mysql",
    ),
}


def get_database_config(db_type: str) -> DatabaseConfig:
    """Get database configuration by type.

    Parameters
    ----------
    db_type : str
        The database type identifier.

    Returns
    -------
    DatabaseConfig
        The database configuration.

    Raises
    ------
    ValueError
        If the database type is not found.
    """
    if db_type not in DATABASES:
        raise ValueError(
            f"Unknown database type: {db_type}. "
            f"Available: {', '.join(DATABASES.keys())}"
        )
    return DATABASES[db_type]


def get_test_databases() -> Dict[str, DatabaseConfig]:
    """Get databases to test based on environment variables.

    Returns databases based on TEST_DATABASES environment variable.
    If not set, returns only SQLite databases.
    If set to 'all', returns all databases.
    Otherwise, returns comma-separated list of database types.
    """
    test_dbs = os.environ.get("TEST_DATABASES", "sqlite").lower()

    if test_dbs == "all":
        return DATABASES
    elif test_dbs == "sqlite":
        return {k: v for k, v in DATABASES.items() if v.dialect == "sqlite"}
    elif test_dbs == "postgres":
        return {
            k: v for k, v in DATABASES.items() if v.dialect == "postgresql"
        }
    else:
        # Parse comma-separated list
        requested = {s.strip() for s in test_dbs.split(",")}
        return {k: v for k, v in DATABASES.items() if k in requested}


def is_database_available(config: DatabaseConfig) -> bool:
    """Check if a database service is available.

    For SQLite, always returns True.
    For other databases, attempts to connect and returns result.
    """
    if not config.requires_service:
        return True

    # For Docker-based services, we could add actual connectivity checks
    # For now, we'll assume they're available if we're in CI or docker
    return (
        os.environ.get("CI") == "true"
        or os.environ.get("IN_DOCKER") == "true"
        or os.environ.get("FORCE_DATABASE_TESTS") == "true"
    )
