import pathlib

import configurables as conf
import sqlalchemy as sa


@conf.configurable("Credentials", conf.ENV > conf.CONF)
@conf.param("username")
@conf.param("password")
@conf.option("database_name", default="dataproducttracker")
@conf.option("database_host", default="localhost")
@conf.option("database_port", type=int, default=5432)
def sessionmaker_from_config(
    username, password, database_name, database_host, database_port
):
    engine = sa.create_engine(
        f"postgresql://{username}:{password}"
        f"@{database_host}:{database_port}/{database_name}"
    )
    Session = sa.orm.sessionmaker(engine)
    return Session


CONFIG_DIR = pathlib.Path("~") / ".config" / "dpt"
CONFIG_PATH = CONFIG_DIR / "db.conf"

if not CONFIG_DIR.exists():
    CONFIG_DIR.mkdir(mode=0o600)

if not CONFIG_PATH.exists():
    sessionmaker_from_config.emit(CONFIG_PATH)
    raise RuntimeError(
        f"{str(CONFIG_PATH)} does not exist. Creating scaffold there..."
    )


db = sessionmaker_from_config(CONFIG_PATH)
