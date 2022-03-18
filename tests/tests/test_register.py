from ..models import Person


def test_registered_function_works():
    Person.objects.create(first_name="foo", last_name="bar")
    assert Person.objects.get(first_name="foo").upper_name == "FOO BAR"


def test_can_filter_on_registered_expression():
    Person.objects.create(first_name="foo", last_name="bar")
    assert Person.objects.filter(upper_name="FOO BAR").get()
