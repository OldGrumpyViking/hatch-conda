import shutil
from pathlib import Path
from textwrap import dedent as _dedent

import pytest
import tomli
import tomli_w
import yaml


def dedent(text):
    return _dedent(text[1:])


class SimpleConfig(dict):
    def __getitem__(self, key):
        item = super().__getitem__(key)
        if not isinstance(item, dict):
            return item
        new_item = SimpleConfig(item)  # makes nested access easier
        super().__setitem__(key, new_item)
        return new_item

    def __missing__(self, key):
        default = SimpleConfig()
        if isinstance(key, tuple):
            _, default = key
        super().__setitem__(key, default)
        return default

    def save_yaml(self, path, mode="w"):
        with path.open(mode) as file:
            yaml.safe_dump(dict(self), file)

    def save_toml(self, path, mode="wb"):
        with path.open(mode) as file:
            tomli_w.dump(dict(self), file)

    @staticmethod
    def from_yaml(path: Path, mode="r"):
        if not path.exists():
            return SimpleConfig()
        with path.open(mode, encoding="utf-8") as f:
            return SimpleConfig(yaml.safe_load(f))

    @staticmethod
    def from_toml(path: Path, mode="rb"):
        if not path.exists():
            return SimpleConfig()
        with path.open(mode) as f:
            return SimpleConfig(tomli.load(f))


class PyProject(SimpleConfig):
    @staticmethod
    def load(project_root):
        return PyProject(SimpleConfig.from_toml(project_root / "pyproject.toml"))

    def save(self, project_root):
        return self.save_toml(project_root / "pyproject.toml")


class CondaYAML(SimpleConfig):
    @staticmethod
    def load(project_root, filename="conda.yaml"):
        return CondaYAML(SimpleConfig.from_yaml(project_root / filename))

    def save(self, project_root, filename="conda.yaml"):
        return self.save_yaml(project_root / filename)


check_for_conda = pytest.mark.skipif(
    (shutil.which("conda") or shutil.which("micromamba")) is None,
    reason="Need at least one of the commands to test env setup",
)
