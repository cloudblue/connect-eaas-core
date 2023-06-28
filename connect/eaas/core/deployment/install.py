from connect.client import ClientError
from connect.eaas.core.deployment.utils import (
    DeploymentError,
    extract_arguments,
    get_git_data,
    process_variables,
)


def install_extension(repo, client, log, tag=None):
    log('Starting install...')

    log('Extracting data from connect_deployment.yaml.')
    try:
        arguments = extract_arguments(repo, is_install=True)
    except DeploymentError as de:
        log(de)
        return

    if not arguments.get('package_id'):
        log('No required package_id found in .connect_deployment.yaml file.')
        return
    arguments['name'] = arguments.get('name') or f'Extension for {arguments["package_id"]}'

    log('Getting repository tag.')
    try:
        git = get_git_data(repo, tag, arguments.get('tag'))
    except DeploymentError as de:
        log(de)
        return

    category_id = None
    if arguments.get('category'):
        try:
            category = client.dictionary['extensions'].categories.filter(
                name=arguments.get('category'),
            ).first()
            if category:
                category_id = {'id': category['id']}
        except ClientError as ce:
            log(f'Error during looking up category: {ce}. Skip it.')

    try:
        log('Creating extension instance.')
        extension = client('devops').services.create(
            data={
                'type': arguments['type'],
                'name': arguments['name'],
                'package_id': arguments['package_id'],
                'category': category_id,
                'short_description': arguments.get('description'),
                'overview': arguments.get('overview'),
                'website': arguments.get('website'),
            },
            files={'icon': arguments.get('icon')},
        )
    except ClientError as ce:
        log(f'Error creating extension: {ce}.')
        return
    finally:
        if arguments.get('icon'):
            arguments['icon'].close()

    environment = extension['environments'][arguments.get('env', 'production')]
    env_api = client('devops').services[extension['id']].environments[environment['id']]
    try:
        log('Creating variables.')
        process_variables(arguments, env_api)

        log('Updating and starting environment.')
        env_api.update({'git': git, 'runtime': 'cloud'})
    except ClientError as ce:
        log(f'Error processing environment: {ce}.')
        return

    log('Extension successfully installed.')
