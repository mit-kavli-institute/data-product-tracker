import os
import socket

import pkg_resources
import sqlalchemy as sa

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


def reflect_libraries(db):
    q = sa.select(e.Library)
    libraries = []
    with db:
        for package in pkg_resources.working_set:
            library_q = q.where(
                e.Library.name == package.key,
                e.Library.version == package.version,
            )
            library = db.execute(library_q).scalars().first()
            if library is None:
                library = e.Library(
                    name=package.key,
                    version=package.version,
                )
                db.add(library)
                db.flush()
            libraries.append(library)
        db.commit()
    return libraries


def reflect_environment(db):
    q = sa.select(e.Variable)
    variables = []
    with db:
        for key, value in os.environ.items():
            variable_q = q.where(key == key, value == value)
            variable = db.execute(variable_q).scalars().first()
            if variable is None:
                variable = e.Variable(key=key, value=value)
                db.add(variable)
                db.flush()
            variables.append(variable)
        db.commit()
    return variables


def get_environment(db) -> e.Environment:
    variables_filter = get_os_environ_filter_clause()
    libraries_filter = get_library_filter_clause()

    library_count = sa.func.count(e.Library.id.distinct())
    variable_count = sa.func.count(e.Variable.id.distinct())
    n_pkgs = max([i for i, _ in enumerate(pkg_resources.working_set)])
    q = (
        sa.select(e.Environment.id, library_count, variable_count)
        .join(
            e.VariableEnvironmentMap,
            e.LibraryEnvironmentMap.environment_id
            == e.VariableEnvironmentMap.environment_id,
        )
        .join(e.LibraryEnvironmentMap.environment)
        .join(e.LibraryEnvironmentMap.library)
        .join(e.VariableEnvironmentMap.variable)
        .select_from(e.LibraryEnvironmentMap)
        .where(variables_filter)
        .where(libraries_filter)
        .where(e.Environment.host == socket.gethostname())
        .having(library_count == n_pkgs)
        .having(variable_count == len(os.environ))
        .group_by(e.Environment.id)
    )
    with db:
        env_id = db.execute(q).first()
        if env_id is None:
            raise ModelDoesNotExist(e.Environment)
        return db.query(e.Environment).get(env_id)


def get_or_create_env(db) -> tuple[int, bool]:
    try:
        env = get_environment(db)
        created = False
    except ModelDoesNotExist:
        libraries = reflect_libraries(db)
        variables = reflect_environment(db)

        env = e.Environment(host=socket.gethostname())
        with db:
            db.add(env)
            db.flush()

            library_relations = [
                e.LibraryEnvironmentMap(environment=env, library=library)
                for library in libraries
            ]

            variable_relations = [
                e.VariableEnvironmentMap(environment=env, variable=variable)
                for variable in variables
            ]
            db.bulk_save_objects(library_relations)
            db.bulk_save_objects(variable_relations)
            db.commit()
            created = True
            return env.id, created
