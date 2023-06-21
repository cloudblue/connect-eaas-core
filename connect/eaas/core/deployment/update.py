import time

from connect.client import ClientError
from connect.eaas.core.deployment.utils import extract_arguments, get_git_data, process_variables


def update_extension(repo, client, log):
    log('Starting update...')

    log('Extracting data from connect_deployment.yaml.')
    arguments, error = extract_arguments(repo)
    if error:
        log(error.message)
        return
    if not arguments.get('package_id'):
        log('No required package_id found in .connect_deployment.yaml file.')
        return

    log('Getting repository tag.')
    git, error = get_git_data(repo, arguments.get('tag'))
    if error:
        log(error.message)
        return

    try:
        log('Getting extension information.')
        extension = client('devops').services.filter(package_id=arguments['package_id']).first()
    except ClientError as ce:
        log(f'Error getting extension: {ce}')
        return

    if extension is None:
        log(f'Extension with package_id {arguments["package_id"]} doesn\'t exist.')
        return

    try:
        environment = extension['environments'][arguments.get('env', 'production')]
        env_api = client('devops').services[extension['id']].environments[environment['id']]
        if environment['status'] == 'running':
            log('Stopping running environment')
            env_api.action('stop').post()

            elapsed = 0
            while elapsed < 5:
                if env_api.get()['status'] not in ['stopped', 'errored']:
                    log(f'Environment is not stopped: wait 1s more, elapsed {elapsed}s')
                    time.sleep(1)
                    elapsed += 1
                    continue

                break
            else:
                log('Environment hasn\'t stopped in maximum wait time, please run update again.')
                return

        log('Updating variables.')
        process_variables(arguments, env_api)

        log('Updating and starting environment.')
        env_api.update({'git': git, 'runtime': 'cloud'})
        if environment['runtime'] == 'cloud':
            env_api.action('start').post()
    except ClientError as ce:
        log(f'Error processing environment: {ce}.')
        return

    log('Extension successfully updated.')
