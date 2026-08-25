from django_shared_property import _runtime


def test_text_helpers_preserve_null_and_handle_unicode():
    assert _runtime.length("A😀") == 2
    assert _runtime.length(None) is None
    assert _runtime.replace("banana", "na", "_") == "ba__"
    assert _runtime.replace(None, "na", "_") is None
    assert _runtime.replace("banana", None, "_") is None
    assert _runtime.replace("banana", "na", None) is None
    assert _runtime.reverse("A😀") == "😀A"
    assert _runtime.reverse(None) is None


def test_left_and_right_preserve_null_and_handle_unicode():
    assert _runtime.left("A😀BC", 2) == "A😀"
    assert _runtime.right("A😀BC", 2) == "BC"
    assert _runtime.left(None, 2) is None
    assert _runtime.right("text", None) is None


def test_existing_text_helpers_preserve_their_sql_null_semantics():
    assert _runtime.lower("TEXT") == "text"
    assert _runtime.lower(None) is None
    assert _runtime.upper("text") == "TEXT"
    assert _runtime.upper(None) is None
    assert _runtime.concat_pair("left", None) == "left"
    assert _runtime.concat_pair(None, "right") == "right"


def test_arithmetic_helpers_preserve_null_and_operator_semantics():
    assert _runtime.add(None, 1) is None
    assert _runtime.multiply(3, None) is None
    assert _runtime.add(1, 2) == 3
    assert _runtime.subtract(5, 2) == 3
    assert _runtime.multiply(3, 2) == 6
    assert _runtime.divide(6, 2) == 3
    assert _runtime.modulo(7, 3) == 1
    assert _runtime.power(2, 3) == 8
    assert _runtime.bitand(6, 3) == 2
    assert _runtime.bitor(6, 3) == 7
    assert _runtime.bitxor(6, 3) == 5
    assert _runtime.lshift(3, 2) == 12
    assert _runtime.rshift(12, 2) == 3
