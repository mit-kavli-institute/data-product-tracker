import pathlib
import warnings

import configurables as conf
from sqlalchemy import create_engine, orm
from sqlalchemy.pool import NullPool


@conf.configurable("Credentials", conf.ENV > conf.CFG)
@conf.param("username")
@conf.param("password")
@conf.option("database_name", default="dataproducttracker")
@conf.option("database_host", default="localhost")
@conf.option("database_port", type=int, default=5432)
def session_from_config(
    username, password, database_name, database_host, database_port
):
    engine = create_engine(
        f"postgresql://{username}:{password}"
        f"@{database_host}:{database_port}/{database_name}",
        poolclass=NullPool,
    )
    Session = orm.sessionmaker(engine)
    return Session()


CONFIG_DIR = (pathlib.Path("~") / ".config" / "dpt").expanduser()
CONFIG_PATH = CONFIG_DIR / "db.conf"


if not CONFIG_DIR.exists() or not CONFIG_PATH.exists():
    warnings.warn(
        f"{str(CONFIG_PATH)} does not exist. Creating scaffold there...",
        RuntimeWarning,
    )
    db = None
else:
    db = session_from_config(CONFIG_PATH)
