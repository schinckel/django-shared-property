import pytest
from django.db import models
from django.db.models.functions import Length

from django_shared_property.decorator import shared_property

from ..models import Person


def test_computed_field_exists_and_can_be_queried():
    assert not Person.objects.filter(name="foo bar").exists()


def test_values_query_result_includes_column():
    Person.objects.create(first_name="Foo", last_name="Bar")
    assert Person.objects.values()[0]["name"] == "Foo Bar"


def test_create_works():
    Person.objects.create(first_name="Foo", last_name="Bar")


def test_computed_field_is_set_on_object():
    Person.objects.create(first_name="Foo", last_name="Bar")
    assert Person.objects.get().name == "Foo Bar"


def test_computed_field_is_set_on_values():
    Person.objects.create(first_name="Foo", last_name="Bar")
    assert Person.objects.values("name")[0] == {"name": "Foo Bar"}


def test_filter_on_computed_field():
    assert not Person.objects.filter(name="Foo Bar").exists()
    Person.objects.create(first_name="Foo", last_name="Bar")
    assert Person.objects.filter(name="Foo Bar").exists()


def test_filter_transform_on_computed_field():
    Person.objects.create(first_name="Foo", last_name="Bar")
    assert Person.objects.filter(name__icontains="foo").exists()


def test_filter_registered_transform_on_computed_field():
    models.TextField.register_lookup(Length)
    Person.objects.create(first_name="Foo", last_name="Bar")
    assert Person.objects.filter(name__length=7).exists()


def test_cascading_field():
    Person.objects.create(first_name="Foo", last_name="Bar")
    assert Person.objects.filter(lower_name="foo bar").exists()


def test_ordering():
    assert len(Person.objects.order_by("name")) == 0


def test_property_behaviour():
    assert Person(first_name="Foo", last_name="Bar").name == "Foo Bar"


def test_class_access_returns_shared_property_descriptor():
    assert isinstance(Person.name, shared_property)


def test_coalesce_property_falls_back_and_can_be_queried():
    person = Person.objects.create(first_name="Foo", last_name="Bar")
    assert person.fallback_name == "Foo"
    assert Person.objects.filter(fallback_name="Foo").get() == person


def test_expression_wrapper_property_can_be_queried():
    person = Person.objects.create(first_name="Foo", last_name="Bar")
    assert person.wrapped_first_name == "Foo"
    assert Person.objects.filter(wrapped_first_name="Foo").get() == person


def test_none_value_property_can_be_queried():
    person = Person.objects.create(first_name="Foo", last_name="Bar")
    assert person.no_preferred_name is None
    assert Person.objects.filter(no_preferred_name__isnull=True).get() == person


def test_raw_f_expressions():
    assert Person(first_name="Foo", last_name="Bar").other == "Foo Bar"
    Person.objects.create(first_name="Foo", last_name="Bar")
    assert Person.objects.filter(other="Foo Bar").exists()


def test_override_callable():
    # This shows that it actually overrides, and uses the python code.
    # Normally you wouldn't do this: make it return a different value.
    assert Person(first_name="Foo", last_name="Bar").useless == "Useless"
    Person.objects.create(first_name="Foo", last_name="Bar")
    assert Person.objects.get(useless="Foo Bar").useless == "Useless"


def test_alternate_syntax():
    assert Person(first_name="Bar").alternate_syntax == "Bar"


def test_setting_value():
    person = Person.objects.create(first_name='Foo', last_name='Bar')
    with pytest.raises(
        ValueError,
        match='Setting a value that does not match the calculated value is unsupported'
    ):
        person.useless = 'WAT'

    person.useless = 'Useless'
    person.save()
