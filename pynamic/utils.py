from typing import (
    Callable,
    Generator,
    Iterable,
    Iterator,
    Mapping,
    TypeVar,
    Union,
)


__all__ = ("deep_apply",)


T = TypeVar("T")
R = TypeVar("R")

_StringLike = (str, bytes, bytearray)
_IterableLike = (Iterator, Generator, range)


def deep_apply(
        obj: T,
        condition: Callable[[T], bool],
        action: Callable[[T], R],
        unpack: bool = True,
) -> Union[T, R]:
    """
    recursively goes through the elements of an object and applies the given
    method if the given condition applies.
    :param obj: the object to manipulate.
    :param condition: a function for determining if the method should be
    applied or not.
    :param action: the function to be applied on an object that satisfies the
    condition.
    :param unpack: for determining if iterators, generators and ranges should
    be looked into or left as is.
    :return: a new instance of the object with elements being modified.
    """
    if condition(obj):
        return action(obj)

    # used for returning a new instance of the same class
    class_ = obj.__class__

    if isinstance(obj, Mapping):
        return class_(
            (key, deep_apply(value, condition, action))
            for key, value in obj.items()
        )

    if isinstance(obj, Iterable) and not isinstance(obj, _StringLike):
        if isinstance(obj, _IterableLike):
            if unpack:
                class_ = list
            else:
                return obj

        return class_(
            deep_apply(value, condition, action) for value in obj
        )

    return obj
