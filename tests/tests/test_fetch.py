from ..models import Person


def test_defer_works():
    Person.objects.create(first_name="Foo", last_name="Bar")
    person = Person.objects.defer('useless').get()
    assert person.useless == 'Useless'


def test_only_works():
    Person.objects.create(first_name="Foo", last_name="Bar")
    person = Person.objects.only('useless').get()
    assert person.useless == 'Useless'


def test_only_includes_dependencies():
    Person.objects.create(first_name="Foo", last_name="Bar")
    person = Person.objects.only('name').get()
    assert person.first_name == 'Foo'
    assert person.last_name == 'Bar'
