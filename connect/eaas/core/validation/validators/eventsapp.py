import inspect

from connect.eaas.core.extension import EventsApplicationBase, Extension
from connect.eaas.core.responses import (
    CustomEventResponse,
    ProcessingResponse,
    ProductActionResponse,
    ValidationResponse,
)
from connect.eaas.core.validation.helpers import get_code_context
from connect.eaas.core.validation.models import ValidationItem, ValidationResult


def validate_eventsapp(context):

    extension_class = context['extension_classes'].get(
        'eventsapp',
        context['extension_classes'].get('extension'),
    )

    if not extension_class:
        return ValidationResult()

    extension_class_file = inspect.getsourcefile(extension_class)

    messages = []

    if issubclass(extension_class, Extension):
        messages.append(
            ValidationItem(
                level='WARNING',
                message=(
                    f'The application class *{extension_class.__name__}* inherits from '
                    '*connect.eaas.extension.Extension* that has been deprecated in favor of '
                    '*connect.eaas.core.extension.EventsApplicationBase*.'
                ),
                file=extension_class_file,
            ),
        )
    elif not issubclass(extension_class, (Extension, EventsApplicationBase)):
        messages.append(
            ValidationItem(
                level='ERROR',
                message=(
                    f'The application class *{extension_class.__name__}* '
                    'is not a subclass of *connect.eaas.core.extension.EventsApplicationBase*.'
                ),
                file=extension_class_file,
            ),
        )
        return ValidationResult(items=messages, must_exit=True)

    defined_classes = [
        member[1]
        for member in inspect.getmembers(extension_class, predicate=inspect.isclass)
    ]

    for deprecated_cls, cls_name in (
        (CustomEventResponse, 'connect.eaas.core.responses.InteractiveResponse'),
        (ProcessingResponse, 'connect.eaas.core.responses.BackgroundResponse'),
        (ProductActionResponse, 'connect.eaas.core.responses.InteractiveResponse'),
        (ValidationResponse, 'connect.eaas.core.responses.InteractiveResponse'),
    ):
        if deprecated_cls in defined_classes:
            messages.append(
                ValidationItem(
                    message=(
                        f'The response class *{deprecated_cls.__name__}* '
                        f'has been deprecated in favor of *{cls_name}*.'
                    ),
                    **get_code_context(extension_class, deprecated_cls.__name__),
                ),
            )

    descriptor = context['descriptor']
    extension_json_file = context['extension_json_file']

    for description in ['variables', 'capabilities', 'schedulables']:
        if description in descriptor:
            messages.append(
                ValidationItem(
                    message=(
                        f'Extension {description} must be declared using the '
                        f'*connect.eaas.core.decorators.'
                        f'{description if description != "schedulables" else "event"}* decorator.'
                    ),
                    file=extension_json_file,
                ),
            )

    messages.extend(_validate_events(context))
    messages.extend(_validate_schedulables(context))

    return ValidationResult(items=messages)


def _validate_events(context):
    messages = []

    extension_class = context['extension_classes'].get(
        'eventsapp',
        context['extension_classes'].get('extension'),
    )

    definitions = context['event_definitions']
    events = extension_class.get_events()
    for event in events:
        method = getattr(extension_class, event['method'])
        if event['event_type'] not in definitions:
            messages.append(
                ValidationItem(
                    level='ERROR',
                    message=f'The event type *{event["event_type"]}* is not valid.',
                    **get_code_context(method, '@event'),
                ),
            )
            continue

        statuses = definitions[event['event_type']]['object_statuses']
        if statuses:
            invalid_statuses = set(event['statuses']) - set(statuses)
        else:
            invalid_statuses = set(event['statuses'] or [])
        if invalid_statuses:
            messages.append(
                ValidationItem(
                    level='ERROR',
                    message=(
                        f'The status/es *{", ".join(invalid_statuses)}* are invalid '
                        f'for the event *{event["event_type"]}*.'
                    ),
                    **get_code_context(method, '@event'),
                ),
            )

        signature = inspect.signature(method)
        if len(signature.parameters) != 2:
            sig_str = f'{event["method"]}({", ".join(signature.parameters)})'

            messages.append(
                ValidationItem(
                    level='ERROR',
                    message=(
                        f'The handler for the event *{event["event_type"]}* '
                        f'has an invalid signature: *{sig_str}*'
                    ),
                    **get_code_context(method, sig_str),
                ),
            )
    return messages


def _validate_schedulables(context):
    messages = []

    extension_class = context['extension_classes'].get(
        'eventsapp',
        context['extension_classes'].get('extension'),
    )

    schedulables = extension_class.get_schedulables()
    for schedulable in schedulables:
        method = getattr(extension_class, schedulable['method'])
        signature = inspect.signature(method)
        if len(signature.parameters) != 2:
            sig_str = f'{schedulable["method"]}({", ".join(signature.parameters)})'

            messages.append(
                ValidationItem(
                    level='ERROR',
                    message=(
                        f'The schedulable method *{schedulable["method"]}* '
                        f'has an invalid signature: *{sig_str}*'
                    ),
                    **get_code_context(method, sig_str),
                ),
            )
    return messages
