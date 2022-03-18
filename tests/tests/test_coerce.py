import pytest

from ..models import Person, State


@pytest.mark.skipif(State is None, reason="Django version does not support TextChoices")
def test_state_object_is_returned():
    Person.objects.create(first_name="foo", last_name="bar", active_bool=True)
    assert Person.objects.get(first_name='foo').state == State.ACTIVE


@pytest.mark.skipif(State is None, reason="Django version does not support TextChoices")
def test_can_filter_on_enum():
    Person.objects.create(first_name="foo", last_name="bar", active_bool=False)
    assert Person.objects.filter(state=State.INACTIVE).get()
