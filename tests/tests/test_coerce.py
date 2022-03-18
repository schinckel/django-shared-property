import pytest

from ..models import Person, State


@pytest.mark.skipif(State is None, reason="Django version does not support TextChoices")
def test_state_object_is_returned():
    Person.objects.create(first_name="foo", last_name="bar", active_until="2300-01-01T00:00:00Z")
    assert Person.objects.get(first_name="foo").state == State.ACTIVE
    assert Person.objects.get(first_name="foo").active


@pytest.mark.skipif(State is None, reason="Django version does not support TextChoices")
def test_can_filter_on_enum():
    Person.objects.create(first_name="foo", last_name="bar", active_until="2001-01-01T00:00:00Z")
    assert Person.objects.filter(state=State.INACTIVE).get()
    assert Person.objects.filter(active=False).get()


@pytest.mark.skipif(State is None, reason="Django version does not support TextChoices")
def test_coalesce_timestamp():
    Person.objects.create(first_name="foo", last_name="bar")
    assert Person.objects.get(first_name="foo").state == State.ACTIVE
    assert Person.objects.get(first_name="foo").active
