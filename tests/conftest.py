"""Establish test-wide fixtures for `data_product_tracker` package"""

import pathlib
import tempfile
import uuid
from typing import Generator
from unittest import mock

import deal
import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session as SessionType

from data_product_tracker.conn import session_factory
from data_product_tracker.models.base import Base

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
    """Create a temporary SQLite database file for testing file-based operations.

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
