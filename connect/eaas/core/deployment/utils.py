import os
import tempfile
import time
from pathlib import Path

import toml
from yaml import safe_load, scanner

from connect.client import ClientError
from connect.eaas.core.deployment.helpers import (
    DEFAULT_CLONE_DIR,
    GitException,
    clone_repo,
    list_tags,
)


class DeploymentError(Exception):
    pass


def extract_arguments(url, tag):  # noqa: CCR001
    with tempfile.TemporaryDirectory() as temp_path:
        try:
            clone_repo(temp_path, url, tag)
        except GitException as ge:
            raise DeploymentError(ge)

        repo_path = Path(os.path.join(temp_path, DEFAULT_CLONE_DIR))
        file_path = os.path.join(repo_path, 'connect-deployment.yaml')
        if not os.path.exists(file_path):
            file_path = os.path.join(repo_path, 'connect-deployment.yml')
        if not os.path.exists(file_path):
            raise DeploymentError(
                (
                    'Deployment file is not found. Please, check, that file with name '
                    'connect-deployment.yaml or connect-deployment.yml exists and '
                    'is located in root project directory.'
                ),
            )
        try:
            with open(file_path, 'r') as file_data:
                arguments = safe_load(file_data)

            if arguments.get('type') is None:
                with open(os.path.join(repo_path, 'pyproject.toml'), 'r') as pyprj_data:
                    content = toml.load(pyprj_data)
                apps = content['tool']['poetry']['plugins']['connect.eaas.ext']
                arguments['type'] = 'transformations' if 'tfnapp' in apps else 'multiaccount'

            if arguments.get('icon'):
                arguments['icon'] = open(os.path.join(repo_path, arguments.get('icon')), 'rb')

            if arguments.get('overview'):
                if os.path.exists(os.path.join(repo_path, arguments['overview'])):
                    with open(os.path.join(repo_path, arguments['overview']), 'r') as overview:
                        arguments['overview'] = overview.read()
                else:
                    arguments['overview'] = None

            return arguments
        except OSError as e:
            raise DeploymentError(f'Error opening file: {e}')
        except scanner.ScannerError as se:
            raise DeploymentError(f'Invalid deployment file: {se}')
        except Exception as e:
            raise DeploymentError(f'Error extracting data: {e}')


def preprocess_variables(arguments):
    vars = arguments.get('var', {})
    for var_key, var in vars.items():
        var = var or {}
        if not var.get('value'):
            var['value'] = os.getenv(var_key)
        if not isinstance(var.get('secure'), bool):
            var['secure'] = False
        vars[var_key] = var

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

    if tag is None:
        tag = list(tags.keys())[0]
    elif tag not in tags:
        raise DeploymentError(
            f'Tag {tag} doesn\'t exist, please, select one of: {", ".join(tags.keys())}.',
        )

    return {
        'tag': tag,
        'commit': tags[tag],
        'url': repo,
    }


def get_category(client, arguments, log):
    category_id = None
    if arguments.get('category'):
        log(f'Looking for a category {arguments["category"]}.')
        try:
            category = client.dictionary['extensions'].categories.filter(
                name=arguments.get('category'),
            ).first()
            if category:
                category_id = {'id': category['id']}
            log(f'Category {arguments["category"]} was{"" if category else " not"} found.')
        except ClientError as ce:
            log(f'Error during looking up category: {ce}. Skip it.')

    return category_id


def create_extension(client, arguments, log):
    payload = {
        'type': arguments['type'],
        'name': arguments['name'],
        'package_id': arguments['package_id'],
        'category': get_category(client, arguments, log),
        'short_description': arguments.get('description'),
        'overview': arguments.get('overview'),
        'website': arguments.get('website'),
    }

    try:
        log(f'Creating extension {arguments["package_id"]}.')
        extension = client('devops').services.create(payload=payload)

        if arguments.get('icon'):
            log(f'Setting icon for extension {arguments["package_id"]} instance.')
            extension = client('devops').services[extension['id']].update(
                files={'icon': arguments.get('icon')},
            )

        return extension
    except ClientError as ce:
        log(f'Error creating extension: {ce}.')
        return None


def update_extension(client, extension, arguments, log):
    payload = {
        'category': get_category(client, arguments, log),
        'short_description': arguments.get('description'),
        'overview': arguments.get('overview'),
        'website': arguments.get('website'),
    }

    try:
        log(f'Updating extension {arguments["package_id"]}.')
        extension = client('devops').services[extension['id']].update(payload=payload)
        return extension
    except ClientError as ce:
        log(f'Error updating extension: {ce}.')
        return None


def stop_environment(environment, env_api, log):
    if environment['status'] != 'running':
        return environment

    try:
        log(f'{environment["type"]} environment is running. Ready to stop it.')
        env_api.action('stop').post()

        elapsed = 0
        while elapsed < 5:
            environment = env_api.get()
            if environment['status'] not in ['stopped', 'errored']:
                log(f'Environment is not stopped: wait 1s more, elapsed {elapsed}s')
                time.sleep(1)
                elapsed += 1
                continue
            break
        else:
            log('Environment hasn\'t stopped in maximum wait time, please run deploy again.')
    except ClientError as ce:
        log(f'Error stopping {environment["type"]} environment: {ce}')

    return environment
