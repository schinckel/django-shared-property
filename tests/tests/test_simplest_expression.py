from ..models import Person


def test_computed_field_exists_and_can_be_queried():
    assert not Person.objects.filter(name='foo bar').exists()


def test_values_query_result_not_includes_column():
    Person.objects.create(first_name='Foo', last_name='Bar')
    assert 'name' not in Person.objects.values()[0]


def test_create_works():
    Person.objects.create(first_name='Foo', last_name='Bar')


def test_computed_field_is_set_on_object():
    Person.objects.create(first_name='Foo', last_name='Bar')
    assert Person.objects.get().name == 'Foo Bar'


def test_computed_field_is_set_on_values():
    Person.objects.create(first_name='Foo', last_name='Bar')
    assert Person.objects.values('name')[0] == {'name': 'Foo Bar'}


def test_filter_on_computed_field():
    assert not Person.objects.filter(name='Foo Bar').exists()
    Person.objects.create(first_name='Foo', last_name='Bar')
    assert Person.objects.filter(name='Foo Bar').exists()


def test_filter_transform_on_computed_field():
    Person.objects.create(first_name='Foo', last_name='Bar')
    assert Person.objects.filter(name__icontains='foo').exists()


def test_cascading_field():
    Person.objects.create(first_name='Foo', last_name='Bar')
    assert Person.objects.filter(lower_name='foo bar').exists()


def test_ordering():
    assert len(Person.objects.order_by('name')) == 0


def test_property_behaviour():
    assert Person(first_name='Foo', last_name='Bar').name == 'Foo Bar'


def test_raw_f_expressions():
    assert Person(first_name='Foo', last_name='Bar').other == 'Foo Bar'
    Person.objects.create(first_name='Foo', last_name='Bar')
    assert Person.objects.filter(other='Foo Bar').exists()
