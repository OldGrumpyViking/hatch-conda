import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from hatch_conda.plugin import BuildInCondaEnvHook

from .utils import build_project, conda_yaml, pyproject_toml, update_project_build

CONDA_FILENAME = "conda.yaml"


@pytest.fixture(scope="package")
def plugin_dir(request):
    project_root_dir = Path(request.fspath).parents[1]
    with TemporaryDirectory() as d:
        directory = Path(d, "plugin")
        shutil.copytree(project_root_dir, directory)

        yield directory.resolve()

        shutil.rmtree(directory, ignore_errors=True)


@pytest.fixture
def conda_file(temp_dir_data, project_name):
    project_dir = temp_dir_data / project_name
    project_dir.mkdir(parents=True, exist_ok=True)

    with conda_yaml(project_dir, CONDA_FILENAME) as config:
        config.update({"name": "test", "channels": ["conda-forge"], "dependencies": ["pip"]})

    yield project_dir / CONDA_FILENAME


@pytest.fixture
def conda_build_project(plugin_dir, hatch, temp_dir_data, config_file, project_name):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    with temp_dir_data.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir_data / project_name

    with pyproject_toml(project_path) as config:
        config["build-system"]["requires"].append(f"hatch-conda @ {plugin_dir.as_uri()}")

    package_dir = project_path / "src" / project_name
    package_dir.mkdir(parents=True, exist_ok=True)
    package_root = package_dir / "__about__.py"
    package_root.write_text('__version__ = "1.2.3"', encoding="utf-8")

    original_dir = os.getcwd()
    os.chdir(project_path)

    yield project_path

    os.chdir(original_dir)


class TestEnvFile:
    def test_default(self, conda_build_project):
        config = {}
        build_dir = conda_build_project / "dist"
        BuildInCondaEnvHook(str(conda_build_project), config, None, None, str(build_dir), "wheel")

    def test_with_file(self, conda_build_project, conda_file):
        config = {"environment-file": CONDA_FILENAME}
        build_dir = conda_build_project / "dist"
        build_hook = BuildInCondaEnvHook(str(conda_build_project), config, None, None, str(build_dir), "wheel")

        assert build_hook.environment_file == CONDA_FILENAME

    def test_with_file_missing(self, conda_build_project):
        config = {"environment-file": CONDA_FILENAME}
        build_dir = conda_build_project / "dist"
        build_hook = BuildInCondaEnvHook(str(conda_build_project), config, None, None, str(build_dir), "wheel")

        with pytest.raises(FileNotFoundError):
            build_hook.environment_file

    def test_with_bad_name(self, conda_build_project):
        config = {"environment-file": 123}
        build_dir = conda_build_project / "dist"
        build_hook = BuildInCondaEnvHook(str(conda_build_project), config, None, None, str(build_dir), "wheel")

        with pytest.raises(TypeError):
            build_hook.environment_file


class TestBuild:
    def test_default(self, conda_build_project):
        build_project()  # should always pass

    def test_with_no_args(self, conda_build_project):
        build_project("-t", "sdist")
        update_project_build(conda_build_project, "wheel", {})
        with pytest.raises(RuntimeError) as error:
            build_project("-t", "wheel")
        assert "ValueError: `environment-file`" in error.value.args[0]

    def test_no_deps(self, conda_build_project, conda_file):
        build_project("-t", "sdist")
        update_project_build(conda_build_project, "wheel", {"environment-file": CONDA_FILENAME})
        build_project("-t", "wheel")

    def test_deps(self, conda_build_project, conda_file):
        dependencies = ["pyyaml"]
        with conda_yaml(conda_build_project, CONDA_FILENAME) as config:
            config["dependencies"].append({"pip": dependencies})
        build_project("-t", "sdist")
        update_project_build(conda_build_project, "wheel", {"environment-file": CONDA_FILENAME})
        build_project("-t", "wheel")

    def test_dep_added(self, conda_build_project, conda_file):
        dependencies = ["a", "b @ https://example.com", "c == 1.2.3"]
        with conda_yaml(conda_build_project, CONDA_FILENAME) as conda_config:
            conda_config["dependencies"].append({"pip": dependencies})

        build_config = {"environment-file": CONDA_FILENAME}
        update_project_build(conda_build_project, "wheel", build_config)

        build_dir = conda_build_project / "dist"
        build_hook = BuildInCondaEnvHook(str(conda_build_project), build_config, None, None, str(build_dir), "wheel")
        build_data = {"dependencies": ["pyyaml"]}
        build_hook.initialize("1.2.3", build_data)
        for dep in dependencies:
            assert dep in build_data["dependencies"]
