#
# Copyright (c) 2023 Ingram Micro. All Rights Reserved.
#

import inspect
import os

from fastapi_utils.cbv import CBV_CLASS_KEY

from connect.eaas.core.constants import (
    PROXIED_CONNECT_API_ALLOWED_PREFIXES,
    PROXIED_CONNECT_API_ENDPOINTS_MAX_ALLOWED_NUMBER,
)
from connect.eaas.core.extension import WebApplicationBase
from connect.eaas.core.validation.helpers import get_code_context
from connect.eaas.core.validation.models import ValidationItem, ValidationResult


def validate_webapp(context):  # noqa: CCR001

    messages = []

    if 'webapp' not in context['extension_classes']:
        return ValidationResult()

    extension_class = _get_extension_class(context)
    extension_class_file = _get_extension_class_file(extension_class)

    if not issubclass(extension_class, WebApplicationBase):
        messages.append(
            ValidationItem(
                level='ERROR',
                message=(
                    f'The application class *{extension_class.__name__}* '
                    f'is not a subclass of *connect.eaas.core.extension.WebApplicationBase*.'
                ),
                file=extension_class_file,
            ),
        )
        return ValidationResult(items=messages, must_exit=True)

    if not getattr(extension_class, CBV_CLASS_KEY, False):
        messages.append(
            ValidationItem(
                level='ERROR',
                message='The Web application class must be wrapped in *@web_app(router)*.',
                file=extension_class_file,
            ),
        )
        return ValidationResult(items=messages, must_exit=True)

    validators = [
        _validate_webapp_exception_handling,
        _validate_webapp_middlewares,
        _validate_webapp_routes,
        _validate_webapp_ui_modules,
        _validate_webapp_proxied_connect_api,
    ]
    for validator in validators:
        messages.extend(validator(context))

    return ValidationResult(items=messages, must_exit=len(messages) > 0)


def _validate_webapp_exception_handling(context):
    errors = []

    extension_class = _get_extension_class(context)
    if not hasattr(extension_class, 'get_exception_handlers'):
        return errors

    extension_class_file = _get_extension_class_file(extension_class)
    try:
        exceptions_dict = extension_class.get_exception_handlers({})
        if not isinstance(exceptions_dict, dict):
            errors.append(
                ValidationItem(
                    level='ERROR',
                    message=(
                        'Invalid implementation of `get_exception_handlers` in Web Application: '
                        'returned value must be a dictionary.'
                    ),
                    file=extension_class_file,
                ),
            )
            return errors

        if not all(issubclass(k, BaseException) for k in exceptions_dict.keys()):
            errors.append(
                ValidationItem(
                    level='ERROR',
                    message=(
                        'Invalid implementation of `get_exception_handlers` in Web Application: all'
                        ' configuration keys must Exception classes, inherited from BaseException.'
                    ),
                    file=extension_class_file,
                ),
            )
            return errors

        return errors

    except TypeError:
        errors.append(
            ValidationItem(
                level='ERROR',
                message='Invalid declaration of `get_exception_handlers` in Web Application.',
                file=extension_class_file,
            ),
        )
        return errors


def _validate_webapp_middlewares(context):
    errors = []

    extension_class = _get_extension_class(context)
    if not hasattr(extension_class, 'get_middlewares'):
        return errors

    extension_class_file = _get_extension_class_file(extension_class)
    try:
        middlewares_list = extension_class.get_middlewares()
        if not isinstance(middlewares_list, list):
            errors.append(
                ValidationItem(
                    level='ERROR',
                    message=(
                        'Invalid implementation of `get_middlewares` in Web Application: '
                        'returned value must be a list.'
                    ),
                    file=extension_class_file,
                ),
            )
            return errors

        return errors

    except TypeError:
        errors.append(
            ValidationItem(
                level='ERROR',
                message='Invalid declaration of `get_middlewares` in Web Application.',
                file=extension_class_file,
            ),
        )
        return errors


def _validate_webapp_proxied_connect_api(context):
    errors = []

    extension_class = _get_extension_class(context)
    proxied_connect_api = extension_class.get_proxied_connect_api()
    code_pattern = '@proxied_connect_api('

    type_msg = 'The argument of the `@proxied_connect_api` must be a list of strings or a dict.'
    if not isinstance(proxied_connect_api, (list, dict)):
        errors.append(
            ValidationItem(
                level='ERROR',
                message=type_msg,
                **get_code_context(extension_class, code_pattern),
            ),
        )
        return errors

    if not proxied_connect_api:
        return errors

    max_length = PROXIED_CONNECT_API_ENDPOINTS_MAX_ALLOWED_NUMBER
    if len(proxied_connect_api) > max_length:
        errors.append(
            ValidationItem(
                level='ERROR',
                message=f'Max allowed length of the `@proxied_connect_api` argument: {max_length}.',
                **get_code_context(extension_class, code_pattern),
            ),
        )
        return errors

    is_dict_conf = isinstance(proxied_connect_api, dict)
    api_paths = proxied_connect_api
    if is_dict_conf:
        api_paths = proxied_connect_api.keys()
    if not all(isinstance(v, str) for v in api_paths):
        errors.append(
            ValidationItem(
                level='ERROR',
                message=type_msg,
                **get_code_context(extension_class, code_pattern),
            ),
        )
        return errors

    allowed_prefixes = PROXIED_CONNECT_API_ALLOWED_PREFIXES
    if not all(v.startswith(allowed_prefixes) for v in api_paths):
        errors.append(
            ValidationItem(
                level='ERROR',
                message='Only Public or Files API can be referenced in `@proxied_connect_api`.',
                **get_code_context(extension_class, code_pattern),
            ),
        )
        return errors

    if is_dict_conf and (
        not all(isinstance(v, str) and v in ('view', 'edit') for v in proxied_connect_api.values())
    ):
        errors.append(
            ValidationItem(
                level='ERROR',
                message='Wrong Public API permission value in `@proxied_connect_api`.',
                **get_code_context(extension_class, code_pattern),
            ),
        )
        return errors

    return errors


def _validate_webapp_routes(context):
    extension_class = _get_extension_class(context)
    extension_class_file = _get_extension_class_file(extension_class)

    auth, no_auth = extension_class.get_routers()

    no_of_routes = len(auth.routes) + len(no_auth.routes)

    if no_of_routes == 0:
        return [
            ValidationItem(
                level='ERROR',
                message=(
                    'The Web application class must contain at least one route '
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


def _generate_ui_component_error(extension_class, parameter_name, format, page_name, code_pattern):
    return [
        ValidationItem(
            level='ERROR',
            message=(
                f'The {parameter_name} of the {page_name} must be a '
                f'path to {format} file relative to the static folder.'
            ),
            **get_code_context(extension_class, code_pattern),
        ),
    ]


def _generate_ui_component_static(extension_class, parameter_name, page_name, value, code_pattern):
    return [
        ValidationItem(
            level='ERROR',
            message=(
                f'The {parameter_name} {value} of the {page_name} must be prefixed with /static.'
            ),
            **get_code_context(extension_class, code_pattern),
        ),
    ]


def _generate_ui_component_does_not_exist(
    extension_class,
    parameter_name,
    page_name,
    value,
    code_pattern,
):
    return [
        ValidationItem(
            level='ERROR',
            message=(
                f'The {parameter_name} {value} of the {page_name} page does not point to any file.'
            ),
            **get_code_context(extension_class, code_pattern),
        ),
    ]


def _check_ui_component_url(extension_class, page_name, value, code_pattern):
    if not isinstance(value, str) or not value:
        return _generate_ui_component_error(extension_class, 'url', 'html', page_name, code_pattern)

    if not value.startswith('/static/'):
        return _generate_ui_component_static(extension_class, 'url', page_name, value, code_pattern)

    page_path = value[8:]
    full_path = os.path.join(
        os.path.dirname(_get_extension_class_file(extension_class)),
        'static',
        page_path,
    )
    if not os.path.exists(full_path):
        return _generate_ui_component_does_not_exist(
            extension_class,
            'url',
            page_name,
            value,
            code_pattern,
        )

    return []


def _check_ui_component_icon(extension_class, page_name, value, code_pattern):
    if not isinstance(value, str) or not value:
        return _generate_ui_component_error(
            extension_class,
            'icon',
            'image',
            page_name,
            code_pattern,
        )

    if not value.startswith('/static/'):
        return _generate_ui_component_static(
            extension_class,
            'icon',
            page_name,
            value,
            code_pattern,
        )

    page_path = value[8:]
    full_path = os.path.join(
        os.path.dirname(_get_extension_class_file(extension_class)),
        'static',
        page_path,
    )
    if not os.path.exists(full_path):
        return _generate_ui_component_does_not_exist(
            extension_class,
            'icon',
            page_name,
            value,
            code_pattern,
        )

    return []


def _validate_webapp_ui_modules(context):  # noqa: CCR001
    messages = []
    extension_class = _get_extension_class(context)

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

    if 'devops' in ui_modules:
        devops = ui_modules['devops']
        if not isinstance(devops, (list, tuple)):
            messages.append(
                ValidationItem(
                    level='ERROR',
                    message=(
                        'The argument of the @devops_pages '
                        'decorator must be a list of objects.'
                    ),
                    **get_code_context(extension_class, '@devops_pages('),
                ),
            )
        else:
            for child in devops:
                if 'label' not in child or 'url' not in child:
                    messages.append(
                        ValidationItem(
                            level='ERROR',
                            message=(
                                'Invalid devops page declaration. '
                                'Each devops page must be an object with the '
                                'label and url attributes.'
                            ),
                            **get_code_context(extension_class, '@devops_pages('),
                        ),
                    )
                    continue

                label = child['label']
                url = child['url']
                messages.extend(
                    _check_ui_component_label(
                        extension_class, '"Devops Page"', label, '@devops_pages(',
                    ),
                )
                messages.extend(
                    _check_ui_component_url(
                        extension_class, '"Devops Page"', url, '@devops_pages(',
                    ),
                )

    if 'customer' in ui_modules:
        customer = ui_modules['customer']
        if not isinstance(customer, (list, tuple)):
            messages.append(
                ValidationItem(
                    level='ERROR',
                    message=(
                        'The argument of the @customer_pages '
                        'decorator must be a list of objects.'
                    ),
                    **get_code_context(extension_class, '@customer_pages('),
                ),
            )
        else:
            for child in customer:
                if 'label' not in child or 'url' not in child:
                    messages.append(
                        ValidationItem(
                            level='ERROR',
                            message=(
                                'Invalid customer page declaration. '
                                'Each customer page must be an object with the '
                                'label and url attributes (and optionally icon).'
                            ),
                            **get_code_context(extension_class, '@customer_pages('),
                        ),
                    )
                    continue

                label = child['label']
                url = child['url']
                messages.extend(
                    _check_ui_component_label(
                        extension_class, '"Customer Page"', label, '@customer_pages(',
                    ),
                )
                messages.extend(
                    _check_ui_component_url(
                        extension_class, '"Customer Page"', url, '@customer_pages(',
                    ),
                )
                if 'icon' in child:
                    messages.extend(
                        _check_ui_component_icon(
                            extension_class, '"Customer Page"', child['icon'], '@customer_pages(',
                        ),
                    )

    return messages


def _get_extension_class(context):
    return context['extension_classes']['webapp']


def _get_extension_class_file(extension_class):
    return inspect.getsourcefile(extension_class)
