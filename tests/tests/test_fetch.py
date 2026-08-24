from django_shared_property.decorator import _reference_dependencies

from ..models import Person


def test_defer_works():
    Person.objects.create(first_name="Foo", last_name="Bar")
    person = Person.objects.defer('useless').get()
    assert person.useless == 'Useless'


def test_only_works():
    Person.objects.create(first_name="Foo", last_name="Bar")
    person = Person.objects.only('useless').get()
    assert person.useless == 'Useless'


def test_only_loads_local_dependencies_without_follow_up_queries(django_assert_num_queries):
    Person.objects.create(first_name="Foo", last_name="Bar")
    person = Person.objects.only('name').get()

    assert {'first_name', 'last_name'}.isdisjoint(person.get_deferred_fields())
    with django_assert_num_queries(0):
        assert person.name == 'Foo Bar'

    person.first_name = 'Baz'
    assert person.name == 'Baz Bar'


def test_only_loads_chained_shared_property_dependencies(django_assert_num_queries):
    Person.objects.create(first_name="Foo", last_name="Bar")
    person = Person.objects.only('lower_name').get()

    assert {'first_name', 'last_name'}.isdisjoint(person.get_deferred_fields())
    with django_assert_num_queries(0):
        assert person.lower_name == 'foo bar'


def test_only_loads_dependencies_referenced_by_q_expressions(django_assert_num_queries):
    Person.objects.create(first_name="Foo", last_name="Bar")
    person = Person.objects.only('display_name').get()

    assert {'first_name', 'last_name', 'preferred_name'}.isdisjoint(
        person.get_deferred_fields()
    )
    with django_assert_num_queries(0):
        assert person.display_name == 'Foo Bar'


def test_only_does_not_expand_related_shared_property_dependencies():
    Person.objects.create(first_name="Foo", last_name="Bar")
    person = Person.objects.only('username').get()

    assert 'user_id' in person.get_deferred_fields()


def test_only_keeps_regular_field_selection_unchanged():
    Person.objects.create(first_name="Foo", last_name="Bar")
    person = Person.objects.only('first_name').get()

    assert person.first_name == 'Foo'
    assert 'last_name' in person.get_deferred_fields()


def test_reverse_relation_is_not_a_local_dependency():
    assert _reference_dependencies(Person, 'address', frozenset()) == set()
