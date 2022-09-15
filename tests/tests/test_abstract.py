from ..models import Concrete


def test_concrete_model_create():
    assert Concrete.objects.create(foo='Foo', baz='Baz').bar == 'Foo'


def test_concrete_model_query():
    obj = Concrete.objects.create(foo='Foo', baz='Baz')
    assert list(Concrete.objects.filter(foo='foo')) == []
    assert list(Concrete.objects.filter(bar='bar')) == []
    assert list(Concrete.objects.filter(bar='Foo')) == [obj]
