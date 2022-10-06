from fastapi.routing import APIRouter

from connect.eaas.core.decorators import (
    account_settings_page,
    admin_pages,
    module_pages,
    web_app,
)
from connect.eaas.core.extension import WebApplicationBase
from connect.eaas.core.validation.models import ValidationItem, ValidationResult
from connect.eaas.core.validation.validators.webapp import validate_webapp


def test_validate_webapp_no_such_extension(mocker):
    extension_class = mocker.MagicMock()
    context = {'extension_classes': {'events': extension_class}}

    result = validate_webapp(context)

    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 0


def test_validate_webapp_no_web_app_decorator(mocker):

    class MyWebApp(WebApplicationBase):
        pass

    mocker.patch(
        'connect.eaas.core.validation.validators.webapp.inspect.getsource',
        return_value='class E2EWebApp(WebApplicationBase):....',
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.webapp.inspect.getsourcefile',
        return_value='/dir/file.py',
    )

    context = {'extension_classes': {'webapp': MyWebApp}}
    result = validate_webapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert 'The Web application class must be wrapped in *@web_app(router)*.' in item.message


def test_validate_webapp_extension_no_router_methods(mocker):

    router = APIRouter()

    @web_app(router)
    class MyWebApp(WebApplicationBase):
        pass

    mocker.patch(
        'connect.eaas.core.validation.validators.webapp.inspect.getsource',
        side_effect=[
            '@web_app(router)\nclass E2EWebApp(WebApplicationBase):...',
            'def retrieve_settings(self):...',
        ],
    )
    mocker.patch(
        'connect.eaas.core.validation.validators.webapp.inspect.getsourcefile',
        return_value='/dir/file.py',
    )

    context = {'extension_classes': {'webapp': MyWebApp}}
    result = validate_webapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'The Web application class must contain at least one route implementation '
        'function wrapped in *@router.your_method("/your_path")*.'
    ) in item.message


def test_validate_webapp_page_doesnt_exist(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    @account_settings_page('Settings', '/static/settings.html')
    class MyWebApp(WebApplicationBase):
        @router.get('/')
        def example(self):
            pass

    mocker.patch(
        'connect.eaas.core.validation.validators.webapp.get_code_context',
        return_value={
            'file': 'file.py',
            'start_line': 11,
            'lineno': 22,
            'code': 'class MyExtension:',
        },
    )

    mocker.patch(
        'connect.eaas.core.validation.validators.webapp.os.path.exists',
        return_value=False,
    )

    context = {'extension_classes': {'webapp': MyWebApp}}

    result = validate_webapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'The url /static/settings.html of the "Account Settings" '
        'page does not point to any file.'
    ) == item.message


def test_validate_webapp_wrong_page_label(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    @account_settings_page(None, '/static/settings.html')
    class MyWebApp(WebApplicationBase):
        @router.get('/')
        def example(self):
            pass

    mocker.patch(
        'connect.eaas.core.validation.validators.webapp.get_code_context',
        return_value={
            'file': 'file.py',
            'start_line': 11,
            'lineno': 22,
            'code': 'class MyExtension:',
        },
    )

    mocker.patch(
        'connect.eaas.core.validation.validators.webapp.os.path.exists',
        return_value=True,
    )

    context = {'extension_classes': {'webapp': MyWebApp}}

    result = validate_webapp(context)

    assert isinstance(result, ValidationResult)
    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert 'The label of the "Account Settings" must be a non-blank string.' == item.message


def test_validate_webapp_wrong_page_url_format(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    @account_settings_page('Settings', 'settings.html')
    class MyWebApp(WebApplicationBase):
        @router.get('/')
        def example(self):
            pass

    mocker.patch(
        'connect.eaas.core.validation.validators.webapp.get_code_context',
        return_value={
            'file': 'file.py',
            'start_line': 11,
            'lineno': 22,
            'code': 'class MyExtension:',
        },
    )

    mocker.patch(
        'connect.eaas.core.validation.validators.webapp.os.path.exists',
        return_value=False,
    )

    context = {'extension_classes': {'webapp': MyWebApp}}

    result = validate_webapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'The url settings.html of the "Account Settings" '
        'must be prefixed with /static.'
    ) == item.message


def test_validate_webapp_wrong_page_url_type(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    @account_settings_page('Settings', None)
    class MyWebApp(WebApplicationBase):
        @router.get('/')
        def example(self):
            pass

    mocker.patch(
        'connect.eaas.core.validation.validators.webapp.get_code_context',
        return_value={
            'file': 'file.py',
            'start_line': 11,
            'lineno': 22,
            'code': 'class MyExtension:',
        },
    )

    mocker.patch(
        'connect.eaas.core.validation.validators.webapp.os.path.exists',
        return_value=False,
    )

    context = {'extension_classes': {'webapp': MyWebApp}}

    result = validate_webapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'The url of the "Account Settings" must be a path to a '
        'html file relative to the static folder.'
    ) == item.message


def test_validate_webapp_wrong_module_children_pages_type(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    @module_pages(
        'Main',
        '/static/main.html',
        children='hello',
    )
    class MyWebApp(WebApplicationBase):
        @router.get('/')
        def example(self):
            pass

    mocker.patch(
        'connect.eaas.core.validation.validators.webapp.get_code_context',
        return_value={
            'file': 'file.py',
            'start_line': 11,
            'lineno': 22,
            'code': 'class MyExtension:',
        },
    )

    mocker.patch(
        'connect.eaas.core.validation.validators.webapp.os.path.exists',
        return_value=True,
    )

    context = {'extension_classes': {'webapp': MyWebApp}}

    result = validate_webapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'The "children" argument of the @module_pages '
        'decorator must be a list of objects.'
    ) == item.message


def test_validate_webapp_wrong_module_children_pages_object(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    @module_pages(
        'Main',
        '/static/main.html',
        children=[{'hello': 'world'}],
    )
    class MyWebApp(WebApplicationBase):
        @router.get('/')
        def example(self):
            pass

    mocker.patch(
        'connect.eaas.core.validation.validators.webapp.get_code_context',
        return_value={
            'file': 'file.py',
            'start_line': 11,
            'lineno': 22,
            'code': 'class MyExtension:',
        },
    )

    mocker.patch(
        'connect.eaas.core.validation.validators.webapp.os.path.exists',
        return_value=True,
    )

    context = {'extension_classes': {'webapp': MyWebApp}}

    result = validate_webapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'Invalid child page declaration. Each child page must be an '
        'object with the label and url attributes.'
    ) == item.message


def test_validate_webapp_wrong_admin_pages_type(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    @admin_pages('hello')
    class MyWebApp(WebApplicationBase):
        @router.get('/')
        def example(self):
            pass

    mocker.patch(
        'connect.eaas.core.validation.validators.webapp.get_code_context',
        return_value={
            'file': 'file.py',
            'start_line': 11,
            'lineno': 22,
            'code': 'class MyExtension:',
        },
    )

    mocker.patch(
        'connect.eaas.core.validation.validators.webapp.os.path.exists',
        return_value=True,
    )

    context = {'extension_classes': {'webapp': MyWebApp}}

    result = validate_webapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert 'The argument of the @admin_pages decorator must be a list of objects.' == item.message


def test_validate_webapp_wrong_admin_pages_object(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    @admin_pages([{'hello': 'world'}])
    class MyWebApp(WebApplicationBase):
        @router.get('/')
        def example(self):
            pass

    mocker.patch(
        'connect.eaas.core.validation.validators.webapp.get_code_context',
        return_value={
            'file': 'file.py',
            'start_line': 11,
            'lineno': 22,
            'code': 'class MyExtension:',
        },
    )

    mocker.patch(
        'connect.eaas.core.validation.validators.webapp.os.path.exists',
        return_value=True,
    )

    context = {'extension_classes': {'webapp': MyWebApp}}

    result = validate_webapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'Invalid admin page declaration. Each admin page must '
        'be an object with the label and url attributes.'
    ) == item.message


def test_validate_webapp(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    @account_settings_page('Settings', '/static/settings.html')
    @module_pages(
        'Main',
        '/static/main.html',
        children=[
            {
                'label': 'Child page1',
                'url': '/static/child1.html',
            },
        ],
    )
    @admin_pages(
        [
            {
                'label': 'Admin page1',
                'url': '/static/admin1.html',
            },
        ],
    )
    class MyWebApp(WebApplicationBase):
        @router.get('/')
        def example(self):
            pass

    mocker.patch(
        'connect.eaas.core.validation.validators.webapp.os.path.exists',
        return_value=True,
    )

    context = {'extension_classes': {'webapp': MyWebApp}}

    result = validate_webapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert len(result.items) == 0


def test_validate_webapp_invalid_superclass(mocker):
    mocker.patch(
        'connect.eaas.core.validation.validators.anvilapp.inspect.getsourcefile',
        return_value='/dir/file.py',
    )

    class MyWebApp:
        pass

    webapp_extension_class = MyWebApp

    context = {'extension_classes': {'webapp': webapp_extension_class}}

    result = validate_webapp(context)

    assert isinstance(result, ValidationResult)

    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'The application class *MyWebApp* is not a subclass of '
        '*connect.eaas.core.extension.WebApplicationBase*.'
    ) in item.message
