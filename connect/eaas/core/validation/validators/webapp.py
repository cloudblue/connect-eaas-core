import inspect
import os

from fastapi_utils.cbv import CBV_CLASS_KEY

from connect.eaas.core.extension import WebAppExtension
from connect.eaas.core.validation.helpers import get_code_context
from connect.eaas.core.validation.models import ValidationItem, ValidationResult


def validate_webapp(context):  # noqa: CCR001

    messages = []

    if 'webapp' not in context['extension_classes']:
        return ValidationResult()

    extension_class = context['extension_classes']['webapp']

    extension_class_file = inspect.getsourcefile(extension_class)

    if not issubclass(extension_class, WebAppExtension):
        messages.append(
            ValidationItem(
                level='ERROR',
                message=(
                    f'The extension class *{extension_class.__name__}* '
                    f'is not a subclass of *connect.eaas.core.extension.WebAppExtension*.'
                ),
                file=extension_class_file,
            ),
        )
        return ValidationResult(items=messages, must_exit=True)

    if not getattr(extension_class, CBV_CLASS_KEY, False):
        messages.append(
            ValidationItem(
                level='ERROR',
                message='The Web app extension class must be wrapped in *@web_app(router)*.',
                file=extension_class_file,
            ),
        )
        return ValidationResult(items=messages, must_exit=True)

    messages.extend(_validate_webapp_routes(context))
    messages.extend(_validate_webapp_ui_modules(context))
    return ValidationResult(items=messages, must_exit=len(messages) > 0)


def _validate_webapp_routes(context):
    extension_class = context['extension_classes']['webapp']
    extension_class_file = inspect.getsourcefile(extension_class)

    auth, no_auth = extension_class.get_routers()

    no_of_routes = len(auth.routes) + len(no_auth.routes)

    if no_of_routes == 0:
        return [
            ValidationItem(
                level='ERROR',
                message=(
                    'The Web app extension class must contain at least one route '
                    'implementation function wrapped in *@router.your_method("/your_path")*.'
                ),
                file=extension_class_file,
            ),
        ]
    return []


def _check_ui_component_label(extension_class, page_name, value, code_pattern):
    if not isinstance(value, str) or not value:
        return [
            ValidationItem(
                level='ERROR',
                message=(
                    f'The label of the {page_name} must be a non-blank string.'
                ),
                **get_code_context(extension_class, code_pattern),
            ),
        ]
    return []


def _check_ui_component_url(extension_class, page_name, value, code_pattern):
    if not isinstance(value, str) or not value:
        return [
            ValidationItem(
                level='ERROR',
                message=(
                    f'The url of the {page_name} must be a '
                    'path to a html file relative to the static folder.'
                ),
                **get_code_context(extension_class, code_pattern),
            ),
        ]

    if not value.startswith('/static/'):
        return [
            ValidationItem(
                level='ERROR',
                message=(
                    f'The url {value} of the {page_name} must be prefixed with /static.'
                ),
                **get_code_context(extension_class, code_pattern),
            ),
        ]

    page_path = value[8:]
    full_path = os.path.join(
        os.path.dirname(inspect.getsourcefile(extension_class)),
        'static_root',
        page_path,
    )
    if not os.path.exists(full_path):
        return [
            ValidationItem(
                level='ERROR',
                message=(
                    f'The url {value} of the {page_name} page does not point to any file.'
                ),
                **get_code_context(extension_class, code_pattern),
            ),
        ]
    return []


def _validate_webapp_ui_modules(context):  # noqa: CCR001
    messages = []
    extension_class = context['extension_classes']['webapp']

    ui_modules = extension_class.get_ui_modules()

    if 'settings' in ui_modules:
        label = ui_modules['settings']['label']
        url = ui_modules['settings']['url']

        messages.extend(
            _check_ui_component_label(
                extension_class, '"Account Settings"', label, '@account_settings_page(',
            ),
        )

        messages.extend(
            _check_ui_component_url(
                extension_class, '"Account Settings"', url, '@account_settings_page(',
            ),
        )

    if 'modules' in ui_modules:
        label = ui_modules['modules']['label']
        url = ui_modules['modules']['url']
        messages.extend(
            _check_ui_component_label(
                extension_class, '"Module Main Page"', label, '@module_pages(',
            ),
        )
        messages.extend(
            _check_ui_component_url(
                extension_class, '"Module Main Page"', url, '@module_pages(',
            ),
        )

        if 'children' in ui_modules['modules']:
            children = ui_modules['modules']['children']
            if not isinstance(children, (list, tuple)):
                messages.append(
                    ValidationItem(
                        level='ERROR',
                        message=(
                            'The "children" argument of the @module_pages '
                            'decorator must be a list of objects.'
                        ),
                        **get_code_context(extension_class, '@module_pages('),
                    ),
                )
            else:
                for child in children:
                    if 'label' not in child or 'url' not in child:
                        messages.append(
                            ValidationItem(
                                level='ERROR',
                                message=(
                                    'Invalid child page declaration. '
                                    'Each child page must be an object with the '
                                    'label and url attributes.'
                                ),
                                **get_code_context(extension_class, '@module_pages('),
                            ),
                        )
                        continue

                    label = child['label']
                    url = child['url']
                    messages.extend(
                        _check_ui_component_label(
                            extension_class, '"Module Child Page"', label, '@module_pages(',
                        ),
                    )
                    messages.extend(
                        _check_ui_component_url(
                            extension_class, '"Module Child Page"', url, '@module_pages(',
                        ),
                    )

    if 'admins' in ui_modules:
        admins = ui_modules['admins']
        if not isinstance(admins, (list, tuple)):
            messages.append(
                ValidationItem(
                    level='ERROR',
                    message=(
                        'The argument of the @admin_pages '
                        'decorator must be a list of objects.'
                    ),
                    **get_code_context(extension_class, '@admin_pages('),
                ),
            )
        else:
            for child in admins:
                if 'label' not in child or 'url' not in child:
                    messages.append(
                        ValidationItem(
                            level='ERROR',
                            message=(
                                'Invalid admin page declaration. '
                                'Each admin page must be an object with the '
                                'label and url attributes.'
                            ),
                            **get_code_context(extension_class, '@admin_pages('),
                        ),
                    )
                    continue

                label = child['label']
                url = child['url']
                messages.extend(
                    _check_ui_component_label(
                        extension_class, '"Admin Page"', label, '@admin_pages(',
                    ),
                )
                messages.extend(
                    _check_ui_component_url(
                        extension_class, '"Admin Page"', url, '@admin_pages(',
                    ),
                )

    return messages
