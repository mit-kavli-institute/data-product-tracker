import os

import sqlalchemy as sa

from data_product_tracker.libraries import yield_distributions_used
from data_product_tracker.models import environment as e
from data_product_tracker.reflection import (
    get_library_filter_clause,
    get_or_create_env,
    get_os_environ_filter_clause,
    reflect_libraries,
    reflect_variables,
)


def test_reflection_of_variables(db_session):
    reflect_variables(db_session)
    variable_q = sa.select(e.Variable)
    for k, v in os.environ.items():
        q = variable_q.where(e.Variable.key == k, e.Variable.value == v)
        variable = db_session.execute(q).scalar()
        assert variable is not None
        assert variable.key == k
        assert variable.value == v
    count = db_session.execute(sa.func.count(e.Variable.id)).scalar()
    assert count == len(os.environ)


def test_reflection_of_libraries(db_session):
    reflect_libraries(db_session)
    library_q = sa.select(e.Library)
    for i, pkg in enumerate(yield_distributions_used(), start=1):
        q = library_q.where(
            e.Library.name == pkg.metadata["Name"],
            e.Library.version == pkg.version,
        )
        library = db_session.execute(q).scalar()
        assert library is not None
        assert library.name == pkg.metadata["Name"]
        assert library.version == pkg.version
    count = db_session.execute(sa.func.count(e.Library.id)).scalar()
    assert count == i


def test_variable_filter(db_session):
    reflect_variables(db_session)
    q = sa.select(e.Variable).where(get_os_environ_filter_clause())
    variables = db_session.execute(q).scalars()
    remote = {(v.key, v.value): v.id for v in variables}

    for key in os.environ.items():
        assert key in remote


def test_library_filter(db_session):
    reflect_libraries(db_session)
    q = sa.select(e.Library).where(get_library_filter_clause())
    libraries = db_session.execute(q).scalars()
    remote = {}
    for library in libraries:
        remote[(library.name, library.version)] = library.id

    for pkg in yield_distributions_used():
        assert (pkg.metadata["Name"], pkg.version) in remote


def test_reflection_of_environment(db_session):
    env_id, _ = get_or_create_env(db_session)
    library_ref = {
        pkg.metadata["Name"]: pkg.version for pkg in yield_distributions_used()
    }
    q = sa.select(e.Environment).where(e.Environment.id == env_id)
    environment = db_session.execute(q).scalars().first()
    for variable in environment.variables:
        assert variable.value == os.environ[variable.key]

    for library in environment.libraries:
        assert library.version == library_ref[library.name]


def test_non_duplication_of_envs(db_session):
    env_id_1, created = get_or_create_env(db_session)

    assert created

    try:
        env_id_2, created = get_or_create_env(db_session)

        assert not created
        assert env_id_1 == env_id_2
    except AssertionError:
        n_pkgs = len([_ for _ in yield_distributions_used()])
        library_count = sa.func.count(
            e.LibraryEnvironmentMap.library_id.distinct()
        )
        variable_count = sa.func.count(
            e.VariableEnvironmentMap.variable_id.distinct()
        )
        raw_q = (
            sa.select(
                e.LibraryEnvironmentMap.environment_id,
                library_count,
                variable_count,
            )
            .join(
                e.VariableEnvironmentMap,
                e.LibraryEnvironmentMap.environment_id
                == e.VariableEnvironmentMap.environment_id,
            )
            .group_by(e.LibraryEnvironmentMap.environment_id)
        )

        q = raw_q.having(
            library_count == n_pkgs, variable_count == len(os.environ)
        )
        print(f"#libraries {n_pkgs}, #variables {len(os.environ)}")
        print(db_session.execute(q).all())
        print(db_session.execute(raw_q).all())
        print(q.compile(compile_kwargs={"literal_binds": True}))
        print("Library Diff")
        for i, pkg in enumerate(yield_distributions_used()):
            lib_q = sa.select(e.Library.id).where(
                e.Library.name == pkg.metadata["Name"],
                e.Library.version == pkg.version,
            )
            hit = db_session.execute(lib_q).first()
            print(f"{i:02} | {pkg.metadata['Name']}:{pkg.version} -> {hit}")
        raise
