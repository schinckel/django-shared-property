from ..models import Person, User, Group


def test_empty_lookup():
    assert not list(Person.objects.filter(username=None))


def test_null_lookup():
    Person.objects.create(first_name='foo', last_name='bar')
    assert Person.objects.get().username is None
    assert Person.objects.filter(username=None).exists()


def test_value_lookup():
    Person.objects.create(
        first_name='foo',
        last_name='bar',
        user=User.objects.create(username='baz')
    )
    assert Person.objects.get().username == 'baz'
    assert Person.objects.filter(username='baz').exists()
    assert not Person.objects.filter(username=None).exists()


def test_multiple_lookups():
    Person.objects.create(
        first_name='foo',
        last_name='bar',
        user=User.objects.create(username='baz', group=Group.objects.create(name='qux'))
    )

    assert Person.objects.get().group == 'qux'
    assert Person.objects.filter(group='qux').exists()
    assert not Person.objects.filter(group=None).exists()
