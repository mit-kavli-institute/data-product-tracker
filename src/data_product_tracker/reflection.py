"""Database reflection utilities for environments, libraries, and variables."""

import socket
import time
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
    """Wrap a function to retry a database operation.

    Retries are done using an increasing backoff factor.
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


# Environment cache for performance optimization
class EnvironmentCache:
    """Simple TTL cache for environment lookups."""

    def __init__(self, ttl_seconds=300):
        """Initialize an empty cache with a time to live eviction strategy."""
        self._cache = {}
        self._timestamps = {}
        self.ttl = ttl_seconds

    def get_key(self, os_variables, distributions, hostname):
        """Create a deterministic cache key."""
        var_key = tuple(sorted((v.key, v.value) for v in os_variables))
        lib_key = tuple(sorted((d.name, d.version) for d in distributions))
        return (var_key, lib_key, hostname)

    def get(self, key):
        """Get value from cache if not expired."""
        if key in self._cache:
            if time.time() - self._timestamps[key] < self.ttl:
                return self._cache[key]
            else:
                del self._cache[key]
                del self._timestamps[key]
        return None

    def set(self, key, value):
        """Set value in cache with timestamp."""
        self._cache[key] = value
        self._timestamps[key] = time.time()

    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        self._timestamps.clear()


# Global cache instance
_env_cache = EnvironmentCache()


def _supports_returning(db):
    """Check if database supports RETURNING clause.

    Parameters
    ----------
    db : Session
        Database session.

    Returns
    -------
    bool
        True if database supports RETURNING clause.
    """
    return db.bind.dialect.name == "postgresql"


def clear_environment_cache():
    """Clear the environment cache. Useful for testing."""
    _env_cache.clear()


@db_retry()
def reflect_libraries_bulk(db, distributions: Iterable[Distribution]):
    """Bulk reflect library distributions using efficient SQL operations.

    Parameters
    ----------
    db : Session
        Database session.
    distributions : Iterable[Distribution]
        Library distributions to reflect.

    Returns
    -------
    dict[tuple[str, str], int]
        Mapping of (name, version) to library ID.
    """
    distributions_list = list(distributions)
    if not distributions_list:
        return {}

    result_map = {}

    with db:
        # First, find all existing libraries in a single query
        existing_libs = []
        if distributions_list:
            # Build OR conditions for all distributions
            conditions = [
                sa.and_(
                    e.Library.name == dist.name,
                    e.Library.version == dist.version,
                )
                for dist in distributions_list
            ]

            if conditions:
                existing_q = sa.select(
                    e.Library.id, e.Library.name, e.Library.version
                ).where(sa.or_(*conditions))

                existing_libs = db.execute(existing_q).all()

                # Map existing libraries
                for lib_id, name, version in existing_libs:
                    result_map[(name, version)] = lib_id

        # Find libraries that need to be created
        existing_keys = set(result_map.keys())
        to_create = [
            dist
            for dist in distributions_list
            if (dist.name, dist.version) not in existing_keys
        ]

        if to_create:
            if _supports_returning(db):
                # PostgreSQL: Use bulk insert with RETURNING
                insert_stmt = (
                    sa.insert(e.Library)
                    .values(
                        [
                            {"name": dist.name, "version": dist.version}
                            for dist in to_create
                        ]
                    )
                    .returning(e.Library.id, e.Library.name, e.Library.version)
                )

                new_libs = db.execute(insert_stmt).all()

                # Map newly created libraries
                for lib_id, name, version in new_libs:
                    result_map[(name, version)] = lib_id
            else:
                # SQLite: Use individual inserts
                for dist in to_create:
                    library = e.Library(name=dist.name, version=dist.version)
                    db.add(library)
                    db.flush()
                    result_map[(dist.name, dist.version)] = library.id

        db.commit()

    return result_map


@db_retry()
def reflect_variables_bulk(db, os_variables: Iterable[OSVariable]):
    """Bulk reflect OS variables using efficient SQL operations.

    Parameters
    ----------
    db : Session
        Database session.
    os_variables : Iterable[OSVariable]
        OS variables to reflect.

    Returns
    -------
    dict[tuple[str, str], int]
        Mapping of (key, value) to variable ID.
    """
    variables_list = list(os_variables)
    if not variables_list:
        return {}

    result_map = {}

    with db:
        # First, find all existing variables in a single query
        existing_vars = []
        if variables_list:
            # Build OR conditions for all variables
            conditions = [
                sa.and_(
                    e.Variable.key == var.key, e.Variable.value == var.value
                )
                for var in variables_list
            ]

            if conditions:
                existing_q = sa.select(
                    e.Variable.id, e.Variable.key, e.Variable.value
                ).where(sa.or_(*conditions))

                existing_vars = db.execute(existing_q).all()

                # Map existing variables
                for var_id, key, value in existing_vars:
                    result_map[(key, value)] = var_id

        # Find variables that need to be created
        existing_keys = set(result_map.keys())
        to_create = [
            var
            for var in variables_list
            if (var.key, var.value) not in existing_keys
        ]

        if to_create:
            if _supports_returning(db):
                # PostgreSQL: Use bulk insert with RETURNING
                insert_stmt = (
                    sa.insert(e.Variable)
                    .values(
                        [
                            {"key": var.key, "value": var.value}
                            for var in to_create
                        ]
                    )
                    .returning(e.Variable.id, e.Variable.key, e.Variable.value)
                )

                new_vars = db.execute(insert_stmt).all()

                # Map newly created variables
                for var_id, key, value in new_vars:
                    result_map[(key, value)] = var_id
            else:
                # SQLite: Use individual inserts
                for var in to_create:
                    variable = e.Variable(key=var.key, value=var.value)
                    db.add(variable)
                    db.flush()
                    result_map[(var.key, var.value)] = variable.id

        db.commit()

    return result_map


@db_retry()
def get_matching_environment_single_query(
    db,
    os_variables: list[OSVariable],
    distributions: list[Distribution],
    hostname: Optional[str] = None,
) -> Optional[int]:
    """Find environment matching all criteria in a single optimized query.

    Parameters
    ----------
    db : Session
        Database session.
    os_variables : list[OSVariable]
        Variables to match.
    distributions : list[Distribution]
        Distributions to match.
    hostname : str, optional
        Hostname to match. Defaults to current hostname.

    Returns
    -------
    int or None
        Environment ID if found, None otherwise.
    """
    if hostname is None:
        hostname = socket.gethostname()

    # Check cache first
    cache_key = _env_cache.get_key(os_variables, distributions, hostname)
    cached_env_id = _env_cache.get(cache_key)
    if cached_env_id is not None:
        # Verify the cached ID still exists in the database
        with db:
            exists = db.scalar(
                sa.select(sa.exists().where(e.Environment.id == cached_env_id))
            )
            if exists:
                return cached_env_id
            else:
                # Remove stale cache entry
                _env_cache._cache.pop(cache_key, None)
                _env_cache._timestamps.pop(cache_key, None)

    with db:
        # Build the query using CTEs for better optimization

        # CTE for environments with all required variables
        if os_variables:
            var_cte = (
                sa.select(e.VariableEnvironmentMap.environment_id)
                .join(e.Variable)
                .where(
                    sa.tuple_(e.Variable.key, e.Variable.value).in_(
                        [(v.key, v.value) for v in os_variables]
                    )
                )
                .group_by(e.VariableEnvironmentMap.environment_id)
                .having(sa.func.count() == len(os_variables))
                .cte("matching_var_envs")
            )

        # CTE for environments with all required libraries
        if distributions:
            lib_cte = (
                sa.select(e.LibraryEnvironmentMap.environment_id)
                .join(e.Library)
                .where(
                    sa.tuple_(e.Library.name, e.Library.version).in_(
                        [(d.name, d.version) for d in distributions]
                    )
                )
                .group_by(e.LibraryEnvironmentMap.environment_id)
                .having(sa.func.count() == len(distributions))
                .cte("matching_lib_envs")
            )

        # Build main query based on what we're matching
        query = sa.select(e.Environment.id).where(
            e.Environment.host == hostname
        )

        if os_variables:
            query = query.where(
                e.Environment.id.in_(sa.select(var_cte.c.environment_id))
            )

        if distributions:
            query = query.where(
                e.Environment.id.in_(sa.select(lib_cte.c.environment_id))
            )

        query = query.limit(1)

        env_id = db.scalar(query)

        # Cache the result
        if env_id is not None:
            _env_cache.set(cache_key, env_id)

        return env_id


@db_retry()
def reflect_libraries(db, distributions: Iterable[Distribution]):
    """Reflect library distributions to database.

    Parameters
    ----------
    db : Session
        Database session.
    distributions : Iterable[Distribution]
        Library distributions to reflect.

    Returns
    -------
    set[int]
        Set of Library IDs.
    """
    # Use bulk operation for performance
    distributions_list = list(distributions)
    bulk_result = reflect_libraries_bulk(db, distributions_list)

    # Return IDs in the same order as input for compatibility
    return set(bulk_result[(d.name, d.version)] for d in distributions_list)


@db_retry()
def reflect_variables(db, os_variables: Iterable[OSVariable]):
    """Reflect OS variables to database.

    Parameters
    ----------
    db : Session
        Database session.
    os_variables : Iterable[OSVariable]
        OS variables to reflect.

    Returns
    -------
    list[int]
        List of Variable IDs.
    """
    # Use bulk operation for performance
    variables_list = list(os_variables)
    bulk_result = reflect_variables_bulk(db, variables_list)

    # Return IDs in the same order as input for compatibility
    return [bulk_result[(v.key, v.value)] for v in variables_list]


@db_retry()
def get_matching_env_by_variables(
    db, os_variables: list[OSVariable]
) -> set[int]:
    """Get environment IDs matching given variables.

    Parameters
    ----------
    db : Session
        Database session.
    os_variables : list[OSVariable]
        Variables to match.

    Returns
    -------
    set[int]
        Set of matching environment IDs.
    """
    VEM = e.VariableEnvironmentMap

    with db:
        return set(db.scalars(VEM.matching_env_id_q(os_variables)))


@db_retry()
def get_matching_env_by_libraries(
    db, distributions: list[Distribution]
) -> set[int]:
    """Get environment IDs matching given libraries.

    Parameters
    ----------
    db : Session
        Database session.
    distributions : list[Distribution]
        Distributions to match.

    Returns
    -------
    set[int]
        Set of matching environment IDs.
    """
    LEM = e.LibraryEnvironmentMap
    with db:
        return set(db.scalars(LEM.matching_env_id_q(distributions)))


def get_environment(
    db,
    environ: Iterable[OSVariable],
    distributions: Iterable[Distribution],
) -> int:
    """Get environment ID matching given configuration.

    Parameters
    ----------
    db : Session
        Database session.
    environ : Iterable[OSVariable]
        OS variables to match.
    distributions : Iterable[Distribution]
        Library distributions to match.

    Returns
    -------
    int
        Environment ID.

    Raises
    ------
    ModelDoesNotExist
        If no matching environment found.
    """
    # Use single-query optimization
    env_id = get_matching_environment_single_query(
        db, list(environ), list(distributions)
    )

    if env_id is None:
        raise ModelDoesNotExist(e.Environment)

    return env_id


def get_or_create_env(
    db,
    environ: Optional[Iterable[OSVariable]] = None,
    distributions: Optional[Iterable[Distribution]] = None,
) -> tuple[int, bool]:
    """Get or create environment matching given configuration.

    Parameters
    ----------
    db : Session
        Database session.
    environ : Iterable[OSVariable], optional
        OS variables. If None, uses current environment.
    distributions : Iterable[Distribution], optional
        Library distributions. If None, uses installed packages.

    Returns
    -------
    tuple[int, bool]
        Tuple of (environment_id, created_flag).
    """
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
        # Use bulk operations for efficiency
        library_map = reflect_libraries_bulk(db, distributions)
        variable_map = reflect_variables_bulk(db, environ)

        hostname = socket.gethostname()

        with db:
            # Create environment
            env = e.Environment(host=hostname)
            db.add(env)
            db.flush()

            # Bulk create associations using bulk_insert_mappings
            if library_map:
                library_mappings = [
                    {"environment_id": env.id, "library_id": lib_id}
                    for lib_id in library_map.values()
                ]
                db.bulk_insert_mappings(
                    e.LibraryEnvironmentMap, library_mappings
                )

            if variable_map:
                variable_mappings = [
                    {"environment_id": env.id, "variable_id": var_id}
                    for var_id in variable_map.values()
                ]
                db.bulk_insert_mappings(
                    e.VariableEnvironmentMap, variable_mappings
                )

            db.commit()

            # Cache the new environment
            cache_key = _env_cache.get_key(environ, distributions, hostname)
            _env_cache.set(cache_key, env.id)

            created = True
            return env.id, created
