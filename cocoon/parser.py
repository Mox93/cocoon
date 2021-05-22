from typing import (
    Iterable,
    Mapping,
    Union,
)

from cocoon.token_ import Token
from cocoon.utils import deep_apply


ObjectToParse = Union[Token, set, Mapping, Iterable]
ParsedObject = Union[set, Mapping, Iterable]


def parse(obj: ObjectToParse) -> ParsedObject:
    """
    a function that recursively loop over elements and parse any
    instance of a string or a Token.
    :param obj: a dictionary containing strings with tokens.
    :return: a new object with all placeholders replaced with the
     appropriate value.
    """
    return deep_apply(obj, (str, Token), Token.parse)
