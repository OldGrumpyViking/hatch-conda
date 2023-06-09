from hatch.project.core import Project

from hatch_conda.plugin import CondaEnvironment


class TestPythonVersion:
    def test_default(self, isolation, data_dir, platform, default_python_version):
        env_config = {}
        project = Project(
            isolation,
            config={
                'project': {'name': 'my_app', 'version': '0.0.1'},
                'tool': {'hatch': {'envs': {'default': env_config}}},
            },
        )
        environment = CondaEnvironment(
            root=isolation,
            metadata=project.metadata,
            name='default',
            config=project.config.envs['default'],
            matrix_variables={},
            data_directory=data_dir,
            isolated_data_directory=None,
            platform=platform,
            verbosity=0,
        )

        assert environment.python_version == default_python_version

    def test_long(self, isolation, data_dir, platform):
        env_config = {'python': '3.10'}
        project = Project(
            isolation,
            config={
                'project': {'name': 'my_app', 'version': '0.0.1'},
                'tool': {'hatch': {'envs': {'default': env_config}}},
            },
        )
        environment = CondaEnvironment(
            root=isolation,
            metadata=project.metadata,
            name='default',
            config=project.config.envs['default'],
            matrix_variables={},
            data_directory=data_dir,
            isolated_data_directory=None,
            platform=platform,
            verbosity=0,
        )

        assert environment.python_version == '3.10'

    def test_short(self, isolation, data_dir, platform):
        env_config = {'python': '310'}
        project = Project(
            isolation,
            config={
                'project': {'name': 'my_app', 'version': '0.0.1'},
                'tool': {'hatch': {'envs': {'default': env_config}}},
            },
        )

        environment = CondaEnvironment(
            root=isolation,
            metadata=project.metadata,
            name='default',
            config=project.config.envs['default'],
            matrix_variables={},
            data_directory=data_dir,
            isolated_data_directory=None,
            platform=platform,
            verbosity=0,
        )

        assert environment.python_version == '3.10'
