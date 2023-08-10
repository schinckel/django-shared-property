from django.contrib.auth.models import User
from ..models import Person


def test_admin(client):
    user = User.objects.create_superuser(username='admin')
    client.force_login(user)

    Person.objects.create(first_name="foo", last_name="bar", active_until="2300-01-01T00:00:00Z")

    response = client.get('/admin/tests/person/')
    assert '<td class="field-last_name">bar</td><td class="field-name">foo bar</td>' in response.content.decode()
