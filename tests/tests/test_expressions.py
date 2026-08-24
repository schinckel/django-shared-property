from types import SimpleNamespace

from django.db.models import F

from django_shared_property.expressions import ExpressionCol, resolve

from ..models import Address, Person


class ResolvesToModel:
    def resolve_expression(self, query):
        return query.model


class SourceExpression:
    def __init__(self, *children):
        self.children = children

    def get_source_expressions(self):
        return self.children

    def set_source_expressions(self, children):
        self.children = children


class ResolvableSourceExpression(SourceExpression):
    def resolve_expression(self, query):
        return self


class MissingAliasQuery:
    def __init__(self, model):
        self.model = model
        self.alias_map = {}

    def table_alias(self, table_name):
        raise KeyError(table_name)


def test_resolve_recurses_into_expression_containers():
    class ResolvesToValue:
        def resolve_expression(self, query):
            return "resolved"

    source = SourceExpression(ResolvesToValue())
    resolved = resolve(source, object())

    assert resolved is not source
    assert resolved.get_source_expressions() == ["resolved"]


def test_resolution_without_query_aliases_uses_the_property_model_query():
    target = SimpleNamespace(expression=ResolvesToModel())
    column = ExpressionCol(F("first_name"), Person, target=target)

    assert column._resolve_expression(MissingAliasQuery(Address)) is Person


def test_resolution_retargets_a_relation_when_its_model_alias_is_missing():
    class RelationshipQuery:
        def __init__(self, model):
            self.model = model
            self.alias_map = {
                "person_alias": SimpleNamespace(
                    join_field=Address._meta.get_field("person"),
                    table_alias=Address._meta.db_table,
                    parent_alias="address_alias",
                ),
            }
            self._address_alias_lookups = 0

        def table_alias(self, table_name):
            if table_name == Address._meta.db_table:
                self._address_alias_lookups += 1
                if self._address_alias_lookups == 1:
                    return "address_alias", False
                raise KeyError(table_name)
            if table_name == Person._meta.db_table:
                return "person_alias", False
            raise AssertionError(table_name)

    expression = ResolvableSourceExpression(F("first_name"))
    target = SimpleNamespace(expression=expression)
    column = ExpressionCol(F("first_name"), Person, target=target)

    resolved = column._resolve_expression(RelationshipQuery(Address))

    assert resolved.get_source_expressions()[0].name == "address__first_name"
