"""Establish test-wide fixtures for `data_product_tracker` package"""

import os

import psycopg2
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from alembic import command
from alembic.config import Config


@pytest.fixture(scope="module")
def database():
    user = os.environ["TEST_DB_USER"]
    host = os.environ["TEST_DB_HOST"]
    password = os.environ["TEST_DB_PASSWORD"]
    port = os.environ["TEST_DB_PORT"]

    conn = psycopg2.connect(user=user, host=host, password=password)
    database_name = f"dpt_testing_{os.getpid()}"

    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE {database_name}")
        conn.commit()

    conn = psycopg2.connect(
        dbname=database_name, user=user, host=host, password=password
    )

    config = Config("./alembic.ini")
    config.attributes["connection"] = conn

    command.upgrade(config, "head")
    conn.close()

    engine = create_engine(
        f"psycopg2://{user}:{password}@{host}:{port}/{database_name}"
    )
    sessionmaker(bind=engine)
    yield sessionmaker

    conn = psycopg2.connect(
        dbname=database_name, user=user, host=host, password=password
    )
    with conn.cursor() as cur:
        cur.execute(f"DROP DATABASE {database_name}")
        cur.commit()
    conn.close()
