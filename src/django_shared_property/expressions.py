from django.db.models.functions import Coalesce
from django.db.models.lookups import Lookup
from django.db.models.expressions import Expression, F, Q, Value
from django.utils.functional import cached_property
from copy import deepcopy
import django


class ExpressionCol(Expression):
    contains_aggregate = False

    def __init__(self, expression, model, alias=None, target=None):
        if django.VERSION < (4, 0):
            if isinstance(expression, Coalesce) and any(
                isinstance(exp, Value)
                for exp in expression.get_source_expressions()
            ):
                expression.set_source_expressions([
                    exp.value if isinstance(exp, Value) and isinstance(exp.value, Lookup) else exp
                    for exp in expression.get_source_expressions()
                ])
        self.expression = expression
        self.alias = alias
        self.model = model
        self.target = target

    @property
    def output_field(self):
        return self.target.output_field

    def get_lookup(self, name):
        return self.target.get_lookup(name)

    def get_transform(self, name):
        return self.target.get_transform(name)

    def _resolve_expression(self, query):
        expression = self.target.expression
        if query.model != self.model:
            if isinstance(expression, (F, Q)) and '__' in expression.name:
                resolved = query.__class__(self.model).resolve_ref(expression.name)
                if getattr(resolved, 'model', None) == query.model:
                    return resolved
            try:
                parent_alias, _ = query.table_alias(query.model._meta.db_table)
            except KeyError:
                parent_alias = query.model._meta.db_table
            # We need to work out the path we need to rewrite the F() expression(s) to contain.
            try:
                alias, _ = query.table_alias(self.model._meta.db_table)
            except KeyError:
                alias = self.model._meta.db_table

            if alias not in query.alias_map:
                # This could be a subquery, with an OuterRef.
                return expression.resolve_expression(query.__class__(self.model))

            while True:
                join = query.alias_map[alias]
                # We need to see which end of this join we need to look up: either name or related_query_name()
                model = join.join_field.model
                try:
                    _model_alias, _ = query.table_alias(model._meta.db_table)
                except KeyError:
                    _model_alias = model._meta.db_table

                if _model_alias == join.table_alias:
                    # This is a join that uses a field on the model we are looking at, so
                    # we need the related_query_name
                    expression = retarget_f_expression(expression, join.join_field.related_query_name())
                else:
                    expression = retarget_f_expression(expression, join.join_field.name)
                alias = join.parent_alias
                if alias == parent_alias:
                    break

        return resolve(expression, query)

    def as_sql(self, compiler, connection):
        resolved = self._resolve_expression(compiler.query)
        alias = getattr(resolved, "alias", None) or self.target.model._meta.db_table
        if alias not in compiler.query.table_map:
            compiler.query.setup_joins(
                self.expression.name.split("__"),
                self.model._meta,
                alias,
            )
        vendor_impl = getattr(resolved, "as_" + connection.vendor, None)
        if vendor_impl:
            return vendor_impl(compiler, connection)
        return resolved.as_sql(compiler, connection)

    @staticmethod
    def _converter(value, expression, connection):
        # expression is ExpressionCol instance. Get underlying expression and use its converter
        underlying_expr = expression.expression
        return underlying_expr.convert_value(value, underlying_expr, connection)

    @cached_property
    def convert_value(self):
        if hasattr(self.expression, 'convert_value'):  # not present on e.g. Combinable subclasses like F()
            if self.expression.convert_value == self.expression._convert_value_noop:
                return self._convert_value_noop
            else:
                return self._converter
        else:
            return super().convert_value


def resolve(exp, query):
    try:
        return exp.resolve_expression(query)
    except AttributeError:
        exp = deepcopy(exp)
        exp.set_source_expressions([
            resolve(x, query) for x in exp.get_source_expressions()
        ])
        return exp


def retarget_f_expression(expression, key):
    if isinstance(expression, F):
        return F(f'{key}__{expression.name}')
    if isinstance(expression, Q):
        return Q(**{
            f'{key}__{rest}': value
            for rest, value in expression.children
        })
    expression = deepcopy(expression)
    expression.set_source_expressions([
        retarget_f_expression(expr, key)
        for expr in expression.get_source_expressions()
    ])
    return expression
