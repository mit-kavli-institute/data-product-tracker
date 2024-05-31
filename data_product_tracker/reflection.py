import os
import socket
from functools import wraps
from time import sleep

import pkg_resources
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from data_product_tracker.exceptions import ModelDoesNotExist
from data_product_tracker.models import environment as e


def get_os_environ_filter_clause():
    filters = []
    for key, value in os.environ.items():
        clause = sa.and_(e.Variable.key == key, e.Variable.value == value)
        filters.append(clause)

    return sa.or_(*filters)


def get_library_filter_clause():
    filters = []
    for package in pkg_resources.working_set:
        clause = sa.and_(
            e.Library.name == package.key,
            e.Library.version == package.version,
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
    libraries = []
    with db:
        for package in pkg_resources.working_set:
            library_q = q.where(
                e.Library.name == package.key,
                e.Library.version == package.version,
            )
            library = db.execute(library_q).scalar()
            if library is None:
                library = e.Library(
                    name=package.key,
                    version=package.version,
                )
                db.add(library)
                db.flush()
            libraries.append(library.id)
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


def get_environment(db) -> int:
    variables_filter = get_os_environ_filter_clause()
    libraries_filter = get_library_filter_clause()
    VEM = e.VariableEnvironmentMap
    LEM = e.LibraryEnvironmentMap
    n_pkgs = len([_ for _ in pkg_resources.working_set])

    viable_variable_env_ids = db.scalars(
        sa.select(VEM.environment_id)
        .join(e.Variable, VEM.variable_id == e.Variable.id)
        .group_by(VEM.environment_id)
        .where(variables_filter)
        .having(sa.func.count(VEM.variable_id) == len(os.environ))
    )

    viable_library_env_ids = db.scalars(
        sa.select(LEM.environment_id)
        .join(e.Library, LEM.library_id == e.Library.id)
        .group_by(LEM.environment_id)
        .where(libraries_filter)
        .having(sa.func.count(LEM.library_id) == n_pkgs)
    )

    viable_env_ids = set(viable_variable_env_ids) & set(viable_library_env_ids)
    if len(viable_env_ids) == 0:
        raise ModelDoesNotExist(e.Environment)

    # Odd, possible duplicate environments, return the 'lowest' environment
    return sorted(viable_env_ids)[0]


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
