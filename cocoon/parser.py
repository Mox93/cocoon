from typing import Mapping, Iterable

from cocoon.token_ import Token


def parse(obj):
    """
    recursively loop over elements and parse any instance of a string or a
    :param obj:
    :return: a new object with all placeholders replaced with the
     appropriate value.
    """
    if isinstance(obj, (str, Token)):
        return Token.parse(obj)

    type_ = obj.__class__

    if isinstance(obj, Mapping):
        return type_(
            (key, parse(value)) for key, value in obj.items()
        )

    if isinstance(obj, Iterable):
        return type_(parse(value) for value in obj)

    return obj
