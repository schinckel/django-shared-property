from ..models import Person


def test_defer_works():
    Person.objects.create(first_name="Foo", last_name="Bar")
    person = Person.objects.defer('useless').get()
    assert 'useless' not in person.__dict__
    assert 'active' in person.__dict__


def test_only_works():
    Person.objects.create(first_name="Foo", last_name="Bar")
    person = Person.objects.only('useless').get()
    assert 'useless' in person.__dict__
    assert 'active' not in person.__dict__


def test_only_includes_dependencies():
    Person.objects.create(first_name="Foo", last_name="Bar")
    person = Person.objects.only('name').get()
    assert 'first_name' in person.__dict__
    assert 'last_name' in person.__dict__
