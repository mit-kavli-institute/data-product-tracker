import os

import pkg_resources
import pytest  # noqa 401
import sqlalchemy as sa

from data_product_tracker.models import environment as e
from data_product_tracker.reflection import (
    get_library_filter_clause,
    get_or_create_env,
    get_os_environ_filter_clause,
    reflect_libraries,
    reflect_variables,
)


def test_reflection_of_variables(database):
    with database as db:
        variable_q = sa.select(e.Variable)
        for k, v in os.environ.items():
            q = variable_q.where(e.Variable.key == k, e.Variable.value == v)
            variable = db.execute(q).scalar()
            assert variable is not None
            assert variable.key == k
            assert variable.value == v
        count = db.execute(sa.func.count(e.Variable.id)).scalar()
        assert count == len(os.environ)


def test_reflection_of_libraries(database):
    with database as db:
        library_q = sa.select(e.Library)
        for i, pkg in enumerate(pkg_resources.working_set, start=1):
            q = library_q.where(
                e.Library.name == pkg.key, e.Library.version == pkg.version
            )
            library = db.execute(q).scalar()
            assert library is not None
            assert library.name == pkg.key
            assert library.version == pkg.version
        count = db.execute(sa.func.count(e.Library.id)).scalar()
        assert count == i


def test_variable_filter(database):
    with database as db:
        reflect_variables(db)
        q = sa.select(e.Variable).where(get_os_environ_filter_clause())
        variables = db.execute(q).scalars()
        remote = {(v.key, v.value): v.id for v in variables}

        for key in os.environ.items():
            assert key in remote


def test_library_filter(database):
    with database as db:
        reflect_libraries(db)
        q = sa.select(e.Library).where(get_library_filter_clause())
        libraries = db.execute(q).scalars()
        remote = {}
        for library in libraries:
            remote[(library.name, library.version)] = library.id

        for pkg in pkg_resources.working_set:
            assert (pkg.key, pkg.version) in remote


def test_reflection_of_environment(database):
    env_id, _ = get_or_create_env(database)
    library_ref = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
    with database as db:
        q = sa.select(e.Environment).where(e.Environment.id == env_id)
        environment = db.execute(q).scalars().first()
        for variable in environment.variables:
            assert variable.value == os.environ[variable.key]

        for library in environment.libraries:
            assert library.version == library_ref[library.name]


def test_non_duplication_of_envs(database):
    env_id_1, created = get_or_create_env(database)

    assert created

    try:
        env_id_2, created = get_or_create_env(database)

        assert not created
        assert env_id_1 == env_id_2
    except AssertionError:
        with database as db:
            print(db.execute(sa.select(e.VariableEnvironmentMap)).all())
            print(db.execute(sa.select(e.LibraryEnvironmentMap)).all())
            q = (
                sa.select(
                    e.LibraryEnvironmentMap.environment_id,
                    sa.func.count(
                        e.LibraryEnvironmentMap.library_id.distinct()
                    ),
                    sa.func.count(
                        e.VariableEnvironmentMap.variable_id.distinct()
                    ),
                )
                .join(
                    e.VariableEnvironmentMap,
                    e.LibraryEnvironmentMap.environment_id
                    == e.VariableEnvironmentMap.environment_id,
                )
                .group_by(e.LibraryEnvironmentMap.environment_id)
            )
            print(db.execute(q).all())
            print(len(os.environ))
            raise
