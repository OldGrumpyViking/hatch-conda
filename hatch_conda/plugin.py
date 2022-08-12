from __future__ import annotations

import sys
from contextlib import contextmanager

from hatch.env.plugin.interface import EnvironmentInterface


class CondaEnvironment(EnvironmentInterface):
    PLUGIN_NAME = 'conda'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__python_version = None

        self.conda_env_name = f'{self.metadata.core.name}_{self.name}_{self.python_version}'
        self.project_path = '.'

    @staticmethod
    def get_option_types():
        return {}

    @property
    def python_version(self):
        if self.__python_version is None:
            python_version = self.config.get('python', '')
            if not python_version:
                python_version = '.'.join(map(str, sys.version_info[:2]))
            elif python_version.isdigit() and len(python_version) > 1:
                python_version = f'{python_version[0]}.{python_version[1:]}'

            self.__python_version = python_version

        return self.__python_version

    def activate(self):
        self.platform.check_command_output(['conda', 'activate', self.conda_env_name])

    def deactivate(self):
        self.platform.check_command_output(['conda', 'deactivate'])

    def find(self):
        return self.conda_env_name

    def create(self):
        command = [
            'conda',
            'create',
            '-y',
            '-n',
            self.conda_env_name,
            '-c',
            'conda-forge',
            '--no-channel-priority',
            f'python={self.python_version}',
            'pip',
        ]
        if self.verbosity > 0:  # no cov
            self.platform.check_command(command)
        else:
            self.platform.check_command_output(command)

    def remove(self):
        self.platform.check_command_output(['conda', 'env', 'remove', '--name', self.conda_env_name])

    def exists(self):
        output = self.platform.check_command_output(['conda', 'env', 'list'])

        return any(line.split(' ')[0] == self.conda_env_name for line in output.splitlines())

    def construct_pip_install_command(self, *args, **kwargs):
        return ['conda', 'run', '-n', self.conda_env_name] + super().construct_pip_install_command(*args, **kwargs)

    def install_project(self):
        with self:
            self.platform.check_command(self.construct_pip_install_command([self.apply_features(self.project_path)]))

    def install_project_dev_mode(self):
        with self:
            self.platform.check_command(
                self.construct_pip_install_command(['--editable', self.apply_features(self.project_path)])
            )

    def dependencies_in_sync(self):
        if not self.dependencies:
            return True

        with self:
            process = self.platform.run_command(
                ' '.join(['hatchling', 'dep', 'synced', '-p', 'python', *self.dependencies]),
                capture_output=True,
            )
            return not process.returncode

    def sync_dependencies(self):
        with self:
            self.platform.check_command(self.construct_pip_install_command(self.dependencies))

    @contextmanager
    def command_context(self):
        with self:
            yield

    def run_shell_command(self, command):
        return self.platform.run_command(' '.join(['conda', 'run', '-n', self.conda_env_name]) + ' ' + command)

    def enter_shell(self, name, path, args):  # no cov
        with self:
            process = self.platform.run_command(' '.join(['conda', 'activate', self.conda_env_name]))
            self.platform.exit_with_code(process.returncode)
