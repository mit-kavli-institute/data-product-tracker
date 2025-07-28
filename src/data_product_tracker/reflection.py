"""Database reflection and environment detection module.

This module provides functions for reflecting the current environment,
including installed libraries and environment variables, into the database.
It handles automatic creation and deduplication of environments.
"""

import socket
from collections.abc import Iterable
from functools import wraps
from time import sleep
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import exc

from data_product_tracker.exceptions import ModelDoesNotExist
from data_product_tracker.libraries import Distribution, yield_distributions
from data_product_tracker.models import environment as e
from data_product_tracker.variables import OSVariable, yield_os_variables


def db_retry(max_retries=2, backoff_factor=2):
    """Decorator to retry database operations with exponential backoff.

    This decorator wraps functions that perform database operations and
    automatically retries them on database errors with increasing wait times.

    Parameters
    ----------
    max_retries : int, optional
        Maximum number of retry attempts. Default is 2.
    backoff_factor : int, optional
        Factor by which to multiply the wait time on each retry. Default is 2.

    Returns
    -------
    function
        Decorated function that will retry on database errors.

    Raises
    ------
    RuntimeError
        If all retry attempts fail.

    Notes
    -----
    The initial wait time is 0.5 seconds, which is multiplied by
    backoff_factor after each failed attempt.

    Examples
    --------
    >>> @db_retry(max_retries=3, backoff_factor=2)
    ... def risky_db_operation(db):
    ...     return db.execute("SELECT * FROM table")
    """

    def _internal(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_try = 1
            current_wait = 0.5
            while current_try <= max_retries:
                try:
                    return func(*args, **kwargs)
                except exc.DatabaseError as e:
                    sleep(current_wait)
                    current_wait *= backoff_factor
                    current_try += 1

                    if current_try >= max_retries:
                        raise RuntimeError from e

        return wrapper

    return _internal


@db_retry()
def reflect_libraries(db, distributions: Iterable[Distribution]):
    """Reflect Python distributions into the database.

    Creates Library records for the given distributions if they don't already exist.

    Parameters
    ----------
    db : sqlalchemy.orm.Session
        Database session to use for operations.
    distributions : Iterable[Distribution]
        Python package distributions to reflect into the database.

    Returns
    -------
    set[int]
        Set of library IDs that were created or found.

    Notes
    -----
    This function is idempotent - running it multiple times with the same
    distributions will not create duplicates.
    """
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
    """Reflect OS environment variables into the database.

    Creates Variable records for the given OS variables if they don't already exist.

    Parameters
    ----------
    db : sqlalchemy.orm.Session
        Database session to use for operations.
    os_variables : Iterable[OSVariable]
        Operating system environment variables to reflect into the database.

    Returns
    -------
    list[int]
        List of variable IDs that were created or found.

    Notes
    -----
    This function is idempotent - running it multiple times with the same
    variables will not create duplicates. Variables are uniquely identified
    by their key-value pairs.
    """
    q = sa.select(e.Variable)
    variables = []
    with db:
        for var in os_variables:
            variable_q = q.where(
                e.Variable.key == var.key,
                e.Variable.value == var.value,
            )
            variable = db.scalar(variable_q)
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

    with db:
        return set(db.scalars(VEM.matching_env_id_q(os_variables)))


@db_retry()
def get_matching_env_by_libraries(
    db, distributions: list[Distribution]
) -> set[int]:
    LEM = e.LibraryEnvironmentMap
    with db:
        return set(db.scalars(LEM.matching_env_id_q(distributions)))


def get_environment(
    db,
    environ: Iterable[OSVariable],
    distributions: Iterable[Distribution],
) -> int:

    env_ids = sorted(
        get_matching_env_by_libraries(db, list(distributions))
        & get_matching_env_by_variables(db, list(environ))
    )
    if len(env_ids) == 0:
        raise ModelDoesNotExist(e.Environment)

    env_id = env_ids[0]
    with db:
        q = sa.select(e.Environment.id).where(
            e.Environment.id == env_id,
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
