import itertools
import os

import requests
from connect.client import ConnectClient


PYPI_PACKAGE_URL = 'https://pypi.org/pypi/{package_name}/json'
CONNECT_API_URL = os.getenv(
    'CONNECT_API_URL',
    'https://api.connect.cloudblue.com/public/v1',
)

CONNECT_UI_TOOLKIT_URL = (
    'https://raw.githubusercontent.com/cloudblue/connect-ui-toolkit/master/README.md'
)


def get_events(extension_type):  # noqa: CCR001
    api_key = os.getenv('CONNECT_API_KEY')

    if os.getenv('READTHEDOCS'):
        api_key = api_key[1:-1]

    client = ConnectClient(
        api_key,
        endpoint=CONNECT_API_URL,
    )

    definitions = sorted(
        client.ns('devops').collection('event-definitions').filter(
            extension_type=extension_type,
        ),
        key=lambda x: x['group'],
    )

    lines = []

    for group, events in itertools.groupby(definitions, key=lambda x: x['group']):

        lines.extend([f'### {group}', ''])

        events = sorted(events, key=lambda x: x['category'])

        for category, defs in itertools.groupby(events, key=lambda x: x['category']):
            lines.extend(
                [
                    f'#### {category}',
                    '',
                ],
            )

            lines.extend(
                [
                    '|Name|Description|Type|Statuses|',
                    '|:---|:----------|:--:|:------:|',
                ],
            )

            for definition in defs:
                lines.append(
                    f'|{definition["name"]}|'
                    f'{definition["description"]}|'
                    f'{definition["type"]}|'
                    f'{", ".join(definition["object_statuses"])}|',
                )
            lines.extend(['', ''])
        lines.extend(['', ''])

    return '\n'.join(lines)


def get_connect_major_version():
    res = requests.get(CONNECT_API_URL)
    version = res.headers['Connect-Version']
    major, _ = version.split('.', 1)
    return major


def get_pypi_version(package_name):
    major_version = get_connect_major_version()
    res = requests.get(PYPI_PACKAGE_URL.format(package_name=package_name))
    content = res.json()
    tags = [
        int(version.split('.')[1])
        for version in content['releases'] if version.startswith(f'{major_version}.')
    ]
    if tags:
        return f'{major_version}.{str(max(tags))}'
    return content['info']['version']


def get_ui_toolkit_readme():
    res = requests.get(CONNECT_UI_TOOLKIT_URL)
    lines = res.content.decode().splitlines()
    for idx, line in enumerate(lines):
        if line.startswith('## Usage'):
            return '\n'.join(lines[idx:])
    return ''


def define_env(env):
    @env.macro
    def runner_version():
        return get_pypi_version('connect-extension-runner')

    @env.macro
    def core_version():
        return get_pypi_version('connect-eaas-core')

    @env.macro
    def current_major():
        return get_connect_major_version()

    @env.macro
    def next_major():
        return str(int(get_connect_major_version()) + 1)

    @env.macro
    def products_events():
        return get_events('products')

    @env.macro
    def hub_events():
        return get_events('hub')

    @env.macro
    def multiaccount_events():
        return get_events('multiaccount')

    @env.macro
    def ui_toolkit_docs():
        return get_ui_toolkit_readme()
