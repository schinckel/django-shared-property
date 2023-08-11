import pytest
from django.conf import settings

from ..models import User, Person


def test_json_reference_works():
    User.objects.create()
    assert User.objects.filter(active=True).exists()
    user = User.objects.get()
    assert user.active
    user.data = {'fields': {'isinactive': 'T'}}
    assert not user.active
    user.save()
    assert User.objects.filter(active=False).exists()
    user = User.objects.get()
    assert not user.active
    assert user.inactive


def test_json_reference_on_joined_model_works():
    user = User.objects.create(
        data={'fields': {'isinactive': 'T'}},
        other='inactive',
    )
    Person.objects.create(user=user)
    assert Person.objects.filter(user__active=False).exists()
    assert Person.objects.filter(user__inactive=True).exists()
    assert Person.objects.filter(user__data__fields__isinactive='T').exists()


@pytest.mark.xfail(
    settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3',
    reason='Direct reference does not currently work in SQLite',
    raises=User.DoesNotExist,
)
def test_json_direct_reference():
    User.objects.create(data={'fields': {'isinactive_2': True}})
    assert User.objects.filter(inactive_2=True).get()
    User.objects.create(data={'fields': {'isinactive_2': False}})
    assert User.objects.filter(inactive_2=True).get()
    assert User.objects.filter(inactive_2=False).get()
