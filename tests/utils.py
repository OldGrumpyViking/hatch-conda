import subprocess
from contextlib import contextmanager
from pathlib import Path
from textwrap import dedent as _dedent

import tomli
import tomli_w
import yaml


def dedent(text):
    return _dedent(text[1:])


@contextmanager
def pyproject_toml(project):
    project_root = project if isinstance(project, Path) else project.root
    project_file = project_root / "pyproject.toml"
    with project_file.open("r", encoding="utf-8") as f:
        raw_config = tomli.loads(f.read())

    yield raw_config

    with project_file.open("wb") as f:
        tomli_w.dump(raw_config, f)


@contextmanager
def conda_yaml(project, file_name="conda.yaml"):
    project_root = project if isinstance(project, Path) else project.root
    conda_file = project_root / file_name
    if conda_file.exists():
        with conda_file.open("r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)
    else:
        raw_config = {}

    yield raw_config

    with conda_file.open("w") as f:
        yaml.safe_dump(raw_config, f)


def update_project_environment(project, name, config):
    with pyproject_toml(project) as raw_config:
        env_config = (
            raw_config.setdefault("tool", {}).setdefault("hatch", {}).setdefault("envs", {}).setdefault(name, {})
        )
        env_config.update(config)

        project.config.envs[name] = project.config.envs.get(name, project.config.envs["default"]).copy()
        project.config.envs[name].update(env_config)


def build_project(*args):
    process = subprocess.run(["hatch", "build", *args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if process.returncode:  # no cov
        raise RuntimeError(process.stdout.decode("utf-8"))


def update_project_build(project, target_name, config):
    with pyproject_toml(project) as raw_config:
        build_config = (
            raw_config.setdefault("tool", {})
            .setdefault("hatch", {})
            .setdefault("build", {})
            .setdefault("targets", {})
            .setdefault(target_name, {})
            .setdefault("hooks", {})
            .setdefault("conda", {})
        )
        build_config.update(config)
