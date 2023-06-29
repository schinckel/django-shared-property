import datetime

from ..models import Person


def test_convert_value_trunc():
    Person.objects.create(first_name="Foo", last_name="Bar", active_until = datetime.datetime(2023, 6, 29, 0, 0, 0, tzinfo = datetime.timezone.utc))
    assert Person.objects.values('active_until')[0]["active_until"] == datetime.datetime(2023, 6, 29, 0, 0, 0, tzinfo = datetime.timezone.utc)
    assert Person.objects.values('active_until_year')[0]["active_until_year"] == datetime.date(2023, 1, 1)

def test_convert_value_values_map():
    Person.objects.create(first_name="Foo", last_name="Bar", person_type_code = 1)
    assert Person.objects.values('person_type')[0]["person_type"] == 'Good'
