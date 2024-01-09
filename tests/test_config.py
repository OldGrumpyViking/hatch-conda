import shutil
from pathlib import Path

import pytest
import yaml
from hatch.project.core import Project

from hatch_conda.plugin import CondaEnvironment, normalize_conda_dict


class TestPythonVersion:
    def test_default(self, isolation, data_dir, platform, default_python_version):
        env_config = {}
        project = Project(
            isolation,
            config={
                "project": {"name": "my_app", "version": "0.0.1"},
                "tool": {"hatch": {"envs": {"default": env_config}}},
            },
        )
        environment = CondaEnvironment(
            root=isolation,
            metadata=project.metadata,
            name="default",
            config=project.config.envs["default"],
            matrix_variables={},
            data_directory=data_dir,
            isolated_data_directory=None,
            platform=platform,
            verbosity=0,
        )

        assert environment.python_version == default_python_version

    def test_long(self, isolation, data_dir, platform):
        env_config = {"python": "3.10"}
        project = Project(
            isolation,
            config={
                "project": {"name": "my_app", "version": "0.0.1"},
                "tool": {"hatch": {"envs": {"default": env_config}}},
            },
        )
        environment = CondaEnvironment(
            root=isolation,
            metadata=project.metadata,
            name="default",
            config=project.config.envs["default"],
            matrix_variables={},
            data_directory=data_dir,
            isolated_data_directory=None,
            platform=platform,
            verbosity=0,
        )

        assert environment.python_version == "3.10"

    def test_short(self, isolation, data_dir, platform):
        env_config = {"python": "310"}
        project = Project(
            isolation,
            config={
                "project": {"name": "my_app", "version": "0.0.1"},
                "tool": {"hatch": {"envs": {"default": env_config}}},
            },
        )

        environment = CondaEnvironment(
            root=isolation,
            metadata=project.metadata,
            name="default",
            config=project.config.envs["default"],
            matrix_variables={},
            data_directory=data_dir,
            isolated_data_directory=None,
            platform=platform,
            verbosity=0,
        )

        assert environment.python_version == "3.10"


class TestNormalizeConfig:
    def test_simple(self):
        config = {"a": "b", "c": {"d": "e"}}
        assert normalize_conda_dict(config) == config

    def test_list(self):
        config = {"a": "b", "c": ["d", "e"]}
        normalized_config = {"a": "b", "c": {"d": "", "e": ""}}
        assert normalize_conda_dict(config) == normalized_config

    def test_list_duplicate(self):
        config = {"a": "b", "c": ["d", "d"]}
        normalized_config = {"a": "b", "c": {"d": ""}}
        assert normalize_conda_dict(config) == normalized_config

    def test_nested_list(self):
        config = {"a": ["b", {"c": "d"}, {"e": ["f", {"g": {"h": ["i"]}}]}]}
        normalized_config = {"a": {"b": "", "c": "d", "e": {"f": "", "g": {"h": {"i": ""}}}}}
        assert normalize_conda_dict(config) == normalized_config

    def test_duplicate(self):
        config = {"a": ["b", {"b": ["c"]}]}
        normalized_config = {"a": {"b": {"c": "", "": ""}}}
        assert normalize_conda_dict(config) == normalized_config


@pytest.mark.skipif(
    (shutil.which("conda") or shutil.which("micromamba")) is None,
    reason="Need at least one of the commands to test env setup",
)
class TestDependencyUpdate:
    @pytest.fixture
    def environment(self, isolation, data_dir, platform) -> CondaEnvironment:
        command = "micromamba" if shutil.which("micromamba") else "conda"
        project = Project(
            isolation,
            config={
                "project": {"name": "my_app", "version": "0.0.1"},
                "tool": {"hatch": {"envs": {"default": {"environment-file": "test.yaml", "command": command}}}},
            },
        )
        environment = CondaEnvironment(
            root=isolation,
            metadata=project.metadata,
            name="default",
            config=project.config.envs["default"],
            matrix_variables={},
            data_directory=data_dir,
            isolated_data_directory=None,
            platform=platform,
            verbosity=0,
        )

        # write env file
        deps = {"name": "test", "channels": ["conda-forge"], "dependencies": ["pip", {"pip": ["pyyaml"]}]}
        env_file = Path(environment.environment_file)
        with env_file.open("w") as file:
            yaml.safe_dump(deps, file)

        return environment

    def test_environment_create(self, environment: CondaEnvironment):
        environment.create()
        assert "pyyaml" in environment.conda_contents["dependencies"]["pip"]
        assert environment.dependencies_in_sync()

        env_file = Path(environment.environment_file)
        with env_file.open() as file:
            config = yaml.safe_load(file)
        pip_deps = [dep["pip"] for dep in config["dependencies"] if isinstance(dep, dict) and "pip" in dep][0]
        pip_deps.append("hatch")
        config["dependencies"] = ["pip", {"pip": pip_deps}]
        with env_file.open("w") as file:
            yaml.safe_dump(config, file)
        assert not environment.dependencies_in_sync()
