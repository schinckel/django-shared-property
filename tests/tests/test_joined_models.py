import pytest

from ..models import Address, Person


@pytest.mark.xfail
def test_joined_lookup():
    assert len(Address.objects.filter(person__name="foo")) == 0
    assert len(Address.objects.filter(person__name__icontains="foo")) == 0


@pytest.mark.xfail
def test_select_related():
    person = Person.objects.create(first_name="Foo", last_name="Bar")
    Address.objects.create(person=person)

    assert Address.objects.select_related("person").get().person.name == "Foo Bar"
