=====
Usage
=====

To use Django Shared Property in a project, you need to decorate a method that (a) takes no arguments other than self, (b) does not reference self in the method body, and (c) returns a single expression that is a Django ORM expression object::

    from django_shared_property.decorator import shared_property

    class Person(models.Model):
        first_name = models.TextField()
        last_name = models.TextField()
        preferred_name = models.TextField(null=True, blank=True)

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

This will result in two things being added to the Model.

  1. The expression that is returned will be used as a computed field - this will be usable in any queryset filters, and will be available in a .values() iff it is referenced directly.
  2. The expression will be turned into a python property and added onto the Model class directly - accessing this property will evaluate the python equivalent to the expression.

For instance::

    >>> Person.objects.create(first_name='Bob', last_name='Dobalino')
    >>> person = Person.objects.filter(display_name='Bob Dobalino').first()
    >>> print(person.display_name)
    Bob Dobalino
    >>> person.preferred_name = 'Dobs'
    >>> print(person.display_name)
    Bob (Dobs) Dobalino

Note that this evaluation is based on the current values of any referenced fields, as opposed to how an annotation of the expression would only be based on what is stored in the database.
