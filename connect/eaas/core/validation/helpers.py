import inspect
import os

import toml

from connect.eaas.core.validation.proto import ValidationItem, ValidationResult


def get_event_definitions(client):
    return list(client('devops').event_definitions.all())


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
                    level='ERROR',
                    message=(
                        'The mandatory *pyproject.toml* project '
                        f'descriptor file is not present in the folder {path}.'
                    ),
                    file=descriptor_file,
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
                    level='ERROR',
                    message=(
                        'The project descriptor file *pyproject.toml* is '
                        'not a valid toml file.'
                    ),
                    file=descriptor_file,
                ),
            ],
            must_exit=True,
        )
