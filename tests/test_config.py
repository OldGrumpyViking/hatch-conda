import shutil
from pathlib import Path

import pytest
import tomli_w
import yaml
from hatch.project.core import Project

from hatch_conda.plugin import CondaEnvironment, CondaEnvironmentCollector, normalize_conda_dict


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
    def environment(self, data_dir) -> Path:
        env_file = "conda.yaml"
        config = {
            "project": {"name": "my_app", "version": "0.0.1"},
            "tool": {
                "hatch": {
                    "env": {
                        "collectors": {"conda": {"default": {"environment-file": env_file}}},
                        "requires": ["hatch-conda"],
                    },
                    "envs": {"default": {"environment-file": env_file, "dependencies": ["tomli"]}},
                }
            },
        }
        with (data_dir / "pyproject.toml").open("wb") as file:
            tomli_w.dump(config, file)

        # write env file
        deps = {"name": "test", "channels": ["conda-forge"], "dependencies": ["pip", {"pip": ["pyyaml"]}]}
        conda_file = data_dir / env_file
        with conda_file.open("w") as file:
            yaml.safe_dump(deps, file)

        return conda_file

    def test_corrrect_dependencies(self, data_dir, environment):
        env_modified = CondaEnvironmentCollector(data_dir, {"default": {"environment-file": environment}})
        new_config = {}
        env_modified.finalize_config(new_config)
        assert "default" in new_config
        assert "dependencies" in new_config["default"]
        dependencies = new_config["default"]["dependencies"]
        assert "pyyaml" in dependencies

        new_config["default"]["dependencies"] = ["tomli"]
        env_modified.finalize_config(new_config)
        dependencies = new_config["default"]["dependencies"]
        assert "tomli" in dependencies
        assert "pyyaml" in dependencies

    def test_bad_file(self, data_dir):
        env_modified = CondaEnvironmentCollector(data_dir, {"default": {"environment-file": "does_not_exist.yaml"}})
        new_config = {"default": {"dependencies": ["tomli"]}}
        env_modified.finalize_config(new_config)
        dependencies = new_config["default"]["dependencies"]
        assert dependencies == ["tomli"]
