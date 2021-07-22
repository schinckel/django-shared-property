# -*- coding: utf-8 -*-
from django.db.models import Expression, F, AutoField
from django.db.models.sql.query import Query
from django.utils.functional import cached_property

from .expressions import ExpressionCol
from .parser import Parser


class SharedPropertyField(AutoField):
    def __init__(self, name, expression, model):
        self.expression = expression
        self.model = model
        self.concrete = False
        super().__init__()
        self.set_attributes_from_name(name)

    def get_col(self, alias, output_field=None):
        if alias != self.model._meta.db_table or output_field != self:
            return ExpressionCol(
                self.expression,
                self.model,
                alias,
                output_field or self,
            )
        return self.cached_col
    
    @cached_property
    def cached_col(self):
        return ExpressionCol(
            self.expression,
            self.model,
            self.model._meta.db_table,
            self
        )
    
    @cached_property
    def resolved_expression(self):
        return self.expression.resolve_expression(Query(self.model))
        

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
