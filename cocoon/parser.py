from typing import (
    Any,
    overload,
    TypeVar,
)

from cocoon.token_ import Token
from cocoon.utils import deep_apply


T = TypeVar("T")


@overload
def parse(obj: str) -> str: ...


@overload
def parse(obj: Token[T]) -> T: ...


@overload
def parse(obj: T) -> T: ...


def parse(obj):
    """
    a function that recursively loop over elements and parse any instance of a
     string or a Token.
    :param obj: a dictionary containing strings with tokens.
    :return: a new object with all placeholders replaced with the appropriate
     value.
    """
    return deep_apply(
        obj,
        lambda x: isinstance(x, (str, Token)),
        Token.parse
    )
