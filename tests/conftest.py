"""Establish test-wide fixtures for `data_product_tracker` package"""
import os

import psycopg2
import pytest
from psycopg2.errors import DuplicateDatabase, ObjectInUse
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from data_product_tracker.models.base import Base


@pytest.fixture()
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

    engine = create_engine(
        f"postgresql://{user}:{password}@{host}:{port}/{database_name}",
        poolclass=NullPool,
    )
    db = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    try:
        yield db()
        del db
        del engine
    finally:
        while True:
            try:
                conn = psycopg2.connect(
                    dbname="postgres", user=user, host=host, password=password
                )
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                with conn.cursor() as cur:
                    cur.execute(f"DROP DATABASE {database_name}")
                conn.close()
                break
            except ObjectInUse:
                continue
