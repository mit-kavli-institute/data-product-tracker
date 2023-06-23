"""Establish test-wide fixtures for `data_product_tracker` package"""
import os
import pathlib
from contextlib import contextmanager

import deal
import psycopg2
import pytest  # noqa F401
from psycopg2.errors import DuplicateDatabase, ObjectInUse
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from data_product_tracker.models.base import Base

deal.enable()
CLEAN_FUNC = (
    "CREATE OR REPLACE FUNCTION truncate_tables(username IN VARCHAR) "
    "RETURNS void AS $$ "
    "DECLARE "
    "statements CURSOR FOR "
    "SELECT tablename FROM pg_tables "
    "WHERE tableowner = username AND schemaname = 'public'; "
    "BEGIN "
    "FOR stmt IN statements LOOP "
    " EXECUTE 'TRUNCATE TABLE ' || quote_ident(stmt.tablename) "
    "|| ' CASCADE;';"
    "END LOOP; "
    "END; "
    "$$ LANGUAGE plpgsql;"
)


def get_config_vals(env_path: pathlib.Path, **overrides):
    with open(env_path, "rt") as fin:
        kwargs = {}
        for line in fin:
            k, v = line.strip().split("=")
            kwargs[k] = v
    kwargs.update(**overrides)
    return kwargs


def get_test_db_conn(env_path: pathlib.Path, **overrides):
    kwargs = get_config_vals(env_path, **overrides)
    user = kwargs["username"]
    dbname = kwargs["database_name"]
    password = kwargs["password"]
    host = kwargs["database_host"]
    port = kwargs["database_port"]
    conn = psycopg2.connect(
        dbname=dbname, user=user, password=password, host=host, port=port
    )
    return conn


def pytest_sessionstart(session):
    admin_conn = get_test_db_conn(
        pathlib.Path(".test_env"),
        database_name="postgres",
    )

    admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    database_name = f"dpt_testing_{os.getpid()}"

    try:
        with admin_conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE {database_name}")
    except DuplicateDatabase:
        admin_conn.set_session(autocommit=True)
        with admin_conn.cursor() as cur:
            cur.execute(f"DROP DATABASE {database_name}")
            cur.execute(f"CREATE DATABASE {database_name}")

    engine_kwargs = get_config_vals(
        pathlib.Path(".test_env"), database_name=database_name
    )
    engine = create_engine(
        (
            "postgresql://{username}:{password}@{database_host}"
            ":{database_port}/{database_name}"
        ).format(**engine_kwargs),
        poolclass=NullPool,
    )
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)
    with db() as db:
        db.execute(text(CLEAN_FUNC))
        db.commit()


def pytest_sessionfinish(session, exitstatus):
    admin_conn = get_test_db_conn(
        pathlib.Path(".test_env"),
        database_name="postgres",
    )

    admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    database_name = f"dpt_testing_{os.getpid()}"

    while True:
        try:
            with admin_conn.cursor() as cur:
                cur.execute(f"DROP DATABASE {database_name}")
            admin_conn.close()
            break
        except ObjectInUse:
            continue


@contextmanager
def database_obj():
    database_name = f"dpt_testing_{os.getpid()}"
    engine_kwargs = get_config_vals(
        pathlib.Path(".test_env"), database_name=database_name
    )
    engine = create_engine(
        (
            "postgresql://{username}:{password}@{database_host}"
            ":{database_port}/{database_name}"
        ).format(**engine_kwargs),
        poolclass=NullPool,
    )
    db = sessionmaker(bind=engine)
    try:
        with db() as active_db:
            yield active_db
    finally:
        with db() as active_db:
            active_db.execute(text(("SELECT truncate_tables('postgres')")))
            active_db.commit()


def ensure_directory(path: pathlib.Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
