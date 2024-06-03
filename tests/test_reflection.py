import os

import sqlalchemy as sa
from hypothesis import HealthCheck, given, settings

from data_product_tracker.libraries import Distribution, yield_distributions
from data_product_tracker.models import environment as e
from data_product_tracker.reflection import (
    get_or_create_env,
    reflect_libraries,
    reflect_variables,
)
from data_product_tracker.variables import OSVariable

from . import strategies as dpt_st


@given(dpt_st.os_variables())
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_reflection_of_variables(db_session, os_variable: OSVariable):

    variable_q = sa.select(e.Variable).where(
        e.Variable.key == os_variable.key,
        e.Variable.value == os_variable.value,
    )

    exist_q = sa.select(variable_q.exists())

    variable_exists = db_session.scalar(exist_q)

    if not variable_exists:
        reflect_variables(db_session, [os_variable])

    variable = db_session.scalar(variable_q)

    assert variable is not None
    assert variable.key == os_variable.key
    assert variable.value == os_variable.value


@given(dpt_st.distributions())
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_reflection_of_libraries(db_session, distribution: Distribution):

    lib_q = sa.select(e.Library).where(
        e.Library.name == distribution.name,
        e.Library.version == distribution.version,
    )

    exist_q = sa.select(lib_q.exists())

    library_exists = db_session.scalar(exist_q)

    if not library_exists:
        reflect_libraries(db_session, [distribution])
    library = db_session.scalar(lib_q)

    assert library is not None
    assert library.name == distribution.name
    assert library.version == distribution.version


@given(dpt_st.environs(), dpt_st.library_installations())
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_reflection_of_environment(db_session, environ, distributions):
    env_id, _ = get_or_create_env(db_session)
    library_ref = {pkg.name: pkg.version for pkg in yield_distributions()}
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
        n_pkgs = len([_ for _ in yield_distributions()])
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
        for i, pkg in enumerate(yield_distributions()):
            lib_q = sa.select(e.Library.id).where(
                e.Library.name == pkg.name,
                e.Library.version == pkg.version,
            )
            hit = db_session.execute(lib_q).first()
            print(f"{i:02} | {pkg.name}:{pkg.version} -> {hit}")
        raise
