# -*- coding: utf-8 -*-
from django.db.models import F
from django.db.models.sql.query import Query

from .expressions import ExpressionCol
from .parser import Parser


def pre_resolve(expression, model):
    if isinstance(expression, F):
        query = Query(model)
        return expression.resolve_expression(query)

    return expression


class shared_property(object):
    def __init__(self, func):
        try:
            self.parsed = Parser(func)
            self.expression = self.parsed.expression
            self.func = func
            context = {}
            eval(self.parsed.code, context)
            self.callable = context[(getattr(func, "__code__", None) or func.func_code).co_name]
        except TypeError:
            self.expression = func

    def __call__(self, method):
        self.callable = method
        return self

    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        return self.callable(instance)

    def __set__(self, instance, value):
        pass

    def contribute_to_class(self, cls, name, private_only=False):
        # Try to resolve any F() expressions
        # resolved = self.resolve_expression(self.parsed.expression, cls)
        #
        # @receiver(class_prepared, weak=False, sender=cls)
        # def finish(sender, **kwargs):

        expression = self.expression

        if getattr(expression, "output_field", None) is None:
            resolved = pre_resolve(expression, cls)
            output_field = resolved.output_field
        else:
            output_field = expression.output_field

        if output_field.name:
            _name, _class, args, kwargs = output_field.deconstruct()
            field = output_field.__class__(*args, **kwargs)
        else:
            field = output_field

        field.set_attributes_from_name(name)
        field.model = cls
        field.concrete = False
        field.cached_col = ExpressionCol(expression, cls, output_field)
        field.get_col = lambda alias, _output_field=None: ExpressionCol(expression, cls, alias, output_field)
        cls._meta.add_field(field, private=True)
        if not getattr(cls, field.attname, None):
            setattr(cls, field.attname, self)

    def property(self, method):
        return self(method)
