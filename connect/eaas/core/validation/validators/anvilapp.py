import inspect
import re

from connect.eaas.core.constants import ANVIL_CALLABLE_ATTR_NAME
from connect.eaas.core.extension import AnvilExtension
from connect.eaas.core.validation.models import ValidationItem, ValidationResult


def validate_anvilapp(context):

    messages = []

    if 'anvil' not in context['extension_classes']:
        return ValidationResult()

    extension_class = context['extension_classes']['anvil']
    extension_class_file = inspect.getsourcefile(extension_class)

    if not issubclass(extension_class, AnvilExtension):
        messages.append(
            ValidationItem(
                level='ERROR',
                message=(
                    f'The extension class *{extension_class.__name__}* '
                    f'is not a subclass of *connect.eaas.core.extension.AnvilExtension*.'
                ),
                file=extension_class_file,
            ),
        )
        return ValidationResult(items=messages, must_exit=True)

    anvil_key_var = extension_class.get_anvil_key_variable()

    if anvil_key_var:
        variable_name_pattern = r'^[A-Za-z](?:[A-Za-z0-9_\-.]+)*$'
        variable_name_regex = re.compile(variable_name_pattern)

        if not variable_name_regex.match(anvil_key_var):
            messages.append(
                ValidationItem(
                    level='ERROR',
                    message=(
                        f'Invalid Anvil key variable name: the value *{anvil_key_var}* '
                        f'does not match the pattern *{variable_name_pattern}*.'
                    ),
                    file=extension_class_file,
                ),
            )

    has_callables = False
    for _, value in inspect.getmembers(extension_class):
        if hasattr(value, ANVIL_CALLABLE_ATTR_NAME):
            has_callables = True
            break

    if not has_callables:
        messages.append(
            ValidationItem(
                level='ERROR',
                message=(
                    'The Anvil app extension class must contain at least one callable '
                    'marked with the *@anvil_callable* decorator.'
                ),
                file=extension_class_file,
            ),
        )
    return ValidationResult(items=messages, must_exit=len(messages) > 0)
