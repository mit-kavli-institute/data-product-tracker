import socket
from collections.abc import Iterable
from functools import wraps
from time import sleep
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from data_product_tracker.exceptions import ModelDoesNotExist
from data_product_tracker.libraries import Distribution, yield_distributions
from data_product_tracker.models import environment as e
from data_product_tracker.variables import OSVariable, yield_os_variables


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
def reflect_libraries(db, distributions: Iterable[Distribution]):
    q = sa.select(e.Library)
    libraries = set()
    with db:
        for distribution in distributions:
            library_q = q.where(
                e.Library.name == distribution.name,
                e.Library.version == distribution.version,
            )
            library = db.execute(library_q).scalar()
            if library is None:
                library = e.Library(
                    name=distribution.name,
                    version=distribution.version,
                )
                db.add(library)
                db.flush()
            libraries.add(library.id)
        db.commit()
    return libraries


@db_retry()
def reflect_variables(db, os_variables: Iterable[OSVariable]):
    q = sa.select(e.Variable)
    variables = []
    with db:
        for var in os_variables:
            variable_q = q.where(
                e.Variable.key == var.key,
                e.Variable.value == var.value,
            )
            variable = db.execute(variable_q).scalar()
            if variable is None:
                variable = e.Variable(key=var.key, value=var.value)
                db.add(variable)
                db.flush()
            variables.append(variable.id)
        db.commit()
    return variables


@db_retry()
def get_matching_env_by_variables(
    db, os_variables: list[OSVariable]
) -> set[int]:
    VEM = e.VariableEnvironmentMap
    q = (
        sa.select(VEM.environment_id)
        .join(e.Variable, e.Variable.id == VEM.variable_id)
        .where(e.Variable.filter_by_variables(os_variables))
        .group_by(VEM.environment_id)
        .having(sa.func.count(VEM.variable_id) == len(os_variables))
    )

    with db:
        return set(db.scalars(q).fetchall())


@db_retry()
def get_matching_env_by_libraries(
    db, distributions: list[Distribution]
) -> set[int]:
    q = (
        sa.select(e.LibraryEnvironmentMap.environment_id)
        .join(
            e.Library,
            e.Library.id == e.LibraryEnvironmentMap.library_id,
        )
        .where(e.Library.filter_by_distributions(distributions))
        .group_by(e.LibraryEnvironmentMap.environment_id)
        .having(
            sa.func.count(e.LibraryEnvironmentMap.library_id)
            == len(distributions)
        )
    )

    with db:
        return set(db.scalars(q).fetchall())


def get_environment(
    db,
    environ: Iterable[OSVariable],
    distributions: Iterable[Distribution],
) -> int:

    env_ids = list(
        get_matching_env_by_libraries(db, list(distributions))
        & get_matching_env_by_variables(db, list(environ))
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


def get_or_create_env(
    db,
    environ: Optional[Iterable[OSVariable]] = None,
    distributions: Optional[Iterable[Distribution]] = None,
) -> tuple[int, bool]:
    if distributions is None:
        distributions = list(yield_distributions())
    else:
        distributions = list(distributions)

    if environ is None:
        environ = list(yield_os_variables())
    else:
        environ = list(environ)

    try:
        env_id = get_environment(db, environ, distributions)
        created = False
        return env_id, created
    except ModelDoesNotExist:
        libraries = reflect_libraries(db, distributions)
        variables = reflect_variables(db, environ)

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
