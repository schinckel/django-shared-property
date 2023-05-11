from ..models import User


def test_setter():
    import pdb; pdb.set_trace()
    User.objects.create(data={'fields': {'isinactive': 'T'}})
    user = User.objects.get(inactive=True)
    user.inactive = False
    assert user.data['fields']['isinactive'] == 'F'
