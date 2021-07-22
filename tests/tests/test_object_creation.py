from ..models import Person


def test_bulk_create_works():
    assert Person.objects.bulk_create([
        Person(
            first_name='x',
            last_name='y',
        )
    ])[0].name == 'x y'
