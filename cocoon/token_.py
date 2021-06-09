"""This module exposes the main Token class used by this package."""

from re import findall
from secrets import token_urlsafe
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    Mapping,
    overload,
    Set,
    TypeVar,
    Union,
)

from cocoon.proxy import Proxy


__all__ = ("Token",)


T = TypeVar("T")
_Cleanup = Union[int, str, Iterable[Union[int, str]], bool]
_ClassCleanup = Union[Mapping["Token", _Cleanup], Iterable["Token"], bool]


_NON_ALPHANUMERIC_EXCEPTION_MESSAGE = (
    lambda arg: f"{arg} can only contain non-alphanumeric characters."
)
_FULL_MATCH_EXCEPTION_MESSAGE = (
    "injecting a full_match token into a string is not allowed.\n"
    "TIP: if you're using NONE it must be on its own, not within a string."
)


def _has_alphanumeric(string: str) -> bool:
    return any(char.isalnum() for char in string)


def _validate_prefix(prefix: str) -> None:
    if not type(prefix) == str:
        raise TypeError("prefix must be a string.")

    if _has_alphanumeric(prefix):
        raise ValueError(
            _NON_ALPHANUMERIC_EXCEPTION_MESSAGE("prefix")
        )


def _validate_brackets(brackets: str) -> None:
    if not type(brackets) == str:
        raise TypeError("brackets must be a string.")

    if len(brackets) < 2 or len(brackets) % 2 != 0:
        raise ValueError(
            "brackets must be an even number of characters with a minimum of "
            "2."
        )

    if _has_alphanumeric(brackets):
        raise ValueError(_NON_ALPHANUMERIC_EXCEPTION_MESSAGE("brackets"))


def _validate_size(size: int) -> None:
    if not type(size) == int:
        raise TypeError("size must be an int.")

    if size <= 0:
        raise ValueError("size must be a positive number.")


def _validate_item(item):
    if not type(item) in (int, str):
        raise TypeError("'item' can only be of type <int> or <str>.")


def _validate_meta(brackets: str, prefix: str, size: int) -> None:
    if brackets is not None:
        _validate_brackets(brackets)
    if prefix is not None:
        _validate_prefix(prefix)
    if size is not None:
        _validate_size(size)


def _validate_obj(obj):
    if not isinstance(obj, (Token, str)):
        raise TypeError("'obj' can only be of type <Token> or <str>")


def _generate_regex(
        brackets: str,
        prefix: str,
        id_: str,
) -> str:
    i = len(brackets) // 2
    b1 = "\\".join(char for char in brackets[:i])
    b2 = "\\".join(char for char in brackets[i:])
    p = "\\".join(char for char in prefix)

    return rf"\{b1}\{p}[a-zA-Z_\d\-]{{{len(id_)}}}\{b2}"


class TokenMeta(type):
    """A metaclass for containing the 'core' class property."""
    @property
    def core(cls) -> Proxy:
        return Proxy()


class Token(Generic[T], metaclass=TokenMeta):
    """A class for dynamically injecting values into objects."""

    __prefix__: str = "$"
    __brackets__: str = "{{}}"
    __size__: int = 8
    __instances__: Dict[str, "Token"] = {}
    __regex__: Set[str] = set()

    def __init__(
            self,
            replacement: Union[Proxy, Callable[[], T], T],
            *,
            full_match: bool = False,
            anonymous: bool = False,
            call_depth: int = 10,
            always_replace: bool = False,
            # TODO:
            #  - accept user defined matching method.
            #  - accept user defined replacing method.
            **kwargs,
    ) -> None:
        """
        A token instance that functions as a placeholder for the given
        replacement.

        :param replacement: str
            A value or callable that gets injected at the time of parsing.
        :param full_match: bool
            Whether the replacement value should be a stand alone token or can be
            part of a string.
        :param anonymous: bool
            Whether this instance should be held onto for parsing or not.
        :param call_depth: int
            The number of nested callables a replacement can have.
        :param always_replace: bool
            After exceeding the call_depth:
            (if True) the replacement will be returned regardless of its type.
            (if False) a ValueError will be raised if the replacement is still
            a callable.
        :param kwargs: Additional customizations.
        :keyword brackets: str
            The opening and closing brackets that will be used in creating
            the placeholder.
        :keyword prefix: str
            A symbol that will be placed before the randomly generated id.
        :keyword size: int
            The byte size of the token_urlsafe used as id.
        """

        brackets: str = kwargs.get("brackets")
        prefix: str = kwargs.get("prefix")
        size: int = kwargs.get("size")

        _validate_meta(brackets, prefix, size)

        # The meta data used for creating a placeholder, needed for creating
        # cached instances.
        self.__prefix = prefix
        self.__brackets = brackets
        self.__size = size

        # The unique id that will be used to identify the placeholder to
        # replace it with the final value at parsing or injection time.
        self.__id = token_urlsafe(self.size)

        if not anonymous:
            # Keep track of all instances for parsing and resetting.
            self.__instances__[str(self)] = self

            # Adding to the regular expression used for extracting placeholders.
            self.__regex__.add(
                _generate_regex(self.brackets, self.prefix, self.__id)
            )

        # Arguments passed at class initialization.
        self.__replacement = replacement
        self.__full_match = full_match
        self.__call_depth = call_depth
        self.__always_replace = always_replace
        self.__anonymous = anonymous

        # For cashing instances with fixed replacement of the current token.
        self.__cached: Dict[Union[str, int], Any] = {}

    def __getitem__(self, item: Union[int, str]) -> "Token":
        _validate_item(item)

        if item in self.__cached:
            return self.__cached[item]

        token = Token(
            self.replacement,
            full_match=self.__full_match,
            anonymous=self.__anonymous,
            call_depth=0,
            always_replace=self.__always_replace,
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
        i = len(brackets) // 2

        return f"{brackets[:i]}{prefix}{id_}{brackets[i:]}"

    def __repr__(self):
        return f"'{self}'"

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other: Any):
        return str(self) == str(other)

    def __cleanup__(self, reset: _Cleanup) -> None:
        if type(reset) in (int, str):
            self.reset_cache(reset)

        elif isinstance(reset, Iterable):
            if reset := tuple(reset):
                self.reset_cache(*reset)

        elif reset is True:
            self.reset_cache()

    @classmethod
    @overload
    def parse(cls, obj: "Token[T]") -> T: ...

    @classmethod
    @overload
    def parse(cls, obj: str) -> str: ...

    @classmethod
    def parse(cls, obj):
        _validate_obj(obj)

        result = str(obj)
        placeholders = set(findall("|".join(cls.__regex__), result))

        for key in placeholders:
            if token := cls.__instances__.get(key):
                result = token.inject_into(result, deep=False)

        return result

    @classmethod
    def set_core(cls, core: Any, reset: _ClassCleanup = True) -> None:
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
    def replacement(self) -> T:
        replacement = self.__replacement
        tries = 0

        while callable(replacement):
            if isinstance(replacement, Proxy):
                replacement = replacement.__resolve__()
                continue

            if tries >= self.__call_depth:
                break

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
            obj: Union[str, "Token[T]"],
            *,
            reset: _Cleanup = False,
            deep: bool = True,
    ) -> Union[str, T]:
        _validate_obj(obj)

        result = str(obj)
        cached = self.__cached.values() if deep else []

        if self.__full_match:
            for token in (self, *cached):
                if token == result:
                    result = self.replacement
                    break
                elif str(token) in result:
                    raise ValueError(_FULL_MATCH_EXCEPTION_MESSAGE)

        else:
            count = result.count(str(self))

            for _ in range(count):
                result = result.replace(str(self), str(self.replacement), 1)

            for token in cached:
                result = token.inject_into(result)

        self.__cleanup__(reset)
        return result

    def reset_cache(self, *keys: Union[int, str]) -> None:
        [_validate_item(key) for key in keys]

        keys = keys or self.__cached.values()

        for key in keys:
            if token := self.__cached.get(key):
                token.__replacement__ = self.replacement
