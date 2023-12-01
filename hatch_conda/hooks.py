from hatchling.plugin import hookimpl

from .plugin import CondaEnvironment, CondaEnvironmentCollector


@hookimpl
def hatch_register_environment():
    return CondaEnvironment


@hookimpl
def hatch_register_environment_collector():
    return CondaEnvironmentCollector
