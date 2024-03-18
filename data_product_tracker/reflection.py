import os
import socket
from functools import wraps
from time import sleep

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from data_product_tracker.exceptions import ModelDoesNotExist
from data_product_tracker.libraries import yield_distributions_used
from data_product_tracker.models import environment as e


def get_os_environ_filter_clause():
    filters = []
    for key, value in os.environ.items():
        clause = sa.and_(e.Variable.key == key, e.Variable.value == value)
        filters.append(clause)

    return sa.or_(*filters)


def get_library_filter_clause():
    filters = []
    for distribution in yield_distributions_used():
        clause = sa.and_(
            e.Library.name == distribution.metadata["Name"],
            e.Library.version == distribution.version,
        )
        filters.append(clause)
    return sa.or_(*filters)


def db_retry(max_retries=10, backoff_factor=2):
    """
    Wrap a function to retry a database operation. Retries are done using
    an increasing backoff factor.
    """

    def _internal(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_try = 1
            current_wait = 0.5
            while current_try <= max_retries:
                try:
                    return func(*args, **kwargs)
                except IntegrityError:
                    sleep(current_wait)
                    current_wait *= backoff_factor
                    current_try += 1

        return wrapper

    return _internal


@db_retry()
def reflect_libraries(db):
    q = sa.select(e.Library)
    libraries = set()
    with db:
        for distribution in yield_distributions_used():
            library_q = q.where(
                e.Library.name == distribution.metadata["Name"],
                e.Library.version == distribution.version,
            )
            library = db.execute(library_q).scalar()
            if library is None:
                library = e.Library(
                    name=distribution.metadata["Name"],
                    version=distribution.version,
                )
                db.add(library)
                db.flush()
            libraries.add(library.id)
        db.commit()
    return libraries


@db_retry()
def reflect_variables(db):
    q = sa.select(e.Variable)
    variables = []
    with db:
        for key, value in os.environ.items():
            variable_q = q.where(
                e.Variable.key == key, e.Variable.value == value
            )
            variable = db.execute(variable_q).scalar()
            if variable is None:
                variable = e.Variable(key=key, value=value)
                db.add(variable)
                db.flush()
            variables.append(variable.id)
        db.commit()
    return variables


@db_retry()
def get_matching_env_by_variables(db) -> set[int]:
    q = (
        sa.select(e.VariableEnvironmentMap.environment_id)
        .join(
            e.Variable, e.Variable.id == e.VariableEnvironmentMap.variable_id
        )
        .where(get_os_environ_filter_clause())
        .group_by(e.VariableEnvironmentMap.environment_id)
        .having(
            sa.func.count(e.VariableEnvironmentMap.variable_id)
            == len(os.environ)
        )
    )

    with db:
        return set(db.scalars(q).fetchall())


@db_retry()
def get_matching_env_by_libraries(db) -> set[int]:
    q = (
        sa.select(e.LibraryEnvironmentMap.environment_id)
        .join(e.Library, e.Library.id == e.LibraryEnvironmentMap.library_id)
        .where(get_library_filter_clause())
        .group_by(e.LibraryEnvironmentMap.environment_id)
        .having(
            sa.func.count(e.LibraryEnvironmentMap.library_id)
            == len(list(yield_distributions_used()))
        )
    )

    with db:
        return set(db.scalars(q).fetchall())


def get_environment(db) -> int:

    env_ids = list(
        get_matching_env_by_libraries(db) & get_matching_env_by_variables(db)
    )
    with db:
        q = sa.select(e.Environment.id).where(
            e.Environment.id.in_(env_ids),
            e.Environment.host == socket.gethostname(),
        )
        env_id = db.scalar(q)

    if env_id is None:
        raise ModelDoesNotExist(e.Environment)
    return env_id


def get_or_create_env(db) -> tuple[int, bool]:
    try:
        env_id = get_environment(db)
        created = False
        return env_id, created
    except ModelDoesNotExist:
        libraries = reflect_libraries(db)
        variables = reflect_variables(db)

        env = e.Environment(host=socket.gethostname())
        with db:
            db.add(env)
            db.flush()

            library_relations = [
                e.LibraryEnvironmentMap(environment_id=env.id, library_id=id)
                for id in libraries
            ]

            variable_relations = [
                e.VariableEnvironmentMap(
                    environment_id=env.id,
                    variable_id=id,
                )
                for id in variables
            ]
            db.bulk_save_objects(library_relations)
            db.bulk_save_objects(variable_relations)
            db.commit()
            created = True
            return env.id, created
