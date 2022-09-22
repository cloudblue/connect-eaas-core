import inspect
import os

import toml
from click import ClickException

from connect.client import ClientError
from connect.eaas.core.proto import ValidationItem, ValidationResult


def get_event_definitions(config):
    try:
        return list(config.active.client('devops').event_definitions.all())
    except ClientError as err:
        raise ClickException(f"Error getting event definitions: {str(err)}")


def get_code_context(obj, pattern):
    source_lines = inspect.getsourcelines(obj)
    file = inspect.getsourcefile(obj)
    start_line = source_lines[1]
    lineno = source_lines[1]
    code = ''.join(source_lines[0])

    for idx, line in enumerate(source_lines[0]):  # pragma: no branch
        if pattern in line:
            lineno += idx
            break

    if inspect.ismodule(obj):
        code = ''.join(code.splitlines(keepends=True)[0:lineno + 3])

    return {
        'file': file,
        'start_line': start_line,
        'lineno': lineno,
        'code': code,
    }


def load_project_toml_file(path):
    descriptor_file = os.path.join(path, 'pyproject.toml')
    if not os.path.isfile(descriptor_file):
        return ValidationResult(
            items=[
                ValidationItem(
                    'ERROR',
                    (
                        'The mandatory *pyproject.toml* project '
                        f'descriptor file is not present in the folder {path}.'
                    ),
                    descriptor_file,
                ),
            ],
            must_exit=True,
        )
    try:
        return toml.load(descriptor_file)
    except toml.TomlDecodeError:
        return ValidationResult(
            items=[
                ValidationItem(
                    'ERROR',
                    'The project descriptor file *pyproject.toml* is not a valid toml file.',
                    descriptor_file,
                ),
            ],
            must_exit=True,
        )
