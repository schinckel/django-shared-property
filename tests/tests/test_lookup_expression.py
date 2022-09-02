import pytest

from ..models import Group, Person, User


def test_empty_lookup():
    assert not list(Person.objects.filter(username=None))
    Person.objects.create(user=User.objects.create(username="foo"))
    assert not list(Person.objects.exclude(username="foo"))


def test_null_lookup():
    Person.objects.create(first_name="foo", last_name="bar")
    assert Person.objects.get().username is None
    assert Person.objects.filter(username__isnull=True)


@pytest.mark.xfail
def test_exists_query():
    Person.objects.create(first_name="foo", last_name="bar")
    assert Person.objects.filter(username=None).exists()


@pytest.mark.xfail
def test_count_query():
    Person.objects.create(first_name="foo", last_name="bar")
    assert Person.objects.filter(username=None).count()


def test_value_lookup():
    Person.objects.create(first_name="foo", last_name="bar", user=User.objects.create(username="baz"))
    assert Person.objects.get().username == "baz"


def test_multiple_lookups():
    Person.objects.create(
        first_name="foo",
        last_name="bar",
        user=User.objects.create(
            username="baz",
            group=Group.objects.create(name="qux"),
        ),
    )

    assert Person.objects.get().group == "qux"
    assert bool(Person.objects.filter(group="qux"))
    assert not bool(Person.objects.filter(group=None))
