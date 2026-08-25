from ast import Constant, Return, fix_missing_locations
from types import SimpleNamespace

import pytest
from django.db.models import Case, Q, Value, When
from django.db.models.expressions import CombinedExpression, F
from django.db.models.functions import Concat, Left, Length, Lower, Replace, Reverse, Right, Upper

from django_shared_property.parser import Parser, _extensions, register


def compile_parser(function):
    parser = Parser(function)
    namespace = {}
    exec(parser.code, namespace)
    return namespace[function.__name__]


def test_parser_preserves_none_and_boolean_values():
    def returns_none(_):
        return None

    def returns_true(_):
        return True

    assert compile_parser(returns_none)(SimpleNamespace()) is None
    assert compile_parser(returns_true)(SimpleNamespace()) is True


def test_parser_case_without_default_returns_none_when_no_condition_matches():
    def conditional_value(_):
        return Case(
            When(Q(first_name=Value("Foo")), then=Value("matched")),
        )

    compiled = compile_parser(conditional_value)
    assert compiled(SimpleNamespace(first_name="Foo")) == "matched"
    assert compiled(SimpleNamespace(first_name="Bar")) is None


def test_parser_when_without_following_expressions_has_an_implicit_none_result():
    def placeholder(_):
        return Value("placeholder")

    parser = Parser(placeholder)
    parser.ast.body[0].body = [
        parser.handle_when(When(Q(first_name=Value("Foo")), then=Value("matched"))),
    ]
    parser.code = compile(fix_missing_locations(parser.ast), mode="exec", filename=__file__)
    namespace = {}
    exec(parser.code, namespace)

    assert namespace["placeholder"](SimpleNamespace(first_name="Foo")) == "matched"
    assert namespace["placeholder"](SimpleNamespace(first_name="Bar")) is None


def test_parser_supports_empty_q_and_combined_comparisons():
    def empty_condition(_):
        return Q()

    def greater_than_one(_):
        return CombinedExpression(F("number"), ">", Value(1))

    assert compile_parser(empty_condition)(SimpleNamespace()) is True
    compiled = compile_parser(greater_than_one)
    assert compiled(SimpleNamespace(number=2)) is True
    assert compiled(SimpleNamespace(number=1)) is False


def test_parser_rejects_unsupported_lookup_types():
    def unsupported_lookup(_):
        return Q(first_name__icontains=Value("Foo"))

    with pytest.raises(ValueError, match="Unhandled attr lookup"):
        Parser(unsupported_lookup)

    def unsupported_value(_):
        return Value(1.5)

    with pytest.raises(ValueError, match="Unhandled Value"):
        Parser(unsupported_value)


def test_parser_compiles_supported_text_expressions_with_nested_sources():
    def text_length(_):
        return Length(F("text"))

    def replace_text(_):
        return Replace(F("text"), F("search"), F("replacement"))

    def reverse_text(_):
        return Reverse(F("text"))

    def left_text(_):
        return Left(Lower(F("text")), F("width"))

    def right_text(_):
        return Right(F("text"), F("width"))

    value = SimpleNamespace(text="ABCD", search="B", replacement="_", width=2)
    assert compile_parser(text_length)(value) == 4
    assert compile_parser(replace_text)(value) == "A_CD"
    assert compile_parser(reverse_text)(value) == "DCBA"
    assert compile_parser(left_text)(value) == "ab"
    assert compile_parser(right_text)(value) == "CD"


def test_parser_uses_null_safe_runtime_for_existing_handlers(monkeypatch):
    monkeypatch.delitem(_extensions, "handle_upper", raising=False)

    def lower_text(_):
        return Lower(F("text"))

    def upper_text(_):
        return Upper(F("text"))

    def concat_text(_):
        return Concat(F("left"), F("right"))

    def add_numbers(_):
        return F("number") + Value(1)

    value = SimpleNamespace(text=None, left="left", right=None, number=None)
    assert compile_parser(lower_text)(value) is None
    assert compile_parser(upper_text)(value) is None
    assert compile_parser(concat_text)(value) == "left"
    assert compile_parser(add_numbers)(value) is None


def test_string_registered_handler_may_return_a_statement_list(monkeypatch):
    class StatementListExpression:
        pass

    def handle_statement_list(self, expression):
        return [Return(value=Constant(value="registered"), **self.file)]

    handler_name = "handle_statementlistexpression"
    monkeypatch.delitem(_extensions, handler_name, raising=False)
    registered_handler = register("statementlistexpression")(handle_statement_list)

    def registered_value(_):
        return StatementListExpression()

    assert registered_handler is handle_statement_list
    assert compile_parser(registered_value)(SimpleNamespace()) == "registered"


def test_registered_handler_names_are_normalized(monkeypatch):
    def normalized_name(self, expression):
        return Constant(value="normalized", **self.file)

    handler_name = "handle_normalized_name"
    monkeypatch.delitem(_extensions, handler_name, raising=False)
    register(normalized_name)

    assert _extensions[handler_name] is normalized_name
