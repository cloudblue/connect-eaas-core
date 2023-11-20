from typing import Callable
from urllib.parse import unquote

from dj_rql.filter_cls import RQLFilterClass
from dj_rql.transformer import RQLLimitOffsetTransformer
from django.db.models.query import QuerySet
from fastapi import Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from lark.exceptions import LarkError
from py_rql.exceptions import RQLFilterParsingError
from py_rql.parser import RQLParser


class _RQLLimitOffsetPaginator:

    def __init__(self, query, default_limit):
        self.query = query
        self.default_limit = default_limit

    def extract_limit_offset_from_rql(self):
        rql_ast = RQLParser.parse_query(self.query)
        try:
            self._rql_limit, self._rql_offset = RQLLimitOffsetTransformer().transform(rql_ast)
        except LarkError:
            raise RQLFilterParsingError(
                details={
                    'error': 'Limit and offset are set incorrectly.',
                },
            )

    def serialize(self, queryset, model):
        self.extract_limit_offset_from_rql()
        self.limit = self.sanitize_limit()
        self.count = self.get_count(queryset)
        if self.limit == 0:
            self.offset = 0
            body = []
        else:
            self.offset = self.sanitize_offset()
            if self.count == 0 or self.offset > self.count:
                body = []
            else:
                if self.limit + self.offset > self.count:
                    self.limit = self.count - self.offset
                body = [
                    dict(jsonable_encoder(model.from_orm(item)))
                    for item in queryset[self.offset: self.offset + self.limit]
                ]

        return JSONResponse(
            body,
            headers=self.get_content_range_header(body),
        )

    async def aserialize(self, queryset, model):
        self.extract_limit_offset_from_rql()
        self.limit = self.sanitize_limit()
        self.count = await self.aget_count(queryset)
        if self.limit == 0:
            self.offset = 0
            body = []
        else:
            self.offset = self.sanitize_offset()
            if self.count == 0 or self.offset > self.count:
                body = []
            else:
                if self.limit + self.offset > self.count:
                    self.limit = self.count - self.offset
                body = [
                    dict(jsonable_encoder(model.from_orm(item)))
                    async for item in queryset[self.offset: self.offset + self.limit]
                ]

        return JSONResponse(
            body,
            headers=self.get_content_range_header(body),
        )

    def get_content_range_header(self, data):
        length = len(data) - 1 if data else 0
        content_range = 'items {0}-{1}/{2}'.format(
            self.offset,
            self.offset + length,
            self.count,
        )
        return {'Content-Range': content_range}

    def sanitize_limit(self):
        if self._rql_limit is not None:
            try:
                return self.positive_int(self._rql_limit, strict=False, cutoff=1000)
            except ValueError:
                pass
        return self.default_limit

    def get_count(self, queryset):
        try:
            return queryset.count()
        except (AttributeError, TypeError):
            return len(queryset)

    async def aget_count(self, queryset):
        try:
            return await queryset.acount()
        except (AttributeError, TypeError):
            return len(queryset)

    def sanitize_offset(self):
        if self._rql_offset is not None:
            try:
                return self.positive_int(self._rql_offset)
            except ValueError:
                pass
        return 0

    def positive_int(self, integer_string, strict=False, cutoff=None):
        ret = int(integer_string)
        if ret < 0 or (ret == 0 and strict):
            raise ValueError()
        if cutoff:
            return min(ret, cutoff)
        return ret


def RQLFilteredQuerySet(
    filter_cls: RQLFilterClass,
    base_queryset: Callable[[], QuerySet] = None,
):
    def _wrapper(
        request: Request,
    ) -> QuerySet:

        query = unquote(request.scope.get('query_string', b'').decode())
        queryset = base_queryset() if base_queryset else filter_cls.MODEL.objects.all()
        filter_instance = filter_cls(queryset)
        _, qs = filter_instance.apply_filters(query)
        return qs
    return Depends(_wrapper)


def RQLLimitOffsetPaginator(
    default_limit=100,
):
    def _wrapper(
        request: Request,
    ):
        return _RQLLimitOffsetPaginator(
            unquote(request.scope.get('query_string', b'').decode()),
            default_limit,
        )
    return Depends(_wrapper)
