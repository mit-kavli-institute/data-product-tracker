"""Environment variable management utilities."""

import os
import typing

OSVariable = typing.NamedTuple("OSVariable", [("key", str), ("value", str)])


def yield_os_variables() -> typing.Generator[OSVariable, typing.Any, None]:
    """Yield OS environment variables as OSVariable tuples.

    Yields
    ------
    OSVariable
        Named tuple with key and value for each environment variable.
    """
    for k, v in os.environ.items():
        var = OSVariable(key=k, value=v)
        yield var
