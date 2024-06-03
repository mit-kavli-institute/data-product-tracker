from pathlib import Path
from typing import Any

from psycopg import adapters
from psycopg.adapt import Dumper


class PathLibDumper(Dumper):
    def dump(self, obj: Any):
        return str(obj).encode("utf-8")


adapters.register_dumper(Path, PathLibDumper)
