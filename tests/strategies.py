import pathlib
from functools import reduce

from hypothesis import strategies as st


def unix_viable_character():
    return st.integers(min_value=1, max_value=2**8 - 1).map(chr)


def unix_filename():
    return st.text(
        alphabet=unix_viable_character(), min_size=1, max_size=255
    ).map(pathlib.Path)


def file_paths(
    file_system_strategy=None,
    max_depth=10,
):
    if file_system_strategy is None:
        file_system_strategy = st.one_of(
            unix_filename(),
        )
    tokens = st.lists(file_system_strategy, min_size=1, max_size=max_depth)
    return tokens.map(lambda list_: reduce(lambda l, r: l / r, list_)).filter(
        lambda p: not p.is_dir()
    )
