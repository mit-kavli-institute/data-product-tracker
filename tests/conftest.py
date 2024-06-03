"""Establish test-wide fixtures for `data_product_tracker` package"""

import pathlib

import deal
import pytest  # noqa F401
import sqlalchemy as sa

from data_product_tracker.conn import Session
from data_product_tracker.models.base import Base

deal.enable()


@pytest.fixture
def db_session(postgresql):
    url = sa.URL.create(
        "postgresql+psycopg",
        database=postgresql.info.dbname,
        username=postgresql.info.user,
        password=postgresql.info.password,
        host=postgresql.info.host,
        port=postgresql.info.port,
    )

    engine = sa.create_engine(url, poolclass=sa.pool.NullPool)

    Base.metadata.create_all(bind=engine, checkfirst=True)

    Session.configure(bind=engine)

    sess = Session()

    try:
        yield sess
    finally:
        sess.close_all()


def ensure_directory(path: pathlib.Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
