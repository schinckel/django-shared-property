from django.db.models.expressions import Expression, F
from django.db.models.sql.query import Query


class ExpressionCol(Expression):
    contains_aggregate = False

    def __init__(self, expression, model, alias=None, output_field=None):
        self.expression = expression
        if output_field:
            self.output_field = output_field
        self.alias = alias
        self.model = model

    def get_lookup(self, name):
        return self.output_field.get_lookup(name)

    def get_transform(self, name):
        return self.output_field.get_transform(name)

    def as_sql(self, compiler, connection):
        resolved = self.expression.resolve_expression(compiler.query)
        return resolved.as_sql(compiler, connection)

    def get_db_converters(self, connection):
        return self.output_field.get_db_converters(connection) + self.expression.get_db_converters(connection)

    def resolve_expression(self, *args, **kwargs):
        return self.expression.resolve_expression(Query(self.model))
