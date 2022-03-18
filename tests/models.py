from django.db import models
from django.db.models.expressions import Case, CombinedExpression, F, Func, Value, When
from django.db.models.functions import Coalesce, Concat, Lower, Upper
from django.utils import timezone
from django.utils.translation import gettext as _

from django_shared_property.decorator import shared_property
from django_shared_property.parser import register


class Group(models.Model):
    name = models.TextField()


class User(models.Model):
    username = models.TextField()
    group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.SET_NULL)


try:
    from django.db.models.enums import TextChoices

    class State(TextChoices):
        ACTIVE = "active", _("Active")
        INACTIVE = "inactive", _("Inactive")


except ImportError:
    State = None


@register
def handle_upper(self, expression):
    from ast import Call, Attribute
    return Call(
        func=Attribute(
            value=self.build_expression(*expression.get_source_expressions()), attr='upper', **self.file
        ),
        args=[],
        keywords=[],
        kwonlyargs=[],
        **self.file,
    )


class Person(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    first_name = models.TextField()
    last_name = models.TextField()
    preferred_name = models.TextField(null=True, blank=True)
    active_until = models.DateTimeField(null=True, blank=True)

    @shared_property
    def name(self):
        return Concat(F("first_name"), Value(" "), F("last_name"), output_field=models.TextField())

    @shared_property
    def lower_name(self):
        return Lower(F("name"), output_field=models.TextField())

    @shared_property
    def upper_name(self):
        return Upper(F('name'), output_field=models.TextField())

    @shared_property
    def display_name(self):
        first_last = Concat(F("first_name"), Value(" "), F("last_name"))
        first_preferred_last = Concat(
            F("first_name"),
            Value(" ("),
            F("preferred_name"),
            Value(") "),
            F("last_name"),
        )
        return Case(
            When(preferred_name__isnull=True, then=first_last),
            When(preferred_name__exact=Value(""), then=first_last),
            default=first_preferred_last,
            output_field=models.TextField(),
        )

    @shared_property
    def other(self):
        return F("name")

    @shared_property
    def useless(self):
        return F("name")

    @useless.property
    def useless(self):
        return "Useless"

    @shared_property(F("first_name"))
    def alternate_syntax(self):
        return self.first_name

    @shared_property
    def username(self):
        return F("user__username")

    @shared_property
    def group(self):
        return F("user__group__name")

    @shared_property(
        Coalesce(
            CombinedExpression(
                Func(function="current_timestamp", arity=0, template="%(function)s"),
                "<",
                F("active_until"),
            ),
            Value(True),
            output_field=models.BooleanField(),
        )
    )
    def active(self):
        return self.active_until is None or self.active_until > timezone.now()

    if State:

        @shared_property
        def state(self):
            return Case(
                When(models.Q(active=models.Value(True)), then=models.Value(State.ACTIVE)),
                default=models.Value(State.INACTIVE),
                output_field=models.TextField(),
            )


class Address(models.Model):
    person = models.OneToOneField(Person, related_name="address", primary_key=True, on_delete=models.CASCADE)
