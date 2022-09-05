from django.db.models.expressions import Expression, F, Q


class ExpressionCol(Expression):
    contains_aggregate = False

    def __init__(self, expression, model, alias=None, target=None):
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
            parent_alias, _ = query.table_alias(query.model._meta.db_table)
            # We need to work out the path we need to rewrite the F() expression(s) to contain.
            alias, _ = query.table_alias(self.model._meta.db_table)
            while True:
                join = query.alias_map[alias]
                # We need to see which end of this join we need to look up: either name or related_query_name()
                model = join.join_field.model
                if query.table_alias(model._meta.db_table) == join.table_alias:
                    # This is a join that uses a field on the model we are looking at, so
                    # we need the related_query_name
                    expression = retarget_f_expression(expression, join.join_field.related_query_name())
                else:
                    expression = retarget_f_expression(expression, join.join_field.name)
                alias = join.parent_alias
                if alias == parent_alias:
                    break

        # Remove duplicate paths.

        return expression.resolve_expression(query)

    def as_sql(self, compiler, connection):
        resolved = self._resolve_expression(compiler.query)
        alias = getattr(resolved, "alias", None) or self.target.model._meta.db_table
        if alias not in compiler.query.table_map:
            compiler.query.setup_joins(
                self.expression.name.split("__"),
                self.model._meta,
                alias,
            )
        return resolved.as_sql(compiler, connection)

    def get_db_converters(self, connection):
        return self.target.get_db_converters(connection)


def retarget_f_expression(expression, key):
    if isinstance(expression, F):
        return F(f'{key}__{expression.name}')
    if isinstance(expression, Q):
        return Q(**{
            f'{key}__{rest}': value
            for rest, value in expression.children
        })
    expression = expression.copy()
    expression.set_source_expressions([
        retarget_f_expression(expr, key)
        for expr in expression.get_source_expressions()
    ])
    return expression
