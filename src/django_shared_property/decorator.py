# -*- coding: utf-8 -*-
from django.db.models import AutoField, Expression, F, Q
from django.db.models.constants import LOOKUP_SEP
from django.db.models.sql.query import Query
from django.utils.functional import cached_property

from .expressions import ExpressionCol
from .parser import Parser


class SharedPropertyField(AutoField):
    def __init__(self, name, expression, model):
        self.expression = expression
        self.model = model
        super().__init__()
        self.set_attributes_from_name(name)
        self.db_returning = False

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
            self,
        )

    @property
    def output_field(self):
        if getattr(self.expression, 'output_field', None):
            return self.expression.output_field
        return self.expression.resolve_expression(Query(self.model)).output_field

    def contribute_to_class(self, cls, name, **kwargs):
        if cls != self.model:
            # Adding to a concrete subclass.
            field = SharedPropertyField(name, expression=self.expression, model=cls)
            cls._meta.add_field(field, private=True)


def _shared_property_dependencies(model, name, seen=frozenset()):
    field = model._meta.get_field(name)
    if not isinstance(field, SharedPropertyField) or name in seen:
        return set()
    return _expression_dependencies(model, field.expression, seen | {name})


def _expression_dependencies(model, expression, seen):
    if isinstance(expression, F):
        return _reference_dependencies(model, expression.name, seen)

    dependencies = set()
    if isinstance(expression, Q):
        expressions = expression.children
    elif hasattr(expression, 'get_source_expressions'):
        expressions = expression.get_source_expressions()
    else:
        return dependencies

    for child in expressions:
        if isinstance(child, tuple):
            dependencies.update(_reference_dependencies(model, child[0], seen))
            dependencies.update(_expression_dependencies(model, child[1], seen))
        else:
            dependencies.update(_expression_dependencies(model, child, seen))
    return dependencies


def _reference_dependencies(model, reference, seen):
    name, separator, _ = reference.partition(LOOKUP_SEP)
    field = model._meta.get_field(name)
    if separator and field.is_relation:
        return set()
    if isinstance(field, SharedPropertyField):
        return _shared_property_dependencies(model, name, seen)
    if field.concrete:
        return {field.name}
    return set()


_add_immediate_loading = Query.add_immediate_loading


def _add_immediate_loading_with_shared_property_dependencies(query, field_names):
    expanded_field_names = set(field_names)
    for field_name in field_names:
        if LOOKUP_SEP not in field_name:
            expanded_field_names.update(
                _shared_property_dependencies(query.model, field_name),
            )
    _add_immediate_loading(query, expanded_field_names)


Query.add_immediate_loading = _add_immediate_loading_with_shared_property_dependencies


def _shared_property_field(options, lookup):
    name = lookup.split(LOOKUP_SEP, 1)[0]
    return next(
        (field for field in options.private_fields if field.name == name),
        None,
    )


def _resolve_shared_property_joins(query, filter_expr, **kwargs):
    if not isinstance(filter_expr, tuple) or not isinstance(filter_expr[0], str):
        return

    field = _shared_property_field(query.get_meta(), filter_expr[0])
    if field is not None:
        field.expression.resolve_expression(query, **kwargs)


_build_filter = Query.build_filter


def _build_filter_with_shared_property_joins(
    self,
    filter_expr,
    branch_negated=False,
    current_negated=False,
    can_reuse=None,
    allow_joins=True,
    split_subq=True,
    check_filterable=True,
    summarize=False,
    update_join_types=True,
):
    _resolve_shared_property_joins(
        self,
        filter_expr,
        allow_joins=allow_joins,
        reuse=can_reuse,
        summarize=summarize,
    )
    return _build_filter(
        self,
        filter_expr,
        branch_negated=branch_negated,
        current_negated=current_negated,
        can_reuse=can_reuse,
        allow_joins=allow_joins,
        split_subq=split_subq,
        check_filterable=check_filterable,
        summarize=summarize,
        update_join_types=update_join_types,
    )


Query.build_filter = _build_filter_with_shared_property_joins


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
        if self.callable.__name__ in instance.__dict__ and self.callable(instance) != value:
            raise ValueError('Setting a value that does not match the calculated value is unsupported')
        # However, to prevent an issue where it thinks we
        # have deferred_fields, we want to also store the
        # value on the instance.
        instance.__dict__[self.callable.__name__] = value

    def contribute_to_class(self, cls, name, private_only=False):
        field = SharedPropertyField(name, expression=self.expression, model=cls)
        cls._meta.add_field(field, private=True)
        setattr(cls, field.attname, self)

    def property(self, method):
        return self(method)
