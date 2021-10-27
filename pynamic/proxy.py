from typing import (
    Any,
    List,
    Optional,
    Tuple,
    Union,
)

from .core import fake
from .utils import deep_apply


__all__ = ("Proxy",)


_MISSING_CORE_EXCEPTION_MESSAGE = (
    "No core was found.\nTIP: you can install 'faker' and it will be used as "
    "the core or define your own core and pass it to 'Token.set_core'."
)
_INCORRECT_ELEMENT_EXCEPTION_MESSAGE = (lambda element: (
    f"element '{element}' of type <{type(element)}> was found in __queue__. "
    f"Only <Arguments> or <Item> types are accepted."
))


class Arguments(object):
    def __init__(self, args: tuple, kwargs: dict):
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        args = ", ".join(repr(arg) for arg in self.args)
        kwargs = ", ".join(
            f"{key}={value}" for key, value in self.kwargs.items()
        )

        return f"({', '.join(filter(lambda x: x, (args, kwargs)))})"


class Item(object):
    def __init__(self, item: Any):
        self.item = item

    def __repr__(self):
        print(repr(self.item))
        if isinstance(self.item, slice):
            has_start = self.item.start is not None
            has_stop = self.item.stop is not None
            has_step = self.item.step is not None

            result = (
                f"{self.item.start if has_start else ''}:"
                f"{self.item.stop if has_stop else ''}"
                f"{f':{self.item.step}' if has_step else ''}"
            )

        else:
            result = self.item

        return f"[{result}]"


_ProxyQueue = List[
    Tuple[Optional[str], List[Union[Arguments, Item]]]
]


class Proxy(object):
    __core__ = fake

    def __init__(self):
        self.__queue__: _ProxyQueue = [(None, [])]

    def __getattr__(self, item):
        self.__queue__.append((item, []))
        return self

    def __getitem__(self, item):
        self.__queue__[-1][1].append(Item(item))
        return self

    def __call__(self, *args, **kwargs) -> "Proxy":
        self.__queue__[-1][1].append(Arguments(args, kwargs))
        return self

    def __resolve__(self) -> Any:
        if self.__core__ is None:
            raise RuntimeError(_MISSING_CORE_EXCEPTION_MESSAGE)

        obj = self.__core__

        for item, params in self.__queue__:
            obj = getattr(obj, item) if item else obj

            for element in params:
                if type(element) == Arguments:
                    args = _resolve(element.args)
                    kwargs = _resolve(element.kwargs)

                    obj = obj(*args, **kwargs)
                elif type(element) == Item:
                    obj = obj[element.item]
                else:
                    raise ValueError(
                        _INCORRECT_ELEMENT_EXCEPTION_MESSAGE(element)
                    )

        return obj

    def __repr__(self):
        result = f"{self.__class__.__name__}()"

        for item, actions in self.__queue__:
            result += (
                (f".{item}" if item else "")
                + "".join(repr(action) for action in actions)
            )

        return result


def _resolve(obj):
    return deep_apply(
        obj,
        lambda x: isinstance(x, Proxy),
        lambda p: p.__resolve__()
    )
