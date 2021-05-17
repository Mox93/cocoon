from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

from faker import Faker


_ProxyQueue = List[
    Tuple[
        Optional[str],
        List[Union[str, int, Tuple[Tuple[Any, ...], Dict[str, Any]]]]
    ]
]


class Proxy(object):
    __core__ = Faker()

    def __init__(self):
        self.__queue__: _ProxyQueue = [(None, [])]

    def __getattr__(self, item):
        self.__queue__.append((item, []))
        return self

    def __getitem__(self, key):
        self.__queue__[-1][1].append(key)
        return self

    def __call__(self, *args, **kwargs) -> "Proxy":
        self.__queue__[-1][1].append((args, kwargs))
        return self

    def __resolve__(self) -> Any:
        obj = self.__core__

        for item, params in self.__queue__:
            obj = getattr(obj, item) if item else obj

            for element in params:
                if type(element) == tuple:
                    args, kwargs = element
                    obj = obj(*args, **kwargs)
                else:
                    obj = obj[element]

        return obj() if callable(obj) else obj

    @classmethod
    def __set_core__(cls, generator):
        cls.__core__ = generator

    def __str__(self):
        result = f"{self.__class__.__name__}()"

        for item, params in self.__queue__:
            result += f".{item}" if item else ""

            for element in params:

                if type(element) == tuple:
                    args, kwargs = element
                    args_ = ', '.join(args)
                    kwargs_ = ', '.join(
                        f'{key}={value}' for key, value in kwargs.items()
                    )
                    params_ = ', '.join(
                        filter(lambda x: x, (args_, kwargs_))
                    )

                    result += f"({params_})"

                elif isinstance(element, str):
                    result += f"['{element}']"

                elif isinstance(element, int):
                    result += f"[{element}]"

        return result
