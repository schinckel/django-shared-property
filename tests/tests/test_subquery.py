from django.db.models import Exists, OuterRef, Subquery

from ..models import Person, Concrete


def test_subquery_to_shared_property():
    Person.objects.create(first_name='Foo', last_name='Bar')
    Concrete.objects.create(foo='Foo Bar', baz='XXX')

    assert Person.objects.filter(
        Exists(Concrete.objects.filter(
            foo=OuterRef('name')
        ))
    ).exists()

    assert Person.objects.filter(
        Exists(Concrete.objects.filter(foo=OuterRef('name')))
    ).annotate(
        baz=Subquery(Concrete.objects.filter(foo=OuterRef('name')).values('baz'))
    ).get().baz == 'XXX'
