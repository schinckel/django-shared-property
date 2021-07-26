from django.db.models.expressions import Expression


class ExpressionCol(Expression):
    contains_aggregate = False

    def __init__(self, expression, model, alias=None, target=None):
        self.expression = expression
        self.alias = alias
        self.model = model
        self.target = target
        self.output_field = target.resolved_expression.output_field

    def get_lookup(self, name):
        return self.target.get_lookup(name)

    def get_transform(self, name):
        return self.target.get_transform(name)

    def as_sql(self, compiler, connection):
        resolved = self.target.expression.resolve_expression(compiler.query)
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
