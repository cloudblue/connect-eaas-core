from connect.eaas.core.decorators import manual_transformation, transformation
from connect.eaas.core.extension import AnvilApplicationBase, TransformationsApplicationBase
from connect.eaas.core.validation.models import ValidationItem, ValidationResult
from connect.eaas.core.validation.validators.tfnapp import validate_tfnapp


def test_validate_tfnapp_no_such_extension(mocker):
    context = {
        'extension_classes': {'webapp': mocker.MagicMock()},
    }
    result = validate_tfnapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 0


def test_validate_tfnapp_not_tfn_extension(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.tfnapp.inspect.getsourcefile',
        return_value='/dir/file.py',
    )

    class MyTfnApp(AnvilApplicationBase):
        pass

    context = {'extension_classes': {'tfnapp': MyTfnApp}}
    result = validate_tfnapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is True
    assert len(result.items) == 1


def test_validate_tfnapp(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.tfnapp.inspect.getsourcefile',
        return_value='/dir/file.py',
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.tfnapp.os.path.exists',
        return_value=True,
    )

    class MyTfnApp(TransformationsApplicationBase):
        @transformation(
            name='Copy Column(s)',
            description='The transformation function that copy content',
            edit_dialog_ui='/static/copy.html',
        )
        def copy_columns(self, row):
            pass

        @manual_transformation()
        @transformation(
            name='Manual Transformation',
            description='The transformation function that do nothing',
            edit_dialog_ui='/static/dummy.html',
        )
        def dummy_function(self):
            pass

    context = {'extension_classes': {'tfn': MyTfnApp}}
    result = validate_tfnapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 0


def test_validate_tfnapp_not_static_ui(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.tfnapp.inspect.getsourcefile',
        return_value='/dir/file.py',
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.tfnapp.get_code_context',
        return_value={
            'file': 'file.py',
            'start_line': 11,
            'lineno': 22,
            'code': 'class MyTnfApp:',
        },
    )

    class MyTfnApp(TransformationsApplicationBase):
        @transformation(
            name='Copy Column(s)',
            description='Transformation function that converts from one currency to another',
            edit_dialog_ui='/currency_conversion.html',
        )
        def convert_pricing(self, row):
            pass

    context = {'extension_classes': {'tfnapp': MyTfnApp}}
    result = validate_tfnapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'The url /currency_conversion.html of the convert_pricing '
        'must be prefixed with /static.'
    ) == item.message


def test_validate_tfnapp_no_ui_page(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.tfnapp.inspect.getsourcefile',
        return_value='/dir/file.py',
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.tfnapp.os.path.exists',
        return_value=False,
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.tfnapp.get_code_context',
        return_value={
            'file': 'file.py',
            'start_line': 11,
            'lineno': 22,
            'code': 'class MyTnfApp:',
        },
    )

    class MyTfnApp(TransformationsApplicationBase):
        @transformation(
            name='Copy Column(s)',
            description='The transformation function that copy content',
            edit_dialog_ui='/static/copy.html',
        )
        def copy_columns(self, row):
            pass

    context = {'extension_classes': {'tfnapp': MyTfnApp}}
    result = validate_tfnapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'The url /static/copy.html of the copy_columns '
        'does not point to any file.'
    ) == item.message
