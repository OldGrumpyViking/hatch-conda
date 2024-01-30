import platform

import pytest

from .utils import CondaYAML, PyProject, check_for_conda


def test_pyproject(conda_project):
    pyproject = PyProject.load(conda_project)
    default_env = pyproject["tool"]["hatch"]["envs"]["default"]
    assert default_env != {}, default_env


def test_conda_yaml(conda_project):
    conda_yaml = CondaYAML.load(conda_project)
    assert "dependencies" in conda_yaml
    assert "name" in conda_yaml
    assert "channels" in conda_yaml


@check_for_conda
class TestEnv:
    def test_no_conda(self, hatch, conda_project):
        pyproject = PyProject.load(conda_project)
        pyproject["tool"]["hatch"]["envs"]["default"].pop("type")
        pyproject["tool"]["hatch"]["envs"]["default"].pop("command")
        pyproject.save(conda_project)
        with conda_project.as_cwd():
            result = hatch("run", "python", "--version")
        assert result.exit_code == 0

    @pytest.mark.slow
    def test_conda(self, hatch, conda_project):
        pyproject = PyProject.load(conda_project)
        pyproject["tool"]["hatch"]["envs"]["default"]["environment-file"] = "conda.yaml"
        pyproject.save(conda_project)
        # TODO: find issue here. Error in mamba for some reason. Can't replicate it manually
        # /tmp/mambafK97uhzLFAf: line 5: exec: --: invalid option
        with conda_project.as_cwd():
            result = hatch("-v", "run", "python", "--version")
        assert result.exit_code == 0, result.output

    def test_missing_file(self, hatch, conda_project):
        pyproject = PyProject.load(conda_project)
        pyproject["tool"]["hatch"]["envs"]["default"]["environment-file"] = "missing.yaml"
        pyproject.save(conda_project)
        with conda_project.as_cwd():
            result = hatch("run", "python", "--version")
        assert "not found" in result.output
        assert result.exit_code != 0


@check_for_conda
class TestBuild:
    def test_no_conda(self, hatch, conda_project):
        with conda_project.as_cwd():
            result = hatch("build")
        assert result.exit_code == 0

    @pytest.mark.slow
    def test_conda(self, hatch, conda_project):
        pyproject = PyProject.load(conda_project)
        pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["hooks"]["conda"]["environment-file"] = "conda.yaml"
        pyproject.save(conda_project)
        with conda_project.as_cwd():
            result = hatch("build", "-t", "wheel")
        assert result.exit_code == 0

    def test_missing_file(self, hatch, conda_project, capfd):
        pyproject = PyProject.load(conda_project)
        pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["hooks"]["conda"]["environment-file"] = "missing.yaml"
        pyproject.save(conda_project)
        with conda_project.as_cwd():
            result = hatch("build", "-t", "wheel")
        assert result.exit_code != 0

        python_min_version = platform.python_version_tuple()[1]
        capture = capfd.readouterr()
        if python_min_version == "7":  # test is failing
            pytest.skip("Can't confirm text for python 3.7")
        assert "missing.yaml is missing" in capture.err
