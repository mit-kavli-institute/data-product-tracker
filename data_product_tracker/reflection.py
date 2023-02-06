import os

import pkg_resources
import sqlalchemy as sa

from data_product_tracker.conn import db
from data_product_tracker.models import environment as e


def get_os_environ_filter_clause():
    filters = []
    for key, value in os.environ.items():
        clause = sa.and_(e.Variable.key == key, e.Variable.value == value)
        filters.append(clause)

    return sa.and_(*filters)


def get_installed_python_modules():
    q = sa.select(e.Library)
    libraries = []
    with db:
        for package in pkg_resources.working_set:
            library_q = q.where(
                name=package.name,
                version=package.version,
                location=package.path,
            )
            library = db.execute(library_q).scalars().first()
            if library is None:
                library = e.Library(
                    name=package.name,
                    version=package.version,
                    location=package.path,
                )
                db.add(library)
                db.flush()
            libraries.append(library)
        db.commit()
    return libraries


def get_or_create_env() -> e.Environment:
    raise NotImplementedError
