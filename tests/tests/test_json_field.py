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
    assert user.inactive_2


def test_json_reference_on_joined_model_works():
    user = User.objects.create(
        data={'fields': {'isinactive': 'T'}},
        other='inactive',
    )
    Person.objects.create(user=user)
    assert Person.objects.filter(user__active=False).exists()
    assert Person.objects.filter(user__inactive=True).exists()
    assert Person.objects.filter(user__data__fields__isinactive='T').exists()
