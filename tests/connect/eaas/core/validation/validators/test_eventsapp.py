import pytest

from connect.eaas.core.decorators import event, schedulable
from connect.eaas.core.extension import EventsApplicationBase, Extension
from connect.eaas.core.responses import (
    CustomEventResponse,
    ProcessingResponse,
    ProductActionResponse,
    ValidationResponse,
)
from connect.eaas.core.validation.models import ValidationItem, ValidationResult
from connect.eaas.core.validation.validators.eventsapp import validate_eventsapp


def test_validate_eventsapp_no_such_extension(mocker):
    extension_class = mocker.MagicMock()
    context = {'extension_classes': {'webapp': extension_class}}
    result = validate_eventsapp(context)

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 0


def test_validate_eventsapp_deprecated_superclass(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.eventsapp.inspect.getsourcefile',
        return_value='/dir/file.py',
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.eventsapp._validate_events',
        return_value=[],
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.eventsapp._validate_schedulables',
        return_value=[],
    )

    class MyExt(Extension):
        pass

    context = {
        'extension_classes': {'extension': MyExt},
        'descriptor': {},
        'extension_json_file': 'extension.json',
    }
    result = validate_eventsapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'WARNING'
    assert (
        'The application class *MyExt* inherits from *connect.eaas.extension.Extension* '
        'that has been deprecated in favor of *connect.eaas.core.extension.EventsApplicationBase*.'
    ) in item.message
    assert item.file == '/dir/file.py'


def test_validate_eventsapp_invalid_superclass(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.eventsapp.inspect.getsourcefile',
        return_value='/dir/file.py',
    )
    context = {'extension_classes': {'extension': KeyError}}
    result = validate_eventsapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'The application class *KeyError* '
        'is not a subclass of *connect.eaas.core.extension.EventsApplicationBase*.'
    ) in item.message
    assert item.file == '/dir/file.py'


@pytest.mark.parametrize(
    ('deprecated', 'replacement'),
    (
        (CustomEventResponse, 'connect.eaas.core.responses.InteractiveResponse'),
        (ProcessingResponse, 'connect.eaas.core.responses.BackgroundResponse'),
        (ProductActionResponse, 'connect.eaas.core.responses.InteractiveResponse'),
        (ValidationResponse, 'connect.eaas.core.responses.InteractiveResponse'),
    ),
)
def test_validate_eventsapp_deprecated_responses(mocker, deprecated, replacement):

    class MyEvtExt(EventsApplicationBase):
        pass

    mocker.patch(
        'connect.eaas.core.validation.validators.eventsapp.inspect.getmembers',
        return_value=[(deprecated.__name__, deprecated)],
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.eventsapp._validate_events',
        return_value=[],
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.eventsapp._validate_schedulables',
        return_value=[],
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.eventsapp.get_code_context',
        return_value={
            'file': 'file',
            'start_line': 0,
            'lineno': 5,
            'code': 'code',
        },
    )

    context = {
        'extension_classes': {'extension': MyEvtExt},
        'descriptor': {},
        'extension_json_file': 'extension.json',
    }

    result = validate_eventsapp(context)

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'WARNING'
    assert (
        f'The response class *{deprecated.__name__}* '
        f'has been deprecated in favor of *{replacement}*.'
    ) in item.message
    assert item.file == 'file'
    assert item.start_line == 0
    assert item.lineno == 5
    assert item.code == 'code'


@pytest.mark.parametrize(
    'descriptor',
    (
        {'capabilities': {}},
        {'variables': []},
        {'schedulables': []},
    ),
)
def test_validate_eventsapp_descriptor_with_declarations(mocker, descriptor):
    mocker.patch(
        'connect.eaas.core.validation.validators.eventsapp.inspect.getsourcefile',
        return_value='/dir/file.py',
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.eventsapp._validate_events',
        return_value=[],
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.eventsapp._validate_schedulables',
        return_value=[],
    )

    class MyExt(EventsApplicationBase):
        pass

    context = {
        'extension_classes': {'extension': MyExt},
        'descriptor': descriptor,
        'extension_json_file': '/dir/extension.json',
    }
    result = validate_eventsapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'WARNING'
    assert 'must be declared using' in item.message
    assert item.file == '/dir/extension.json'


def test_validate_eventsapp_invalid_event(mocker):
    class MyExt(EventsApplicationBase):
        @event('my_awesome_event', statuses=['pending', 'accepted'])
        def handle_event(self, request):
            pass

    context = {
        'extension_classes': {'extension': MyExt},
        'descriptor': {},
        'extension_json_file': 'extension.json',
        'event_definitions': {'another_event': {}},
    }
    mocker.patch(
        'connect.eaas.core.validation.validators.eventsapp.get_code_context',
        return_value={
            'file': 'file',
            'start_line': 0,
            'lineno': 5,
            'code': 'code',
        },
    )

    result = validate_eventsapp(context)

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert 'The event type *my_awesome_event* is not valid.' in item.message
    assert item.file == 'file'
    assert item.start_line == 0
    assert item.lineno == 5
    assert item.code == 'code'


@pytest.mark.parametrize(
    ('object_statuses', 'event_statuses'),
    (
        (['status1', 'status2'], ['status3']),
        ([], ['status3']),
    ),
)
def test_validate_eventsapp_invalid_status(mocker, object_statuses, event_statuses):
    class MyExt(EventsApplicationBase):
        @event('test_event', statuses=event_statuses)
        def handle_event(self, request):
            pass

    context = {
        'extension_classes': {'extension': MyExt},
        'descriptor': {},
        'extension_json_file': 'extension.json',
        'event_definitions': {'test_event': {'object_statuses': object_statuses}},
    }

    mocker.patch(
        'connect.eaas.core.validation.validators.eventsapp.get_code_context',
        return_value={
            'file': 'file',
            'start_line': 0,
            'lineno': 5,
            'code': 'code',
        },
    )

    result = validate_eventsapp(context)

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert 'The status/es *status3* are invalid for the event *test_event*.' in item.message
    assert item.file == 'file'
    assert item.start_line == 0
    assert item.lineno == 5
    assert item.code == 'code'


def test_validate_eventsapp_invalid_signature(mocker):
    class MyExt(EventsApplicationBase):
        @event('test_event', statuses=['status'])
        def handle_event(self, request, another_arg):
            pass

    context = {
        'extension_classes': {'extension': MyExt},
        'descriptor': {},
        'extension_json_file': 'extension.json',
        'event_definitions': {'test_event': {'object_statuses': ['status']}},
    }

    mocker.patch(
        'connect.eaas.core.validation.validators.eventsapp.get_code_context',
        return_value={
            'file': 'file',
            'start_line': 0,
            'lineno': 5,
            'code': 'code',
        },
    )

    result = validate_eventsapp(context)

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert 'The handler for the event *test_event* has an invalid signature' in item.message
    assert item.file == 'file'
    assert item.start_line == 0
    assert item.lineno == 5
    assert item.code == 'code'


def test_validate_eventsapp_schedulables_invalid_signature(mocker):
    class MyExt(EventsApplicationBase):
        @schedulable('name', 'description')
        def handle_event(self, request, another_arg):
            pass

    context = {
        'extension_classes': {'extension': MyExt},
        'descriptor': {},
        'extension_json_file': 'extension.json',
        'event_definitions': {},
    }
    mocker.patch(
        'connect.eaas.core.validation.validators.eventsapp.get_code_context',
        return_value={
            'file': 'file',
            'start_line': 0,
            'lineno': 5,
            'code': 'code',
        },
    )

    result = validate_eventsapp(context)

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert 'The schedulable method *handle_event* has an invalid signature' in item.message
    assert item.file == 'file'
    assert item.start_line == 0
    assert item.lineno == 5
    assert item.code == 'code'
