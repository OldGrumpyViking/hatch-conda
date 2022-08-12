from hatchling.plugin import hookimpl

from .plugin import CondaEnvironment


@hookimpl
def hatch_register_environment():
    return CondaEnvironment
