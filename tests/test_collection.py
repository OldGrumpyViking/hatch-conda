import pytest
import yaml

from hatch_conda.plugin import CondaEnvironmentCollector


def test_collection_ctor(isolation):
    CondaEnvironmentCollector(
        root=isolation,
        config={},
    )


def test_collection_config(isolation):
    env_config = {"default": {}}
    collector = CondaEnvironmentCollector(
        root=isolation,
        config=env_config,
    )
    assert collector.config == env_config


def test_collection_no_file(isolation):
    env_config = {"default": {}}
    collector = CondaEnvironmentCollector(
        root=isolation,
        config=env_config,
    )
    config = {}
    collector.finalize_config(config)
    assert len(config) == 1
    assert config["default"]["dependencies"] == []


def test_collection_bad_file(isolation):
    env_config = {"default": {"environment-file": "not_present"}}
    collector = CondaEnvironmentCollector(
        root=isolation,
        config=env_config,
    )
    config = {}
    with pytest.raises(FileNotFoundError):
        collector.finalize_config(config)


def test_collection_no_pip(isolation):
    env_config = {"default": {"environment-file": "env.yaml"}}
    conda_config = {"dependencies": ["one", "two"]}
    with (isolation / "env.yaml").open("w") as file:
        yaml.dump(conda_config, file)
    collector = CondaEnvironmentCollector(
        root=isolation,
        config=env_config,
    )
    config = {}
    collector.finalize_config(config)
    assert config["default"]["dependencies"] == []


def test_collection_pip(isolation):
    env_config = {"default": {"environment-file": "env.yaml"}}
    conda_config = {"dependencies": ["one", "two", {"other": "three"}]}
    pip_deps = ["a", "b"]
    conda_config["dependencies"].append({"pip": ["--pip-option"] + pip_deps})
    with (isolation / "env.yaml").open("w") as file:
        yaml.dump(conda_config, file)
    collector = CondaEnvironmentCollector(
        root=isolation,
        config=env_config,
    )
    config = {}
    collector.finalize_config(config)
    assert config["default"]["dependencies"] == pip_deps
