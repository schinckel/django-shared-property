import operator


def _null_propagating(operation):
    def apply(left, right):
        if left is None or right is None:
            return None
        return operation(left, right)

    return apply


def length(value):
    return None if value is None else len(value)


def replace(value, text, replacement):
    if value is None or text is None or replacement is None:
        return None
    return value.replace(text, replacement)


def reverse(value):
    return None if value is None else value[::-1]


def left(value, length):
    if value is None or length is None:
        return None
    return value[:length]


def right(value, length):
    if value is None or length is None:
        return None
    return value[-length:]


def lower(value):
    return None if value is None else value.lower()


def upper(value):
    return None if value is None else value.upper()


def concat_pair(left, right):
    return (left or "") + (right or "")


add = _null_propagating(operator.add)
subtract = _null_propagating(operator.sub)
multiply = _null_propagating(operator.mul)
divide = _null_propagating(operator.truediv)
modulo = _null_propagating(operator.mod)
power = _null_propagating(operator.pow)
bitand = _null_propagating(operator.and_)
bitor = _null_propagating(operator.or_)
bitxor = _null_propagating(operator.xor)
lshift = _null_propagating(operator.lshift)
rshift = _null_propagating(operator.rshift)
