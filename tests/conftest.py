"""Establish test-wide fixtures for `data_product_tracker` package."""

import pathlib
import tempfile
import uuid
from typing import Generator, Optional
from unittest import mock

import deal
import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session as SessionType

from data_product_tracker.conn import session_factory
from data_product_tracker.models.base import Base

from .database_configs import (
    DatabaseConfig,
    get_database_config,
    get_test_databases,
    is_database_available,
)

deal.enable()


@pytest.fixture(autouse=True)
def mock_global_session():
    """Mock the global Session to prevent configuration conflicts.

    This prevents the production code from trying to configure a global
    session that would conflict with our test sessions.
    """
    with mock.patch(
        "data_product_tracker.conn.session_factory"
    ) as mock_session:
        # Create a dummy sessionmaker that doesn't interfere with tests
        mock_session.return_value = mock.MagicMock()
        yield mock_session


@pytest.fixture
def db_session() -> Generator[SessionType, None, None]:
    """Create a SQLite in-memory database session for testing.

    This replaces the PostgreSQL fixture with a lightweight SQLite
    in-memory database that's faster and doesn't require external services.
    Each test gets its own isolated database and session.
    """
    # Create in-memory SQLite database with unique connection
    engine = sa.create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=sa.pool.StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine, checkfirst=True)

    session_factory.configure(bind=engine)
    # Create a session
    sess = session_factory()

    try:
        yield sess
    finally:
        sess.close()
        # Clean up
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def temp_db_file(worker_id) -> Generator[pathlib.Path, None, None]:
    """Create a temporary SQLite database file for file-based testing.

    Uses worker_id from pytest-xdist to ensure unique files per test worker.
    """
    # Create unique filename using worker_id and UUID
    unique_id = f"{worker_id}_{uuid.uuid4().hex}"
    with tempfile.NamedTemporaryFile(
        suffix=f"_{unique_id}.db",
    ) as tmp:
        db_path = pathlib.Path(tmp.name)
        yield db_path


@pytest.fixture
def db_session_file(
    temp_db_file: pathlib.Path,
) -> Generator[SessionType, None, None]:
    """Create a SQLite file-based database session for testing.

    Use this fixture when you need to test database persistence
    or file-based operations. Each test gets its own isolated database file.
    """
    # Create file-based SQLite database with proper isolation
    engine = sa.create_engine(
        f"sqlite:///{temp_db_file}",
        connect_args={"check_same_thread": False},
        # Use exclusive locking mode for file-based SQLite in tests
        pool_pre_ping=True,
        echo=False,
    )

    # Set WAL mode for better concurrency
    with engine.connect() as conn:
        conn.execute(sa.text("PRAGMA journal_mode=WAL"))
        conn.commit()

    # Create all tables
    Base.metadata.create_all(bind=engine, checkfirst=True)

    session_factory.configure(bind=engine)

    # Create a session
    with session_factory() as sess:
        try:
            yield sess
        finally:
            # Clean up
            Base.metadata.drop_all(bind=engine)
            engine.dispose()


@pytest.fixture(scope="session")
def worker_id(request):
    """Get the pytest-xdist worker id, or 'master' if not using xdist."""
    return (
        request.config.workerinput.get("workerid", "master")
        if hasattr(request.config, "workerinput")
        else "master"
    )


def ensure_directory(path: pathlib.Path) -> pathlib.Path:
    """Ensure that the parent directory of a path exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


# Multi-database testing fixtures


def pytest_addoption(parser):
    """Add command-line options for database testing."""
    parser.addoption(
        "--database",
        action="append",
        default=[],
        help="Specify databases to test against (can be used multiple times)",
    )
    parser.addoption(
        "--all-databases",
        action="store_true",
        default=False,
        help="Run tests against all configured databases",
    )


def pytest_generate_tests(metafunc):
    """Generate test instances for each requested database."""
    if "database_type" in metafunc.fixturenames:
        # Get requested databases from command line or environment
        db_options = metafunc.config.getoption("database")
        all_dbs = metafunc.config.getoption("all_databases")

        if all_dbs:
            test_dbs = get_test_databases()
        elif db_options:
            test_dbs = {db: get_database_config(db) for db in db_options}
        else:
            # Default to SQLite for fast testing
            test_dbs = {"sqlite-memory": get_database_config("sqlite-memory")}

        # Filter out unavailable databases
        available_dbs = {
            k: v for k, v in test_dbs.items() if is_database_available(v)
        }

        if not available_dbs:
            available_dbs = {
                "sqlite-memory": get_database_config("sqlite-memory")
            }

        metafunc.parametrize(
            "database_type",
            list(available_dbs.keys()),
            ids=[v.name for v in available_dbs.values()],
        )


@pytest.fixture
def database_config(database_type: str) -> DatabaseConfig:
    """Get database configuration for the current test."""
    return get_database_config(database_type)


@pytest.fixture
def multi_db_engine(
    database_config: DatabaseConfig,
    temp_db_file: Optional[pathlib.Path] = None,
) -> Generator[sa.Engine, None, None]:
    """Create a database engine based on configuration.

    This fixture creates engines for different database types,
    handling SQLite file paths appropriately.
    """
    url = database_config.url

    # Handle SQLite file databases
    if (
        database_config.dialect == "sqlite"
        and url.startswith("sqlite:///")
        and url != "sqlite:///:memory:"
    ):
        if temp_db_file:
            url = f"sqlite:///{temp_db_file}"
        else:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(
                suffix=".db", delete=False
            ) as tmp:
                url = f"sqlite:///{tmp.name}"

    # Create engine with appropriate settings
    if database_config.dialect == "sqlite":
        engine = sa.create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=(
                sa.pool.StaticPool if url == "sqlite:///:memory:" else None
            ),
            pool_pre_ping=True,
        )
        # Set SQLite pragmas for better performance in tests
        if url != "sqlite:///:memory:":
            with engine.connect() as conn:
                conn.execute(sa.text("PRAGMA journal_mode=WAL"))
                conn.execute(sa.text("PRAGMA synchronous=NORMAL"))
                conn.commit()
    else:
        # PostgreSQL, MySQL, etc.
        engine = sa.create_engine(
            url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )

    # Create all tables
    Base.metadata.create_all(bind=engine, checkfirst=True)

    try:
        yield engine
    finally:
        # Clean up
        Base.metadata.drop_all(bind=engine)
        engine.dispose()

        # Clean up temporary SQLite files
        if (
            database_config.dialect == "sqlite"
            and url.startswith("sqlite:///")
            and url != "sqlite:///:memory:"
        ):
            try:
                pathlib.Path(url.replace("sqlite:///", "")).unlink(
                    missing_ok=True
                )
            except Exception:
                pass


@pytest.fixture
def multi_db_session(
    multi_db_engine: sa.Engine,
) -> Generator[SessionType, None, None]:
    """Create a database session for multi-database testing.

    This fixture provides sessions that work with any configured database type.
    """
    session_factory.configure(bind=multi_db_engine)
    session = session_factory()

    try:
        yield session
    finally:
        session.close()


# Markers for database-specific tests
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "postgres: mark test to run only on PostgreSQL"
    )
    config.addinivalue_line(
        "markers", "sqlite: mark test to run only on SQLite"
    )
    config.addinivalue_line(
        "markers", "mysql: mark test to run only on MySQL/MariaDB"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow on certain databases"
    )
    config.addinivalue_line(
        "markers", "all_databases: explicitly run on all database types"
    )
