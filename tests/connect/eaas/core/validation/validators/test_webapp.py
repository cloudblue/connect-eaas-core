import pytest
from fastapi.exceptions import HTTPException
from fastapi.routing import APIRouter

from connect.client import ClientError
from connect.eaas.core.decorators import (
    account_settings_page,
    admin_pages,
    customer_pages,
    devops_pages,
    module_pages,
    proxied_connect_api,
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
        'The url of the "Account Settings" must be a path to '
        'html file relative to the static folder.'
    ) == item.message


@pytest.mark.parametrize(
    'pages',
    (
        set(),
        dict(),
    ),
)
def test_validate_webapp_customer_page_invalid_format(mocker, pages):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    @customer_pages(
        pages=pages,
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

    context = {'extension_classes': {'webapp': MyWebApp}}

    result = validate_webapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'The argument of the @customer_pages decorator must be a list of objects.'
    ) == item.message


@pytest.mark.parametrize(
    'pages',
    (
        [{'url': '/static/customer.html'}],
        [{'label': 'Label'}],
    ),
)
def test_validate_webapp_customer_page_invalid_child_format(mocker, pages):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    @customer_pages(
        pages=pages,
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

    context = {'extension_classes': {'webapp': MyWebApp}}

    result = validate_webapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'Invalid customer page declaration. Each customer page must be an object with the label'
        ' and url attributes (and optionally icon).'
    ) == item.message


def test_validate_webapp_customer_page_doesnt_exist(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    @customer_pages(
        pages=[
            {
                'label': 'Customer home page',
                'url': '/static/customer.html',
            },
        ],
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
        'The url /static/customer.html of the "Customer Page" '
        'page does not point to any file.'
    ) == item.message


def test_validate_webapp_wrong_customer_page_label(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    @customer_pages(
        pages=[
            {
                'label': None,
                'url': '/static/customer.html',
                'icon': '/static/icon.png',
            },
        ],
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
    assert 'The label of the "Customer Page" must be a non-blank string.' == item.message


def test_validate_webapp_wrong_customer_page_url_format(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    @customer_pages(
        pages=[
            {
                'label': 'Customer home page',
                'url': 'customer.html',
            },
        ],
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
        'The url customer.html of the "Customer Page" '
        'must be prefixed with /static.'
    ) == item.message


def test_validate_webapp_wrong_customer_page_url_type(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    @customer_pages(
        pages=[
            {
                'label': 'Customer home page',
                'url': None,
            },
        ],
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
        'The url of the "Customer Page" must be a path to '
        'html file relative to the static folder.'
    ) == item.message


def test_validate_webapp_wrong_customer_page_icon_format(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    @customer_pages(
        pages=[
            {
                'label': 'Customer home page',
                'url': '/static/customer.html',
                'icon': 'icon.png',
            },
        ],
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
        'The icon icon.png of the "Customer Page" '
        'must be prefixed with /static.'
    ) == item.message


def test_validate_webapp_wrong_customer_page_icon_type(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    @customer_pages(
        pages=[
            {
                'label': 'Customer home page',
                'url': '/static/customer.html',
                'icon': None,
            },
        ],
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
        'The icon of the "Customer Page" must be a path to '
        'image file relative to the static folder.'
    ) == item.message


def test_validate_webapp_wrong_customer_page_url_and_icon_does_not_exist(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    @customer_pages(
        pages=[
            {
                'label': 'Customer home page',
                'url': '/static/customer.html',
                'icon': '/static/icon.png',
            },
        ],
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

    context = {'extension_classes': {'webapp': MyWebApp}}

    result = validate_webapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is True
    assert len(result.items) == 2
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert (
        'The url /static/customer.html of the "Customer Page" page does not point to any file.'
    ) == item.message
    item2 = result.items[1]
    assert isinstance(item2, ValidationItem)
    assert item2.level == 'ERROR'
    assert (
        'The icon /static/icon.png of the "Customer Page" page does not point to any file.'
    ) == item2.message


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


def test_validate_webapp_wrong_devops_pages_type(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    @devops_pages('hello')
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
    assert 'The argument of the @devops_pages decorator must be a list of objects.' == item.message


def test_validate_webapp_wrong_devops_pages_object(mocker):

    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    @devops_pages([{'hello': 'world'}])
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
        'Invalid devops page declaration. Each devops page must '
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
        '/static/icon.png',
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
    @devops_pages(
        [
            {
                'label': 'Tab1',
                'url': '/static/tab1.html',
            },
        ],
    )
    @customer_pages(
        pages=[
            {
                'label': 'Customer Home Page',
                'url': '/static/customer.html',
                'icon': '/static/icon.png',
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


@pytest.mark.parametrize('exception_handlers', (
    {},
    {ValueError: 1},
    {HTTPException: 2, ClientError: ''},
))
def test_validate_webapp_get_exc_handling_ok(mocker, exception_handlers):
    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    class MyWebApp(WebApplicationBase):
        @classmethod
        def get_exception_handlers(cls, _):
            return exception_handlers

        @router.get('/')
        def example(self):
            pass

    context = {'extension_classes': {'webapp': MyWebApp}}

    result = validate_webapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert not result.items


@pytest.mark.parametrize('f, error', (
    (1, 'Invalid declaration of `get_exception_handlers` in Web Application.'),
    (lambda: {}, 'Invalid declaration of `get_exception_handlers` in Web Application.'),
    (
        lambda a: [],
        'Invalid implementation of `get_exception_handlers` in Web Application: '
        'returned value must be a dictionary.',
    ),
    (
        lambda a: {
            RuntimeError: 1,
            WebApplicationBase: 2,
        },
        'Invalid implementation of `get_exception_handlers` in Web Application: all'
        ' configuration keys must Exception classes, inherited from BaseException.',
    ),
))
def test_validate_webapp_get_exc_handling_fail(mocker, f, error):
    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    class MyWebApp(WebApplicationBase):
        @classmethod
        def get_exception_handlers(cls, *args, **kwargs):
            return f(*args, **kwargs)

        @router.get('/')
        def example(self):
            pass

    context = {'extension_classes': {'webapp': MyWebApp}}

    result = validate_webapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert error == item.message


@pytest.mark.parametrize('middlewares', (
    [],
    [lambda: 1],
    [WebApplicationBase(), lambda: 1],
))
def test_validate_webapp_get_middlewares_ok(mocker, middlewares):
    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    class MyWebApp(WebApplicationBase):
        @classmethod
        def get_middlewares(cls):
            return middlewares

        @router.get('/')
        def example(self):
            pass

    context = {'extension_classes': {'webapp': MyWebApp}}

    result = validate_webapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert not result.items


@pytest.mark.parametrize('f, error', (
    (1, 'Invalid declaration of `get_middlewares` in Web Application.'),
    (
        lambda: {},
        'Invalid implementation of `get_middlewares` in Web Application: '
        'returned value must be a list.',
    ),
))
def test_validate_webapp_get_middlewares_fail(mocker, f, error):
    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)
    mocker.patch(
        'connect.eaas.core.validation.validators.webapp._get_extension_class_file',
        return_value='1',
    )

    @web_app(router)
    class MyWebApp(WebApplicationBase):
        @classmethod
        def get_middlewares(cls, *args, **kwargs):
            return f(*args, **kwargs)

        @router.get('/')
        def example(self):
            pass

    context = {'extension_classes': {'webapp': MyWebApp}}

    result = validate_webapp(context)

    assert isinstance(result, ValidationResult)

    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert item.file == '1'
    assert error == item.message


@pytest.mark.parametrize('proxied_api', (
    [],
    {},
    ['/public/v1/auth'],
    ['/public/', '/public/v1/auth/context'],
    {
        '/public/': 'view',
        '/public/v1/auth/context': 'edit',
    },
))
def test_validate_webapp_get_proxied_connect_api_ok(mocker, proxied_api):
    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)

    @web_app(router)
    @proxied_connect_api(proxied_api)
    class MyWebApp(WebApplicationBase):
        @router.get('/')
        def example(self):
            pass

    context = {'extension_classes': {'webapp': MyWebApp}}

    result = validate_webapp(context)
    assert isinstance(result, ValidationResult)
    assert result.must_exit is False
    assert not result.items


@pytest.mark.parametrize('proxied_api, error', (
    (set(), 'The argument of the `@proxied_connect_api` must be a list of strings or a dict.'),
    (['str', 1], 'The argument of the `@proxied_connect_api` must be a list of strings or a dict.'),
    (['/public/v1/auth'] * 101, 'Max allowed length of the `@proxied_connect_api` argument: 100.'),
    (['/media'], 'Only Public or Files API can be referenced in `@proxied_connect_api`.'),
    (
        {f'/public/v1/ep{i}': 'view' for i in range(200)},
        'Max allowed length of the `@proxied_connect_api` argument: 100.',
    ),
    (
        {
            '/files': 'view',
            '/public/v1/marketplaces': 'view',
            '/public/v1/products': 'edit',
            '/private/api': 'view',
        },
        'Only Public or Files API can be referenced in `@proxied_connect_api`.',
    ),
    (
        {
            '/public/v1/marketplaces': 'view',
            '/public/v1/products': 'create',
            '/public/v1/accounts/VA-123/users': 'post',
        },
        'Wrong Public API permission value in `@proxied_connect_api`.',
    ),
    (
        {'/public/v1/marketplaces': []},
        'Wrong Public API permission value in `@proxied_connect_api`.',
    ),
))
def test_validate_webapp_get_proxied_connect_api_fail(mocker, proxied_api, error):
    router = APIRouter()
    mocker.patch('connect.eaas.core.extension.router', router)
    mocker.patch(
        'connect.eaas.core.validation.validators.webapp._get_extension_class_file',
        return_value='1',
    )

    @web_app(router)
    @proxied_connect_api(proxied_api)
    class MyWebApp(WebApplicationBase):
        @router.get('/')
        def example(self):
            pass

    context = {'extension_classes': {'webapp': MyWebApp}}

    result = validate_webapp(context)

    assert isinstance(result, ValidationResult)

    assert result.must_exit is True
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, ValidationItem)
    assert item.level == 'ERROR'
    assert error == item.message
