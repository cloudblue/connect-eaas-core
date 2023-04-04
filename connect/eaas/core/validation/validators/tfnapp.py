import inspect
import os

from connect.eaas.core.extension import TransformationsApplicationBase
from connect.eaas.core.validation.helpers import get_code_context
from connect.eaas.core.validation.models import ValidationItem, ValidationResult


def validate_tfnapp(context):  # noqa: CCR001
    messages = []

    if 'tfnapp' not in context['extension_classes']:
        return ValidationResult()

    extension_class = context['extension_classes']['tfnapp']
    extension_class_file = inspect.getsourcefile(extension_class)

    if not issubclass(extension_class, TransformationsApplicationBase):
        messages.append(
            ValidationItem(
                level='ERROR',
                message=(
                    f'The application class *{extension_class.__name__}* '
                    f'is not a subclass of '
                    f'*connect.eaas.core.extension.TransformationsApplicationBase*.'
                ),
                file=extension_class_file,
            ),
        )
        return ValidationResult(items=messages, must_exit=True)

    transformations = extension_class.get_transformations()
    for tfn in transformations:
        if not isinstance(tfn['name'], str) or not tfn['name']:
            messages.append(
                ValidationItem(
                    level='ERROR',
                    message=(
                        f'The name of the {tfn["method"]} must be a non-blank string.'
                    ),
                    **get_code_context(extension_class, tfn['method']),
                ),
            )
        if not isinstance(tfn['description'], str) or not tfn['description']:
            messages.append(
                ValidationItem(
                    level='ERROR',
                    message=(
                        f'The description of the {tfn["method"]} must be a non-blank string.'
                    ),
                    **get_code_context(extension_class, tfn['method']),
                ),
            )

        edit_dialog_ui = tfn['edit_dialog_ui']
        if (
            not isinstance(edit_dialog_ui, str)
            or not edit_dialog_ui
            or not edit_dialog_ui.startswith('/static/')
        ):
            messages.append(
                ValidationItem(
                    level='ERROR',
                    message=(
                        f'The url {edit_dialog_ui} of the {tfn["method"]} '
                        f'must be not empty string and prefixed with /static.'
                    ),
                    **get_code_context(extension_class, tfn['method']),
                ),
            )
        else:
            full_path = os.path.join(
                os.path.dirname(inspect.getsourcefile(extension_class)),
                'static',
                edit_dialog_ui[8:],
            )
            if not os.path.exists(full_path):
                messages.append(
                    ValidationItem(
                        level='ERROR',
                        message=(
                            f'The url {edit_dialog_ui} of the {tfn["method"]} '
                            f'does not point to any file.'
                        ),
                        **get_code_context(extension_class, tfn['method']),
                    ),
                )

    return ValidationResult(items=messages)
