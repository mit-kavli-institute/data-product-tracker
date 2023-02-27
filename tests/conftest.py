"""Establish test-wide fixtures for `data_product_tracker` package"""

import os

import psycopg2
import pytest
from psycopg2.errors import DuplicateDatabase
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from alembic import command
from alembic.config import Config


@pytest.fixture(scope="module")
def database():
    kwargs = {}
    with open(".test_env", "rt") as fin:
        for line in fin:
            k, v = line.strip().split("=")
            kwargs[k] = v

    user = kwargs["username"]
    password = kwargs["password"]
    host = kwargs["database_host"]
    port = kwargs["database_port"]

    conn = psycopg2.connect(
        dbname="postgres",
        user=user,
        host=host,
        password=password,
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    database_name = f"dpt_testing_{os.getpid()}"

    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE {database_name}")
    except DuplicateDatabase:
        conn.set_session(autocommit=True)
        with conn.cursor() as cur:
            cur.execute(f"DROP DATABASE {database_name}")
            cur.execute(f"CREATE DATABASE {database_name}")

    conn = psycopg2.connect(
        dbname=database_name, user=user, host=host, password=password
    )

    with open("./alembic.ini", "rt") as fin, open(
        "./alembic.ini.conv", "wt"
    ) as fout:
        for line in fin:
            if line.startswith("sqlalchemy.url"):
                url = (
                    f"postgresql://{user}:{password}@{host}"
                    f":{port}/{database_name}"
                )
                fout.write(f"sqlalchemy.url = {url}\n")
            else:
                fout.write(line)
    config = Config("./alembic.ini.conv")
    config.attributes["connection"] = conn

    command.upgrade(config, "head")
    conn.close()

    engine = create_engine(
        f"postgresql://{user}:{password}@{host}:{port}/{database_name}"
    )
    sessionmaker(bind=engine)
    yield sessionmaker

    conn = psycopg2.connect(
        dbname="postgres", user=user, host=host, password=password
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    with conn.cursor() as cur:
        cur.execute(f"DROP DATABASE {database_name}")
    conn.close()
