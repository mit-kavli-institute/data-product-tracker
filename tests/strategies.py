"""Hypothesis strategies for property-based testing."""

import pathlib
from functools import reduce

from hypothesis import strategies as st

from data_product_tracker.libraries import Distribution
from data_product_tracker.variables import OSVariable


def psql_valid_text(**kwargs):
    return st.text(
        alphabet=st.characters(
            exclude_characters="\x00", exclude_categories=("Cs",)
        ),
        **kwargs,
    )


def unix_viable_character():
    return st.integers(min_value=1, max_value=2**8 - 1).map(chr)


def unix_filename():
    return (
        st.text(alphabet=unix_viable_character(), min_size=1, max_size=255)
        .filter(lambda t: not t.startswith("/"))
        .map(pathlib.Path)
    )


def file_paths(
    file_system_strategy=None,
    max_depth=10,
):
    if file_system_strategy is None:
        file_system_strategy = st.one_of(
            unix_filename(),
        )
    tokens = st.lists(file_system_strategy, min_size=1, max_size=max_depth)
    return tokens.map(
        lambda list_: reduce(lambda left, right: left / right, list_)
    ).filter(lambda path: not path.is_dir())


def distributions():
    return st.builds(
        Distribution,
        name=psql_valid_text(min_size=1),
        version=st.from_regex(r"^(\d+\.)?(\d+\.)?(\*|\d+)$"),
    )


def os_variables():
    return st.builds(
        OSVariable,
        key=psql_valid_text(min_size=1),
        value=psql_valid_text(),
    )


def environs():
    return st.lists(os_variables(), unique_by=lambda var: var.key)


def library_installations():
    return st.lists(distributions(), unique_by=lambda dist: dist.name)
