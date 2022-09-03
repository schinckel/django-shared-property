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

    def as_sql(self, compiler, connection):
        expression = self.target.expression
        if compiler.query.model != self.model:
            expression = retarget_f_expression(
                expression, get_retarget_key(self.model, compiler.query.model)
            )
        resolved = expression.resolve_expression(compiler.query)
        alias = getattr(resolved, "alias", None) or self.target.model._meta.db_table
        if alias not in compiler.query.table_map:
            compiler.query.setup_joins(
                expression.name.split("__"),
                self.model._meta,
                alias,
            )
        return resolved.as_sql(compiler, connection)

    def get_db_converters(self, connection):
        return self.target.get_db_converters(connection)


def get_retarget_key(from_model, to_model):
    for field in from_model._meta.fields:
        if field.related_model == to_model:
            return field.related_query_name()
    for field in to_model._meta.fields:
        if field.related_model == from_model:
            return field.name
    raise ValueError('Unable to detect relation')


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
