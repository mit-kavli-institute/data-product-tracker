import os

import sqlalchemy as sa
from hypothesis import HealthCheck, assume, given, note, settings

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
def test_reflection_of_variables(db_session_file, os_variable: OSVariable):

    variable_q = sa.select(e.Variable).where(
        e.Variable.key == os_variable.key,
        e.Variable.value == os_variable.value,
    )

    created_variables = reflect_variables(db_session_file, [os_variable])

    variable = db_session_file.scalar(variable_q)

    note(str(created_variables))
    note(str(db_session_file.execute(sa.select(e.Variable)).all()))

    assert variable is not None
    assert variable.key == os_variable.key
    assert variable.value == os_variable.value


@given(dpt_st.distributions())
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_reflection_of_libraries(db_session_file, distribution: Distribution):

    lib_q = sa.select(e.Library).where(
        e.Library.name == distribution.name,
        e.Library.version == distribution.version,
    )

    exist_q = sa.select(lib_q.exists())

    library_exists = db_session_file.scalar(exist_q)

    if not library_exists:
        reflect_libraries(db_session_file, [distribution])
    library = db_session_file.scalar(lib_q)

    assert library is not None
    assert library.name == distribution.name
    assert library.version == distribution.version


@given(dpt_st.environs(), dpt_st.library_installations())
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_reflection_of_environment(db_session_file, environ, distributions):
    env_id, created = get_or_create_env(
        db_session_file, environ, distributions
    )
    note(str((env_id, created)))
    q = sa.select(e.Environment).where(e.Environment.id == env_id)
    environment = db_session_file.execute(q).scalars().first()

    assert len(environment.variables) == len(environ)
    assert len(environment.libraries) == len(distributions)

    note(
        e.LibraryEnvironmentMap.matching_env_id_q(distributions).compile(
            compile_kwargs={"literal_binds": True}
        )
    )

    for variable in environment.variables:
        remote_var = OSVariable(key=variable.key, value=variable.value)
        assert remote_var in environ

    for library in environment.libraries:
        remote_dis = Distribution(name=library.name, version=library.version)
        assert remote_dis in distributions


def test_non_duplication_of_envs_static(db_session_file):
    env_id_1, created = get_or_create_env(db_session_file)

    assert created

    try:
        env_id_2, created = get_or_create_env(db_session_file)

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
        print(db_session_file.execute(q).all())
        print(db_session_file.execute(raw_q).all())
        print(q.compile(compile_kwargs={"literal_binds": True}))
        print("Library Diff")
        for i, pkg in enumerate(yield_distributions()):
            lib_q = sa.select(e.Library.id).where(
                e.Library.name == pkg.name,
                e.Library.version == pkg.version,
            )
            hit = db_session_file.execute(lib_q).first()
            print(f"{i:02} | {pkg.name}:{pkg.version} -> {hit}")
        raise


@given(dpt_st.environs(), dpt_st.library_installations())
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_non_duplication_of_envs(db_session_file, environ, distributions):

    assume(len(environ) > 0 and len(distributions) > 0)

    env_id_1, _ = get_or_create_env(db_session_file, environ, distributions)

    env_id_2, created = get_or_create_env(
        db_session_file, environ, distributions
    )

    assert not created
    assert env_id_1 == env_id_2
