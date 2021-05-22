from typing import (
    Any,
    Callable,
    Iterable,
    Mapping,
    Tuple,
    Union,
)


def deep_apply(
        obj: Any,
        type_: Union[type, Tuple[Union[type, Tuple[Any, ...]], ...]],
        method: Callable
):
    if isinstance(obj, type_):
        return method(obj)

    # used for returning a new instance of the same class
    class_ = obj.__class__

    if isinstance(obj, Mapping):
        return class_(
            (key, deep_apply(value, type_, method))
            for key, value in obj.items()
        )

    if isinstance(obj, Iterable):
        return class_(
            deep_apply(value, type_, method) for value in obj
        )

    return obj
