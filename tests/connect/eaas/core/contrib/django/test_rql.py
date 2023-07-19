import pytest

from connect.eaas.core.contrib.django.rql import (
    RQLFilteredQuerySet,
    RQLLimitOffsetPaginator,
    _RQLLimitOffsetPaginator,
)


def test_rql_paginator_class_with_empty_rql(mocker):
    mocked_queryset = mocker.MagicMock()
    mocked_queryset.count.return_value = 11
    mocked_queryset.__getitem__.return_value = [
        {},
        {},
    ]
    mocked_queryset.__len__.return_value = 11
    mocked_model = mocker.MagicMock()
    mocked_model.from_orm.return_value = {'field': 'hola'}
    paginator = _RQLLimitOffsetPaginator('', 100)
    response = paginator.serialize(mocked_queryset, mocked_model)
    assert response.body == b'[{"field":"hola"},{"field":"hola"}]'
    assert dict(response.headers) == {
        'content-range': 'items 0-1/11',
        'content-length': '35',
        'content-type': 'application/json',
    }
    assert paginator.limit == 11
    assert paginator.offset == 0
    assert paginator.count == 11
    mocked_model.from_orm.assert_called_with({})


def test_rql_paginator_class_with_limit_0(mocker):
    mocked_queryset = mocker.MagicMock()
    mocked_queryset.count.return_value = 11
    mocked_queryset.__getitem__.return_value = [
        {},
        {},
    ]
    mocked_queryset.__len__.return_value = 11
    mocked_model = mocker.MagicMock()
    paginator = _RQLLimitOffsetPaginator('limit=0', 100)
    response = paginator.serialize(mocked_queryset, mocked_model)
    assert response.body == b'[]'
    assert dict(response.headers) == {
        'content-range': 'items 0-0/11',
        'content-length': '2',
        'content-type': 'application/json',
    }
    assert paginator.limit == 0
    assert paginator.offset == 0
    assert paginator.count == 11
    mocked_model.from_orm.assert_not_called()


def test_rql_paginator_class_with_0_items(mocker):
    mocked_queryset = mocker.MagicMock()
    mocked_queryset.count.return_value = 0
    mocked_queryset.__getitem__.return_value = [
    ]
    mocked_queryset.__len__.return_value = 0
    mocked_model = mocker.MagicMock()
    paginator = _RQLLimitOffsetPaginator('', 100)
    response = paginator.serialize(mocked_queryset, mocked_model)
    assert response.body == b'[]'
    assert dict(response.headers) == {
        'content-range': 'items 0-0/0',
        'content-length': '2',
        'content-type': 'application/json',
    }
    assert paginator.limit == 100
    assert paginator.offset == 0
    assert paginator.count == 0
    mocked_model.from_orm.assert_not_called()


def test_rql_paginator_class_with_offset_higher_than_items(mocker):
    mocked_queryset = mocker.MagicMock()
    mocked_queryset.count.return_value = 10
    mocked_queryset.__getitem__.return_value = [
    ]
    mocked_queryset.__len__.return_value = 0
    mocked_model = mocker.MagicMock()
    paginator = _RQLLimitOffsetPaginator('offset=12', 100)
    response = paginator.serialize(mocked_queryset, mocked_model)
    assert response.body == b'[]'
    assert dict(response.headers) == {
        'content-range': 'items 12-12/10',
        'content-length': '2',
        'content-type': 'application/json',
    }
    assert paginator.limit == 100
    assert paginator.offset == 12
    assert paginator.count == 10
    mocked_model.from_orm.assert_not_called()


def test_rql_paginator_class_with_limit_offset_higher_than_items(mocker):
    mocked_queryset = mocker.MagicMock()
    mocked_queryset.count.return_value = 10
    mocked_queryset.__getitem__.return_value = [
    ]
    mocked_queryset.__len__.return_value = 10
    mocked_model = mocker.MagicMock()
    paginator = _RQLLimitOffsetPaginator('offset=5&limit=10', 100)
    response = paginator.serialize(mocked_queryset, mocked_model)
    assert response.body == b'[]'
    assert dict(response.headers) == {
        'content-range': 'items 5-5/10',
        'content-length': '2',
        'content-type': 'application/json',
    }
    assert paginator.limit == 5
    assert paginator.offset == 5
    assert paginator.count == 10
    mocked_model.from_orm.assert_not_called()


def test_rql_paginator_class_with_limit_offset_lower_than_items(mocker):
    mocked_queryset = mocker.MagicMock()
    mocked_queryset.count.return_value = 10
    mocked_queryset.__getitem__.return_value = [
        {},
        {},
        {},
        {},
        {},
    ]
    mocked_queryset.__len__.return_value = 10
    mocked_model = mocker.MagicMock()
    mocked_model.from_orm.return_value = {'field': 'hola'}
    paginator = _RQLLimitOffsetPaginator('offset=2&limit=5', 100)
    response = paginator.serialize(mocked_queryset, mocked_model)
    assert response.body == (
        b'[{"field":"hola"},{"field":"hola"},{"field":"hola"},{"field":"hola"},'
        b'{"field":"hola"}]'
    )
    assert dict(response.headers) == {
        'content-range': 'items 2-6/10',
        'content-length': '86',
        'content-type': 'application/json',
    }
    assert paginator.limit == 5
    assert paginator.offset == 2
    assert paginator.count == 10
    mocked_model.from_orm.assert_called_with({})


def test_rql_paginator_class_serialize(mocker):
    mocked_queryset = mocker.MagicMock()
    mocked_queryset.count.return_value = 11
    mocked_queryset.__getitem__.return_value = [
        {},
        {},
    ]
    mocked_queryset.__len__.return_value = 11
    mocked_model = mocker.MagicMock()
    mocked_model.from_orm.return_value = {'field': 'hola'}
    paginator = _RQLLimitOffsetPaginator('eq(field,name)&limit=10000&offset=2', 100)
    response = paginator.serialize(mocked_queryset, mocked_model)
    assert response.body == b'[{"field":"hola"},{"field":"hola"}]'
    assert dict(response.headers) == {
        'content-range': 'items 2-3/11',
        'content-length': '35',
        'content-type': 'application/json',
    }
    assert paginator.limit == 9
    assert paginator.offset == 2
    assert paginator.count == 11
    mocked_model.from_orm.assert_called_with({})


@pytest.mark.asyncio
async def test_rql_paginator_class_aserialize(mocker):
    mocked_queryset = mocker.AsyncMock()
    mocked_queryset.acount.return_value = 11

    async def genfunc(self):
        yield {"field": "hola"}
        yield {"field": "hola"}
    iterator = mocker.AsyncMock()
    iterator.__aiter__ = genfunc
    mocked_queryset.__getitem__.return_value = iterator
    mocked_model = mocker.MagicMock()
    mocked_model.from_orm.return_value = {'field': 'hola'}
    paginator = _RQLLimitOffsetPaginator('eq(field,name)&limit=10000&offset=2', 100)
    response = await paginator.aserialize(mocked_queryset, mocked_model)
    assert response.body == b'[{"field":"hola"},{"field":"hola"}]'
    assert dict(response.headers) == {
        'content-range': 'items 2-3/11',
        'content-length': '35',
        'content-type': 'application/json',
    }
    assert paginator.limit == 9
    assert paginator.offset == 2
    assert paginator.count == 11
    mocked_model.from_orm.assert_called_with({"field": "hola"})
    assert mocked_model.from_orm.call_count == 2


@pytest.mark.asyncio
async def test_rql_paginator_class_aserialize_limit_0(mocker):
    mocked_queryset = mocker.AsyncMock()
    mocked_queryset.acount.return_value = 11
    mocked_model = mocker.MagicMock()
    paginator = _RQLLimitOffsetPaginator('limit=0', 100)
    response = await paginator.aserialize(mocked_queryset, mocked_model)
    assert response.body == b'[]'
    assert dict(response.headers) == {
        'content-range': 'items 0-0/11',
        'content-length': '2',
        'content-type': 'application/json',
    }
    assert paginator.limit == 0
    assert paginator.offset == 0
    assert paginator.count == 11
    mocked_model.from_orm.assert_not_called()


@pytest.mark.asyncio
async def test_rql_paginator_class_aserialize_count_0(mocker):
    mocked_queryset = mocker.AsyncMock()
    mocked_queryset.acount.return_value = 0
    mocked_model = mocker.MagicMock()
    paginator = _RQLLimitOffsetPaginator('', 100)
    response = await paginator.aserialize(mocked_queryset, mocked_model)
    assert response.body == b'[]'
    assert dict(response.headers) == {
        'content-range': 'items 0-0/0',
        'content-length': '2',
        'content-type': 'application/json',
    }
    assert paginator.limit == 100
    assert paginator.offset == 0
    assert paginator.count == 0
    mocked_model.from_orm.assert_not_called()


@pytest.mark.asyncio
async def test_rql_paginator_class_aserialize_offset_higher_count(mocker):
    mocked_queryset = mocker.AsyncMock()
    mocked_queryset.acount.return_value = 5
    mocked_model = mocker.MagicMock()
    paginator = _RQLLimitOffsetPaginator('offset=10', 100)
    response = await paginator.aserialize(mocked_queryset, mocked_model)
    assert response.body == b'[]'
    assert dict(response.headers) == {
        'content-range': 'items 10-10/5',
        'content-length': '2',
        'content-type': 'application/json',
    }
    assert paginator.limit == 100
    assert paginator.offset == 10
    assert paginator.count == 5
    mocked_model.from_orm.assert_not_called()


@pytest.mark.asyncio
async def test_rql_paginator_class_aserialize_limit_offset_not_higher_count(mocker):
    mocked_queryset = mocker.AsyncMock()
    mocked_queryset.acount.return_value = 9

    async def genfunc(self):
        yield {"field": "hola"}
        yield {"field": "hola"}
    iterator = mocker.AsyncMock()
    iterator.__aiter__ = genfunc
    mocked_queryset.__getitem__.return_value = iterator
    mocked_model = mocker.MagicMock()
    mocked_model.from_orm.return_value = {'field': 'hola'}
    paginator = _RQLLimitOffsetPaginator('offset=5&limit=4', 100)
    response = await paginator.aserialize(mocked_queryset, mocked_model)
    assert response.body == b'[{"field":"hola"},{"field":"hola"}]'
    assert dict(response.headers) == {
        'content-range': 'items 5-6/9',
        'content-length': '35',
        'content-type': 'application/json',
    }
    assert paginator.limit == 4
    assert paginator.offset == 5
    assert paginator.count == 9
    mocked_model.from_orm.assert_called_with({"field": "hola"})
    assert mocked_model.from_orm.call_count == 2


def test_rql_paginator_class_sanitize_limit_error(mocker):
    paginator = _RQLLimitOffsetPaginator('limit=10', 150)
    mocked_positive_int = mocker.patch.object(
        paginator,
        'positive_int',
        side_effect=ValueError(),
    )
    paginator.extract_limit_offset_from_rql()
    assert paginator.sanitize_limit() == 150
    mocked_positive_int.assert_called_with(
        '10',
        strict=False,
        cutoff=1000,
    )


@pytest.mark.parametrize(
    'error',
    (AttributeError, TypeError),
)
def test_rql_paginator_class_get_count_error(mocker, error):
    paginator = _RQLLimitOffsetPaginator('', 150)
    mocked_queryset = mocker.MagicMock()
    mocked_queryset.__len__.return_value = 5
    mocked_queryset.count.side_effect = error()
    assert paginator.get_count(mocked_queryset) == 5


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'error',
    (AttributeError, TypeError),
)
async def test_rql_paginator_class_aget_count_error(mocker, error):
    paginator = _RQLLimitOffsetPaginator('', 150)
    mocked_queryset = mocker.AsyncMock()
    mocked_queryset.__len__.return_value = 5
    mocked_queryset.acount.side_effect = error()
    assert await paginator.aget_count(mocked_queryset) == 5


def test_rql_paginator_class_sanitize_offset_error(mocker):
    paginator = _RQLLimitOffsetPaginator('offset=10', 150)
    mocked_positive_int = mocker.patch.object(
        paginator,
        'positive_int',
        side_effect=ValueError(),
    )
    paginator.extract_limit_offset_from_rql()
    assert paginator.sanitize_offset() == 0
    mocked_positive_int.assert_called_with(
        '10',
    )


def test_rql_paginator_class_positive_int_error(mocker):
    paginator = _RQLLimitOffsetPaginator('offset=10', 150)
    with pytest.raises(ValueError):
        paginator.positive_int('-1')
        paginator.positive_int('0', strict=True)


def test_filter_queryset(
    mocker,
):
    base_qs = mocker.MagicMock()
    filtered_qs = mocker.MagicMock()
    model = mocker.MagicMock()
    model.objects.all.return_value = base_qs
    filter_instance = mocker.MagicMock()
    filter_cls = mocker.MagicMock(return_value=filter_instance)
    filter_cls.MODEL = model
    filter_instance.apply_filters.return_value = (None, filtered_qs)

    mocked_request = mocker.MagicMock()
    mocked_request.scope = {'query_string': b'xxx'}

    f = RQLFilteredQuerySet(filter_cls).dependency
    assert f(mocked_request) == filtered_qs
    filter_cls.assert_called_once_with(base_qs)
    filter_instance.apply_filters.assert_called_once_with('xxx')


def test_paginator(
    mocker,
):
    mocked_request = mocker.MagicMock()
    mocked_request.scope = {'query_string': b'xxx'}

    mocked_cls = mocker.MagicMock()
    mocker.patch(
        'connect.eaas.core.contrib.django.rql._RQLLimitOffsetPaginator',
        mocked_cls,
    )

    f = RQLLimitOffsetPaginator().dependency
    mocked_instance = f(mocked_request)
    mocked_cls.assert_called_once_with(
        'xxx',
        100,
    )
    assert mocked_instance == mocked_cls()
