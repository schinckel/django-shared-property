# -*- coding: utf-8 -*-
from django.db.models import Expression, F, Field
from django.db.models.sql.query import Query

from .expressions import ExpressionCol
from .parser import Parser


class SharedPropertyField(Field):
    def __init__(self, name, expression, model):
        self.expression = expression
        self.model = model
        self.concrete = False
        super().__init__()
        self.set_attributes_from_name(name)

    def get_col(self, alias, output_field=None):
        return ExpressionCol(
            self.expression,
            self.model,
            alias,
            self.expression.resolve_expression(Query(self.model)).output_field,
            self,
        )


class shared_property(object):
    def __init__(self, func):
        if isinstance(func, (Expression, F)):
            self.expression = func
        else:
            self.parsed = Parser(func)
            self.expression = self.parsed.expression
            self.func = func
            context = dict(func.__globals__)
            eval(self.parsed.code, context)
            self.callable = context[func.__code__.co_name]

    def __call__(self, method):
        self.callable = method
        return self

    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        return self.callable(instance)

    def __set__(self, instance, value):
        # We don't really do anything with the value - but we need to
        # override this otherwise instance.refresh_from_db() would stomp
        # over our values.
        self.value = value

    def contribute_to_class(self, cls, name, private_only=False):
        field = SharedPropertyField(name, expression=self.expression, model=cls)
        cls._meta.add_field(field, private=True)
        if not getattr(cls, field.attname, None):
            setattr(cls, field.attname, self)

    def property(self, method):
        return self(method)
