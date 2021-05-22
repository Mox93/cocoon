from re import findall
from secrets import token_urlsafe
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Mapping,
    Set,
    Union,
)

from cocoon.proxy import Proxy


_Cleanup = Union[int, str, Iterable[Union[int, str]], bool]
_ClassCleanup = Union[
    Mapping["Token", _Cleanup], Iterable["Token"], bool
]


_NON_ALPHANUMERIC_EXCEPTION_MESSAGE = (
    lambda arg: (
        f"{arg} can only contain non-alphanumeric characters."
    )
)
_FULL_MATCH_EXCEPTION_MESSAGE = (
    "injecting a full_match token into a string is not allowed.\n"
    "TIP: if you're using NONE it must be on its own, not within a "
    "string."
)


def _has_alphanumeric(string: str) -> bool:
    return any(char.isalnum() for char in string)


def _validate_prefix(prefix: str):
    if not type(prefix) == str:
        raise TypeError("prefix must be a string.")

    if _has_alphanumeric(prefix):
        raise ValueError(
            _NON_ALPHANUMERIC_EXCEPTION_MESSAGE("prefix")
        )


def _validate_brackets(brackets: str):
    if not type(brackets) == str:
        raise TypeError("brackets must be a string.")

    if len(brackets) < 2 or len(brackets) % 2 != 0:
        raise ValueError(
            "brackets must be an even number of characters "
            "with a minimum of 2."
        )

    if _has_alphanumeric(brackets):
        raise ValueError(
            _NON_ALPHANUMERIC_EXCEPTION_MESSAGE("brackets")
        )


def _validate_size(size: int):
    if not type(size) == int:
        raise TypeError("size must be an int.")

    if size <= 0:
        raise ValueError("size must be a positive number.")


def _validate_meta(brackets: str, prefix: str, size: int):
    if brackets is not None:
        _validate_brackets(brackets)
    if prefix is not None:
        _validate_prefix(prefix)
    if size is not None:
        _validate_size(size)


def _generate_regex(
        brackets: str,
        prefix: str,
        id_: str,
) -> str:
    i = int(len(brackets) / 2)
    b1 = "\\".join(char for char in brackets[:i])
    b2 = "\\".join(char for char in brackets[i:])
    p = "\\".join(char for char in prefix)

    return rf"\{b1}\{p}[a-zA-Z_\d\-]{{{len(id_)}}}\{b2}"


class TokenMeta(type):
    def __getattr__(self, item):
        if item == "core":
            return Proxy()

        raise AttributeError(
            f"type object '{self.__name__}' "
            f"has no attribute '{item}'."
        )


class Token(object, metaclass=TokenMeta):
    __prefix__: str = "$"
    __brackets__: str = "{{}}"
    __size__: int = 8
    __instances__: Dict[str, "Token"] = {}
    __regex__: Set[str] = set()

    def __init__(
            self,
            replacement: Union[Proxy, Callable[[], Any], Any],
            *,
            full_match: bool = False,
            # TODO:
            #  - accept user defined matching method.
            #  - accept user defined replacing method.
            **kwargs,
    ):
        """
        a class for dynamically injecting values into objects.
        :param replacement: a value or callable that gets injected in
         the future.
        :param full_match: whether the injected value should be stand
         alone or can be surrounded by other characters.
        :param kwargs: additional customizations.
        :keyword brackets: a string for the opening and closing
         brackets that will be used in creating the placeholder.
        :keyword prefix: a string that will be attached to the
         randomly generated id.
        :keyword size: an integer for the byte size of the
         token_urlsafe.
        :keyword call_depth: an integer for the number of nested
         callables a replacement can have.
        :keyword always_replace: after exceeding the call_depth:
         (if True) the replacement will be returned regardless of
         its type.
         (if False) a ValueError will be raised if the replacement
         is still a callable.
        """

        brackets = kwargs.get("brackets")
        prefix = kwargs.get("prefix")
        size = kwargs.get("size")

        _validate_meta(brackets, prefix, size)

        # the meta data used for creating a placeholder, needed for
        # creating cached instances.
        self.__prefix = prefix
        self.__brackets = brackets
        self.__size = size

        # the unique id that will be used to identify the placeholder
        # to replace it with the final value at parsing or injection
        # time.
        self.__id = token_urlsafe(self.size)

        # updating the regular expression used for extracting
        # placeholders.
        self.__regex__.add(
            _generate_regex(self.brackets, self.prefix, self.__id)
        )

        # arguments passed at class initialization
        self.__replacement = replacement
        self.__full_match = full_match

        # kwargs passed at class initialization
        self.__call_depth = kwargs.get("call_depth", 10)
        self.__always_replace = kwargs.get("always_replace", False)

        #
        self.__cached = {}

        #
        self.__instances__[str(self)] = self

    def __getitem__(self, item: Union[int, str]) -> "Token":
        if not type(item) in (int, str):
            raise ValueError(
                "a key can only be of type <int> or <str>."
            )

        if item in self.__cached:
            return self.__cached[item]

        token = Token(
            self.replacement,
            prefix=self.prefix,
            brackets=self.brackets,
            size=self.size,
        )
        self.__cached[item] = token

        return token

    def __str__(self):
        brackets = self.brackets
        prefix = self.prefix
        id_ = self.__id
        i = int(len(brackets) / 2)

        return f"{brackets[:i]}{prefix}{id_}{brackets[i:]}"

    def __repr__(self):
        return f"\'{self}\'"

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)

    def __cleanup__(self, reset: _Cleanup):
        if type(reset) in (int, str):
            self.reset_cache(reset)

        elif isinstance(reset, Iterable):
            if reset := tuple(reset):
                self.reset_cache(*reset)

        elif reset is True:
            self.reset_cache()

    @classmethod
    def parse(cls, obj: Union["Token", str]) -> str:
        result = str(obj)
        placeholders = set(findall("|".join(cls.__regex__), result))

        for key in placeholders:
            if token := cls.__instances__.get(key):
                result = token.inject_into(result, deep=False)

        return result

    @classmethod
    def set_core(cls, core: Any, reset: _ClassCleanup = True):
        cls.core.__set_core__(core)

        if isinstance(reset, Mapping):
            for token, cleanup in reset.items():
                token.__cleanup__(cleanup)

        elif isinstance(reset, Iterable):
            for token in reset:
                token.__cleanup__(True)

        elif reset is True:
            for token in cls.__instances__.values():
                token.__cleanup__(reset)

    @property
    def brackets(self) -> str:
        return self.__brackets or self.__brackets__

    @property
    def prefix(self) -> str:
        return self.__prefix or self.__prefix__

    @property
    def size(self) -> int:
        return self.__size or self.__size__

    @property
    def replacement(self) -> Any:
        replacement = self.__replacement
        tries = 0

        while tries < self.__call_depth and callable(replacement):
            if isinstance(replacement, Proxy):
                replacement = replacement.__resolve__()
                continue

            replacement = replacement()
            tries += 1

        if callable(replacement) and not self.__always_replace:
            raise RuntimeError(
                "maximum call depth was reached and replacement is "
                "still a callable."
            )

        return replacement

    def inject_into(
            self,
            obj: Union["Token", str],
            *,
            reset: _Cleanup = False,
            deep: bool = True,
    ) -> Any:
        result = str(obj)
        cached = self.__cached.values() if deep else []

        if self.__full_match:
            if self == result:
                result = self.replacement
            elif str(self) in result:
                raise ValueError(_FULL_MATCH_EXCEPTION_MESSAGE)

            for token in cached:
                if token == result:
                    result = token.inject_into(result)
                elif token in result:
                    raise ValueError(_FULL_MATCH_EXCEPTION_MESSAGE)

        else:
            if str(self) in result:
                result = result.replace(
                    str(self), str(self.replacement)
                )

            for token in cached:
                result = token.inject_into(result)

        self.__cleanup__(reset)
        return result

    def reset_cache(self, *keys: Union[int, str]):
        if not keys:
            for token in self.__cached.values():
                token.__replacement = self.replacement

            return

        for key in keys:
            if token := self.__cached.get(key):
                token.__replacement__ = self.replacement
