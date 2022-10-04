from connect.eaas.core.decorators import anvil_callable
from connect.eaas.core.extension import AnvilExtension
from connect.eaas.core.validation.models import ValidationItem, ValidationResult
from connect.eaas.core.validation.validators.anvilapp import validate_anvilapp


def test_validate_anvilapp_no_such_extension(mocker):
    context = {
        'extension_classes': {'webapp': mocker.MagicMock()},
    }
    result = validate_anvilapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 0


def test_validate_anvilapp(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.anvilapp.inspect.getsourcefile',
        return_value='/dir/file.py',
    )

    class MyAnvilApp(AnvilExtension):
        @classmethod
        def get_anvil_key_variable(cls):
            return 'ANVIL_API_KEY'

        @anvil_callable()
        def my_callable(self, a_parameter):
            pass

    anvil_extension_class = MyAnvilApp
    context = {'extension_classes': {'anvil': anvil_extension_class}}

    result = validate_anvilapp(context)

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 0


def test_validate_anvilapp_invalid_anvil_api_key(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.anvilapp.inspect.getsourcefile',
        return_value='/dir/file.py',
    )

    class MyAnvilApp(AnvilExtension):
        @classmethod
        def get_anvil_key_variable(cls):
            return '1ANVIL1'

        @anvil_callable()
        def my_callable(self, a_parameter):
            pass

    anvil_extension_class = MyAnvilApp

    context = {'extension_classes': {'anvil': anvil_extension_class}}

    result = validate_anvilapp(context)

    assert isinstance(result, ValidationResult)

    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert 'Invalid Anvil key variable name: the value *1ANVIL1* does not match' in item.message


def test_validate_anvilapp_no_callables(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.anvilapp.inspect.getsourcefile',
        return_value='/dir/file.py',
    )

    class MyAnvilApp(AnvilExtension):
        @classmethod
        def get_anvil_key_variable(cls):
            return 'ANVIL_API_KEY'

    anvil_extension_class = MyAnvilApp

    context = {'extension_classes': {'anvil': anvil_extension_class}}

    result = validate_anvilapp(context)

    assert isinstance(result, ValidationResult)

    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'The Anvil app extension class must contain at least '
        'one callable marked with the *@anvil_callable* decorator.'
    ) in item.message


def test_validate_anvilapp_invalid_superclass(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.anvilapp.inspect.getsourcefile',
        return_value='/dir/file.py',
    )

    class MyAnvilApp:
        pass

    anvil_extension_class = MyAnvilApp

    context = {'extension_classes': {'anvil': anvil_extension_class}}

    result = validate_anvilapp(context)

    assert isinstance(result, ValidationResult)

    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'he extension class *MyAnvilApp* is not a subclass of '
        '*connect.eaas.core.extension.AnvilExtension*.'
    ) in item.message
