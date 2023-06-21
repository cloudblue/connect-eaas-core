import os
import tempfile
from pathlib import Path

import toml
from yaml import safe_load, scanner

from connect.eaas.core.deployment.helpers import (
    DEFAULT_CLONE_DIR,
    GitException,
    clone_repo,
    list_tags,
)


class DeploymentError(Exception):
    pass


def extract_arguments(url, is_install=False):
    with tempfile.TemporaryDirectory() as temp_path:
        try:
            clone_repo(temp_path, url)
        except GitException as ge:
            raise DeploymentError(ge)

        repo_path = Path(os.path.join(temp_path, DEFAULT_CLONE_DIR))
        try:
            with open(os.path.join(repo_path, '.connect_deployment.yaml'), 'r') as file_data:
                arguments = safe_load(file_data)

            if arguments.get('type') is None:
                with open(os.path.join(repo_path, 'pyproject.toml'), 'r') as pyprj_data:
                    content = toml.load(pyprj_data)
                apps = content['tool']['poetry']['plugins']['connect.eaas.ext']
                arguments['type'] = 'transformations' if 'tfnapp' in apps else 'multiaccount'

            if arguments.get('icon') and is_install:
                arguments['icon'] = open(os.path.join(repo_path, arguments.get('icon')), 'rb')

            return arguments
        except FileNotFoundError as fe:
            raise DeploymentError(f'No file: {fe}.')
        except OSError as e:
            raise DeploymentError(f'Error opening file: {e}')
        except scanner.ScannerError as se:
            raise DeploymentError(f'Invalid deployment file: {se}')
        except Exception as e:
            raise DeploymentError(f'Error extracting data: {e}')


def preprocess_variables(arguments):
    vars = arguments.get('var', {})
    for var_key, var in vars.items():
        if var is None:
            vars[var_key] = {'value': os.getenv(var_key), 'secure': False}
        else:
            vars[var_key]['value'] = var.get('value', os.getenv(var_key))
            vars[var_key]['secure'] = var.get('secure', False)

    return vars


def process_variables(arguments, env_api):
    vars = preprocess_variables(arguments)
    existing_vars = env_api.action('variables').get()
    existing_vars = {var['name']: var for var in existing_vars}

    for key, var in vars.items():
        if key in existing_vars:
            if (
                    var['value'] != existing_vars[key]['value']
                    or var['secure'] != existing_vars[key]['secure']
            ):
                env_api.variables[existing_vars[key]['id']].update(var)
        else:
            env_api.action('variables').post(
                {
                    'name': key,
                    'value': var['value'],
                    'secure': var['secure'],
                },
            )


def get_git_data(repo, tag):
    try:
        tags = list_tags(repo)
    except GitException as ge:
        raise DeploymentError(f'Cannot retrieve git repository {repo} tags info: {ge}.')

    tag = list(tags.keys())[0] if tag is None else str(tag)
    if tag not in tags:
        raise DeploymentError(f'Invalid tag: {tag}.')

    return {
        'tag': tag,
        'commit': tags[tag],
        'url': repo,
    }
