from django.db import models
from django.db.models.expressions import Value, Case, When, F, ExpressionWrapper
from django.db.models.functions import Concat, Lower

from django_shared_property.decorator import shared_property


class Group(models.Model):
    name = models.TextField()


class User(models.Model):
    username = models.TextField()
    group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.SET_NULL)


class Person(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    first_name = models.TextField()
    last_name = models.TextField()
    preferred_name = models.TextField(null=True, blank=True)

    @shared_property
    def name(self):
        return Concat(
            F('first_name'), Value(' '), F('last_name'),
            output_field=models.TextField()
        )

    @shared_property
    def lower_name(self):
        return Lower(F('name'), output_field=models.TextField())

    @shared_property
    def display_name(self):
        first_last = Concat(F('first_name'), Value(' '), F('last_name'))
        first_preferred_last = Concat(
            F('first_name'),
            Value(' ('), F('preferred_name'), Value(') '),
            F('last_name'),
        )
        return Case(
            When(preferred_name__isnull=True, then=first_last),
            When(preferred_name__exact=Value(''), then=first_last),
            default=first_preferred_last,
            output_field=models.TextField()
        )

    @shared_property
    def other(self):
        return F('name')

    @shared_property
    def useless(self):
        return F('name')

    @useless.property
    def useless(self):
        return 'Useless'

    @shared_property(F('first_name'))
    def alternate_syntax(self):
        return self.first_name

    # @shared_property
    # def username(self):
    #     return ExpressionWrapper(F('user__username'), output_field=models.TextField())
    #
    # @shared_property
    # def group(self):
    #     return ExpressionWrapper(F('user__group__name'), output_field=models.TextField())


class Address(models.Model):
    person = models.OneToOneField(Person, related_name='address', primary_key=True, on_delete=models.CASCADE)
