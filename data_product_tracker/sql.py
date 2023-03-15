import pathlib

from psycopg2.extensions import QuotedString, register_adapter


def adapt_pathlib_path(path):
    return QuotedString(str(path))


register_adapter(pathlib.Path, adapt_pathlib_path)
