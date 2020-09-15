# -*- coding: utf-8 -*-

from .expressions import ExpressionCol
from .parser import Parser


class shared_property(object):
    def __init__(self, func):
        self.parsed = Parser(func)
        self.func = func
        context = {}
        eval(self.parsed.code, context)
        self.callable = context[func.func_code.co_name]

    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        return self.callable(instance)

    def contribute_to_class(self, cls, name, private_only=False):
        field = self.parsed.expression.output_field
        field.set_attributes_from_name(name)
        field.model = cls
        field.concrete = False
        field.cached_col = ExpressionCol(self.parsed.expression)
        cls._meta.add_field(field, private=True)
        if not getattr(cls, field.attname, None):
            setattr(cls, field.attname, self)
