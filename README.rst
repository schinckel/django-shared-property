======================
Django Shared Property
======================


.. image:: https://img.shields.io/pypi/v/django_shared_property.svg
        :target: https://pypi.python.org/pypi/django_shared_property

.. image:: https://img.shields.io/travis/schinckel/django-shared-property.svg
        :target: https://travis-ci.org/schinckel/django-shared-property

.. image:: https://ci.appveyor.com/api/projects/status/schinckel/branch/main?svg=true
    :target: https://ci.appveyor.com/project/schinckel/django-shared-property/branch/main
    :alt: Build status on Appveyor

.. image:: https://readthedocs.org/projects/django-shared-property/badge/?version=latest
        :target: https://django-shared-property.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status




Properties that are both ORM expressions and python code.


* Free software: MIT license

* Documentation: https://django-shared-property.readthedocs.io.



Installation:
-------------

.. code-block:: console

    $ pip install django_shared_property

Philosophy:
-------------

I often find that I have annotations in Django querysets that are based on one or more other fields, and are used frequently. In some cases I have even been known to ensure these annotations are always available on the model using a custom queryset/manager.

But, unlike Python properties, these annotations are not "live". If, for example, you have the following:

.. code-block:: python

    class FullNameQueryset(models.query.QuerySet):
        def with_full_name(self):
            return self.annotate(
              full_name=Concat(models.F('first_name'), models.Value(' '), models.F('last_name')),
            )


    class Person(models.Model):
        first_name = models.TextField()
        last_name = models.TextField()

        objects = FullNameQueryset.as_manager()


Then, you can do a `person = Person.objects.with_full_name().get(pk=1)`, and then reference `person.full_name`.

But, if you modify `person.first_name`, you'd need to write it back to the database, and then reload it. Which may not be ideal, and at best requires two database operations.

django-shared-property allows you to have properties that automatically act as an annototation, allowing you to define the expression, and have Django use that operation within any database query. It can then be used in a filter (or further annotation), even across relationships. And finally, if any local changes are made to the object that would affect the value when stored in the database, then the property value will also update in Python.

Show me how!
-------------

Similar to a Python property, a django-shared-property requires a method that takes no arguments. It should, however, return a Django Expression. For example, following our annotation above:

.. code-block:: python

    class Person(models.Model):
        first_name = models.TextField()
        last_name = models.TextField()

        @shared_property
        def full_name(self):
            return Concat(models.F('first_name'), models.Value(' '), models.F('last_name'))


You then reference it just like any other field.

.. code-block:: python


    Person.objects.filter(full_name__contains='Bob')


What else can it do?
---------------------

Shared properties can reference any number of fields on the model, and even other shared properties, just like with annotations. They can even reference fields from related models, using the familiar ``models.F('relation__field')`` lookup syntax. You can also use some Django expressions (such as Concat, Lower, Upper), where there is a clear relationship to a Python concept.

  * Case
  * When
  * F
  * Q (Specifically, within a When, but it could work elsewhere)
  * Concat
  * Value
  * Lower and Upper (but only on Python objects that have these as attributes)
  * ExpressionWrapper
  * CombinedExpresson
  * Coalesce (but see the note below)

Within the context of a Q expression, you can use ``__isnull`` and ``__exact`` lookups.


You can even refer to constants in your Python file, such as the different values of an Enum. The return value of your python object will then correctly return instances of the Enum.


If your chosen expression/function/value does not work, then it may be possible to implement it (see below).


Shared properties should be pure functions - they must not refer to ``self`` (indeed, this will cause an error), and should not refer to variables, as they will be executed at times other than when they are about to be decorated.


How does it work?
------------------

Because of the limit that the decorated function be a pure function, we are able to execute the callable, using the result as a Django expression.

The Django part is relatively straightforward. The expression returned by the method that is decorated as a shared_property is used in a context that looks a bit like an annotation - however there are a couple of things that need to be done to ensure that the expression has the correct data available to it to make sure it points at the correct tables. We indicate to Django  that it should not be written back to the database by marking it as a ``private`` field.

Creating the Python property is a bit trickier. We still need the expression, but we build an Abstract Syntax Tree based on the expression. We then compile this into a callable object that we use as the property.

In a little more detail:

  * Call the decorated function, returning the Expression
  * Use Python's introspection tools to examine the expression (and it's "source expressions") and a recursive descent parser to build an AST equivalent to the expression. Specifically, the AST contains a function definition.
  * Compile this AST into a code object
  * ``eval`` this code object with the correct context to pull in any constants from outside the namespace.
  * Extract the newly defined function, and use it for the callable in our property.


Advanced Use
-------------

Sometimes you want to define the callable yourself: there is an alternate syntax for that. This could be where the expression has not been defined, or it's possible to create a more efficient callable by hand:

.. code-block:: python

    class MyModel(models.Model):
        # other fields

        @shared_property(Case(
            When(models.Q(x__gte=2, x__lt=5), then=models.Value('B')),
            When(models.Q(x__lt=2), then=models.Value('A')),
            default=models.Value('C'),
            output_field=models.TextField(),
        )
        def state(self):
            if 2 <= self.x < 5:
                return 'B'
            elif x < 2:
                return 'A'
            return 'C'

        @shared_property(Coalesce(
          CombinedExpression(F('expiry_date'), '<', Func(function='current_timestamp')),
          models.Value(True),
        ))
        def active(self):
            return self.expiry_date is None or self.expiry_date < timezone.now()


In this specific case, the code that is generated would be fairly similar (although it would not use the ``a < b < c`` idiom), however it shows how it is possible to to explicitly provide the python code. Please note that the onus of responsibility is on the developer to ensure that the expression and function are equivalent in this context.

The second example shows where a python comparison doesn't quite map to the SQL code: the ``COALESCE(expiry_date < now(), true)`` relies on SQL comparisons involving NULL to also return NULL, but in Python you cannot do this.

Also note that in this case only a single expression may be used as the argument to the decorator.

Registering Expressions
-----------------------

It is possible to register your own expressions. The structure is quite strict, and you'll need to reference the parser instance as well as the incoming expression. There's sometimes quite a bit of work to turn the Expression into (a) the correct Python, and then (b) the AST that is required.


.. code-block:: python

    from django_shared_property.parser import register


    @register
    def handle_foo(parser, expression):
        # This assumes a foo() function in python that matches a foo()
        # function in SQL, neither of which takes arguments.
        return Call(
            func=Name(id='foo', **parser.file),
            args=[],
            keywords=[],
            kwonlyargs=[],
            **parser.file,
        )


    class Foo(Func):
        function = 'foo'


    class MyModel(models.Model):
        # ...

        @shared_property
        def the_foo(self):
            return Foo()


This is a toy example - try looking in the ``parser`` module for other examples.

Limitations
-----------

Use of the django queryset methods defer/only prevent any shared properties from loading. However, because of the way the feature works, you would still be able to use this property - at least in the case where the referenced fields are local.

When you use a shared property that references a related model, and then try to filter on this, you cannot perform a count or exists query. See https://github.com/schinckel/django-shared-property/issues/2


Credits
-------

Developed by `Matthew Schinckel`_.

This package was created with Cookiecutter_ and the `wboxx1/cookiecutter-pypackage-poetry`_ project template.

.. _`Matthew Schinckel`: https://schinckel.net/
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`wboxx1/cookiecutter-pypackage-poetry`: https://github.com/wboxx1/cookiecutter-pypackage-poetry
