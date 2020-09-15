class ExpressionCol(object):
    contains_aggregate = False

    def __init__(self, expression):
        self.expression = expression
        self.output_field = expression.output_field

    def get_lookup(self, name):
        return self.output_field.get_lookup(name)

    def get_transform(self, name):
        return self.output_field.get_transform(name)

    def as_sql(self, compiler, connection):
        resolved = self.expression.resolve_expression(compiler.query)
        return resolved.as_sql(compiler, connection)

    def get_db_converters(self, connection):
        return self.output_field.get_db_converters(connection) + self.expression.get_db_converters(connection)
