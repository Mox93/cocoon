"""This module exposes the main Token class used by this package."""

from re import findall
from secrets import token_urlsafe
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    overload,
    Set,
    TypeVar,
    Union,
)

from .proxy import Proxy


__all__ = ("Token",)


T = TypeVar("T")
_IntOrStr = Union[int, str]


_NON_ALPHANUMERIC_EXCEPTION_MESSAGE = (
    lambda arg: f"{arg} can only contain non-alphanumeric characters."
)
_FULL_MATCH_EXCEPTION_MESSAGE = (
    "injecting a full_match token into a string is not allowed.\n"
    "TIP: if you're using NONE it must be on its own, not within a string."
)
_DEPTH_EXCEEDED_EXCEPTION_MESSAGE = (
    "maximum call depth was reached and replacement is still a callable."
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
    _validate_brackets(brackets)
    _validate_prefix(prefix)
    _validate_size(size)


def _validate_obj(obj) -> None:
    if type(obj) not in (Token, str):
        raise TypeError("'obj' can only be of type <Token> or <str>")


def _generate_token(brackets: str, prefix: str, size: int) -> str:
    i = len(brackets) // 2

    return f"{brackets[:i]}{prefix}{token_urlsafe(size)}{brackets[i:]}"


def _generate_regex(
        brackets: str,
        prefix: str,
        size: int,
) -> str:
    i = len(brackets) // 2
    b1 = "\\".join(char for char in brackets[:i])
    b2 = "\\".join(char for char in brackets[i:])
    p = "\\".join(char for char in prefix)

    return rf"\{b1}\{p}[a-zA-Z_\d\-]{{{size}}}\{b2}"


def _call_once(function: Callable[[], T]) -> Callable[[], T]:
    """
    Used for postponing resolving the token value till the first time it's parsed.
    :param function:
    :return:
    """
    result: T = ...

    def inner_function():
        nonlocal result

        if result is ...:
            result = function()

        return result

    return inner_function


def _match_sequence(
        tokens: List["Token"], target: List["Token"]
) -> List["Token"]:
    result = []

    for token in target:
        try:
            i = tokens.index(token)
            result.append(tokens[i])
        except ValueError:
            pass

    return result


class TokenMeta(type):
    """A metaclass for containing the 'core' class property."""
    @property
    def core(cls) -> Proxy:
        return Proxy()


class Token(str, Generic[T], metaclass=TokenMeta):
    """A class for dynamically injecting values into objects."""

    __instances__: Dict[str, "Token"] = {}
    __regex__: Set[str] = set()

    def __new__(
            cls,
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
    ) -> "Token[T]":
        """
        A token instance that functions as a placeholder for the given
        replacement.

        :param replacement: Union[Proxy, Callable[[], T], T]
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
            (if False) a RuntimeError will be raised if the replacement is still
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

        brackets: str = kwargs.get("brackets", "{{}}")
        prefix: str = kwargs.get("prefix", "$")
        size: int = kwargs.get("size", 8)

        _validate_meta(brackets, prefix, size)

        placeholder = _generate_token(brackets, prefix, size)
        token = super(Token, cls).__new__(cls, placeholder)

        # The meta data used for creating a placeholder, needed for creating
        # cached instances.
        token.__prefix = prefix
        token.__brackets = brackets
        token.__size = size

        if not anonymous:
            # Keep track of all instances for parsing and resetting.
            if cls.__instances__.get(str(token)):
                raise RuntimeError("Token collision.")

            cls.__instances__[str(token)] = token

            # Adding to the regular expression used for extracting placeholders.
            id_length = len(placeholder) - len(brackets + prefix)
            cls.__regex__.add(_generate_regex(brackets, prefix, id_length))

        # Arguments passed at class initialization.
        token.__replacement = replacement
        token.__full_match = full_match
        token.__call_depth = call_depth
        token.__always_replace = always_replace
        token.__anonymous = anonymous

        # For cashing instances with fixed replacement of the current token.
        cached: Dict[_IntOrStr, Token[T]] = {}
        token.__cached = cached

        return token

    def __getitem__(self, item: _IntOrStr) -> "Token":
        _validate_item(item)

        if item in self.__cached:
            return self.__cached[item]

        token = Token(
            _call_once(lambda: self.value),
            full_match=self.__full_match,
            anonymous=self.__anonymous,
            call_depth=0,
            always_replace=self.__always_replace,
            prefix=self.__prefix,
            brackets=self.__brackets,
            size=self.__size,
        )
        self.__cached[item] = token

        return token

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other: Union["Token[T]", str]):
        return str(self) == str(other)

    @classmethod
    @overload
    def parse(cls, obj: "Token[T]") -> T: ...

    @classmethod
    @overload
    def parse(cls, obj: str) -> str: ...

    @classmethod
    def parse(cls, obj):
        _validate_obj(obj)

        placeholders = findall("|".join(cls.__regex__), obj)

        for key in placeholders:
            token = cls.__instances__.get(key)

            if not token:
                continue

            obj = token.inject_into(
                obj,
                deep=False,
                __first_only__=True,
                __placeholders__=placeholders
            )

        return obj

    @classmethod
    def set_core(
            cls,
            core: Any,
            *,
            reset: bool = True
    ) -> None:
        Proxy.__core__ = core

        if reset is True:
            for token in cls.__instances__.values():
                if isinstance(token.__replacement, Proxy):
                    token.reset_cache()

    @property
    def value(self) -> T:
        result = self.__replacement
        tries = 0

        while callable(result):
            if isinstance(result, Proxy):
                result = result.__resolve__()
                continue

            if tries > self.__call_depth:
                break

            result = result()
            tries += 1

        if callable(result) and not self.__always_replace:
            raise RuntimeError(_DEPTH_EXCEEDED_EXCEPTION_MESSAGE)

        return result

    @overload
    def inject_into(self, obj: "Token[T]", **kwargs) -> "Token[T]": ...

    @overload
    def inject_into(self, obj: "Token[T]", **kwargs) -> T: ...

    @overload
    def inject_into(self, obj: str, **kwargs) -> str: ...

    def inject_into(self, obj, *, deep: bool = True, **kwargs):
        _validate_obj(obj)

        first_only = kwargs.get("__first_only__", False)
        # to avoid doing regex pattern matching more than once
        placeholders = kwargs.get(
            "__placeholders__",
            findall("|".join(self.__regex__), obj)
        )

        cached = self.__cached.values() if deep else []
        tokens = _match_sequence([self, *cached], placeholders)

        for token in tokens:
            if token == obj:
                return token.value

            if token in obj:
                if token.__full_match:
                    raise ValueError(_FULL_MATCH_EXCEPTION_MESSAGE)

                obj = obj.replace(token, token.value, 1)

                if first_only:
                    return obj

        return obj

    def reset_cache(self, *keys: _IntOrStr) -> None:
        [_validate_item(key) for key in keys]

        keys = keys or self.__cached.keys()

        for key in keys:
            token = self.__cached.get(key)

            if token:
                token.__replacement = _call_once(lambda: self.value)

    @classmethod
    def reset_all_cache(cls, *keys: _IntOrStr):
        for token in cls.__instances__.values():
            token.reset_cache(*keys)
