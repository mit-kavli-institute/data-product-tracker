"""Library distribution management utilities."""

import typing
from importlib import metadata

Distribution = typing.NamedTuple(
    "Distribution", [("name", str), ("version", str)]
)


def yield_distributions() -> typing.Generator[Distribution, typing.Any, None]:
    """Yield unique installed Python distributions.

    Yields
    ------
    Distribution
        Named tuple with name and version of each unique distribution.
    """
    mask = set()
    for dist in metadata.distributions():
        converted = Distribution(
            name=dist.metadata["Name"], version=dist.version
        )
        if converted in mask:
            continue
        yield converted
        mask.add(converted)
