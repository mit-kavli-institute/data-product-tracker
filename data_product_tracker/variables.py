import os
import typing

OSVariable = typing.NamedTuple("OSVariable", [("key", str), ("value", str)])


def yield_os_variables() -> typing.Generator[OSVariable, typing.Any, None]:
    for k, v in os.environ.items():
        var = OSVariable(key=k, value=v)
        yield var
