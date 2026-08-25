from ..models import Person


def test_shared_text_functions_match_python_and_database_values():
    person = Person.objects.create(
        first_name="Ada",
        last_name="Lovelace",
        preferred_name="A😀BC",
        person_type_code=2,
    )

    assert person.lower_preferred_name == "a😀bc"
    assert person.preferred_name_length == 4
    assert person.replaced_preferred_name == "A😀BC"
    assert person.reversed_preferred_name == "CB😀A"
    assert person.left_preferred_name == "a😀"
    assert person.right_preferred_name == "BC"
    assert person.nullable_concat == "A😀BC!"

    assert Person.objects.get(lower_preferred_name="a😀bc") == person
    assert Person.objects.get(preferred_name_length=4) == person
    assert Person.objects.get(replaced_preferred_name="A😀BC") == person
    assert Person.objects.get(reversed_preferred_name="CB😀A") == person
    assert Person.objects.get(left_preferred_name="a😀") == person
    assert Person.objects.get(right_preferred_name="BC") == person
    assert Person.objects.get(nullable_concat="A😀BC!") == person

    assert Person.objects.values("preferred_name_length", "left_preferred_name").get() == {
        "preferred_name_length": 4,
        "left_preferred_name": "a😀",
    }


def test_shared_text_functions_preserve_null_and_concat_semantics():
    person = Person.objects.create(first_name="Ada", last_name="Lovelace")

    assert person.lower_preferred_name is None
    assert person.preferred_name_length is None
    assert person.replaced_preferred_name is None
    assert person.reversed_preferred_name is None
    assert person.left_preferred_name is None
    assert person.right_preferred_name is None
    assert person.nullable_concat == "!"
    assert person.next_person_type_code is None

    for property_name in (
        "lower_preferred_name",
        "preferred_name_length",
        "replaced_preferred_name",
        "reversed_preferred_name",
        "left_preferred_name",
        "right_preferred_name",
        "next_person_type_code",
    ):
        assert Person.objects.get(**{f"{property_name}__isnull": True}) == person

    assert Person.objects.get(nullable_concat="!") == person
