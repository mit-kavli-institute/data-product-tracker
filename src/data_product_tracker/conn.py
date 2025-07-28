import pathlib
import warnings

import configurables as conf
import sqlalchemy as sa
from sqlalchemy import create_engine, orm
from sqlalchemy.pool import NullPool


@conf.configurable("Credentials", conf.ENV > conf.CFG)
@conf.param("username")
@conf.param("password")
@conf.option("database_name", default="dataproducttracker")
@conf.option("database_host", default="localhost")
@conf.option("database_port", type=int, default=5432)
def configure_engine(
    username,
    password,
    database_name,
    database_host,
    database_port,
    **engine_kwargs,
):

    url = sa.URL.create(
        "postgresql+psycopg",
        database=database_name,
        username=username,
        password=password,
        host=database_host,
        port=database_port,
    )
    engine = create_engine(url, poolclass=NullPool, **engine_kwargs)

    return engine


CONFIG_DIR = (pathlib.Path("~") / ".config" / "dpt").expanduser()
CONFIG_PATH = CONFIG_DIR / "db.conf"


session_factory = orm.sessionmaker(expire_on_commit=False)


if not CONFIG_DIR.exists() or not CONFIG_PATH.exists():
    warnings.warn(
        f"{str(CONFIG_PATH)} does not exist. Creating scaffold there...",
        RuntimeWarning,
    )
    db = None
else:
    session_factory.configure(bind=configure_engine(CONFIG_PATH))
    db = session_factory()
