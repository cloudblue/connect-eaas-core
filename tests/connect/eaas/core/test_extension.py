import os

from connect.eaas.core.decorators import event, schedulable, variables
from connect.eaas.core.extension import Extension, UIExtension


def test_get_events():

    class MyExtension(Extension):

        @event(
            'asset_purchase_request_processing',
            statuses=['pending', 'inquiring'],
        )
        def process_purchase(self, request):
            """This process purchases"""
            pass

        @event(
            'asset_change_request_processing',
            statuses=['pending', 'inquiring'],
        )
        async def process_change(self, request):
            pass

    assert sorted(MyExtension.get_events(), key=lambda x: x['method']) == [
        {
            'method': 'process_change',
            'event_type': 'asset_change_request_processing',
            'statuses': ['pending', 'inquiring'],
        },
        {
            'method': 'process_purchase',
            'event_type': 'asset_purchase_request_processing',
            'statuses': ['pending', 'inquiring'],
        },
    ]

    assert MyExtension(None, None, None).process_purchase.__name__ == 'process_purchase'
    assert MyExtension(None, None, None).process_purchase.__doc__ == 'This process purchases'


def test_get_schedulables():

    class MyExtension(Extension):

        @schedulable(
            'schedulable1_name',
            'schedulable1_description',
        )
        def schedulable1(self, request):
            """This is schedulable"""
            pass

        @schedulable(
            'schedulable2_name',
            'schedulable2_description',
        )
        async def schedulable2(self, request):
            pass

    assert sorted(MyExtension.get_schedulables(), key=lambda x: x['method']) == [
        {
            'method': 'schedulable1',
            'name': 'schedulable1_name',
            'description': 'schedulable1_description',
        },
        {
            'method': 'schedulable2',
            'name': 'schedulable2_name',
            'description': 'schedulable2_description',
        },
    ]

    assert MyExtension(None, None, None).schedulable1.__name__ == 'schedulable1'
    assert MyExtension(None, None, None).schedulable1.__doc__ == 'This is schedulable'


def test_get_variables():

    vars = [
        {
            'name': 'var1',
            'initial_value': 'val1',
        },
        {
            'name': 'var2',
            'initial_value': 'val2',
            'secure': True,
        },
    ]

    @variables(vars)
    class MyExtension(Extension):
        """this is my extension"""
        pass

    assert MyExtension.get_variables() == vars
    assert MyExtension.__name__ == 'MyExtension'
    assert MyExtension.__doc__ == 'this is my extension'


def test_get_static_root(mocker):
    mocker.patch('connect.eaas.core.extension.os.path.exists', return_value=True)
    mocker.patch('connect.eaas.core.extension.os.path.isdir', return_value=True)

    class MyUIExtension(UIExtension):
        pass

    assert MyUIExtension.get_static_root() == os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            'static_root',
        ),
    )


def test_get_static_root_not_exists(mocker):
    mocker.patch('connect.eaas.core.extension.os.path.exists', return_value=False)

    class MyUIExtension(UIExtension):
        pass

    assert MyUIExtension.get_static_root() is None
