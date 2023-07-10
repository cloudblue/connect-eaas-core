from connect.client import ClientError
from connect.eaas.core.deployment.utils import (
    DeploymentError,
    create_extension,
    extract_arguments,
    get_git_data,
    process_variables,
    stop_environment,
    update_extension,
)


def deploy_extension(repo, client, log, tag=None):
    log(f'Starting deploy repo {repo}...')

    try:
        log('Getting tags information.')
        git = get_git_data(repo, tag)
        log(f'Tag {git["tag"]} is set.')

        log('Extracting data from deployment file.')
        arguments = extract_arguments(repo, git['tag'])
    except DeploymentError as de:
        log(de)
        return

    if not arguments.get('package_id'):
        log('No required package_id found.')
        return
    arguments['name'] = arguments.get('name') or f'Extension for {arguments["package_id"]}'

    try:
        log(f'Looking up for extension with package_id {arguments["package_id"]}.')
        extension = client('devops').services.filter(package_id=arguments['package_id']).first()
    except ClientError as ce:
        log(f'Error getting extension: {ce}')
        return

    log(
        (
            f'Extension with package_id {arguments["package_id"]} '
            f'does{"" if extension else " not"} exist, '
            f'{"updating" if extension else "creating"} it.'
        ),
    )
    is_install = extension is None

    if is_install:
        extension = create_extension(client, arguments, log)
    else:
        extension = update_extension(client, extension, arguments, log)

    if arguments.get('icon'):
        arguments['icon'].close()
    if extension is None:
        return

    environment = extension['environments'][arguments.get('env', 'production')]
    env_api = client('devops').services[extension['id']].environments[environment['id']]

    environment = stop_environment(environment, env_api, log)
    if environment['status'] == 'running':
        return

    try:
        log(f'Creating variables for extension with package_id {arguments["package_id"]}.')
        process_variables(arguments, env_api)

        log(f'Updating and starting {environment["type"]} environment.')
        env_api.update({'git': git, 'runtime': 'cloud'})

        if environment['runtime'] == 'cloud':
            env_api.action('start').post()
    except ClientError as ce:
        log(f'Error processing environment: {ce}.')
        return

    log(f'Extension with package_id {arguments["package_id"]} successfully deployed.')
