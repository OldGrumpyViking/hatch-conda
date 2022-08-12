from textwrap import dedent as _dedent

import tomli
import tomli_w


def dedent(text):
    return _dedent(text[1:])


def update_project_environment(project, name, config):
    project_file = project.root / 'pyproject.toml'
    with open(str(project_file), 'r', encoding='utf-8') as f:
        raw_config = tomli.loads(f.read())

    env_config = raw_config.setdefault('tool', {}).setdefault('hatch', {}).setdefault('envs', {}).setdefault(name, {})
    env_config.update(config)

    project.config.envs[name] = project.config.envs.get(name, project.config.envs['default']).copy()
    project.config.envs[name].update(env_config)

    with open(str(project_file), 'w', encoding='utf-8') as f:
        f.write(tomli_w.dumps(raw_config))
