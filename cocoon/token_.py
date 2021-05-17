from re import findall
from secrets import token_urlsafe
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Set,
    Union,
)

from cocoon.proxy import Proxy


_Cleanup = Union[int, str, Iterable[Union[int, str]], bool]
_ClassCleanup = Union[Dict["Token", _Cleanup], bool]


_NON_ALPHANUMERIC_EXCEPTION_MESSAGE = (
    lambda arg: f"{arg} can only contain non-alphanumeric characters"
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
        raise TypeError("prefix must be a string")

    if _has_alphanumeric(prefix):
        raise ValueError(
            _NON_ALPHANUMERIC_EXCEPTION_MESSAGE("prefix")
        )


def _validate_brackets(brackets: str):
    if not type(brackets) == str:
        raise TypeError("brackets must be a string")

    if len(brackets) < 2 or len(brackets) % 2 != 0:
        raise ValueError(
            "brackets must be an even number of characters "
            "with a minimum of 2"
        )

    if _has_alphanumeric(brackets):
        raise ValueError(
            _NON_ALPHANUMERIC_EXCEPTION_MESSAGE("brackets")
        )


def _validate_size(size: int):
    if not type(size) == int:
        raise TypeError("size must be an int")

    if size <= 0:
        raise ValueError("size must be a positive number")


def _generate_id(brackets: str, prefix: str, size: int):
    i = int(len(brackets) / 2)
    return (
        f"{brackets[:i]}{prefix}{token_urlsafe(size)}{brackets[i:]}"
    )


def _generate_regex(
        brackets: str,
        prefix: str,
        placeholder: str,
) -> str:
    id_length = len(placeholder) - (len(brackets) + len(prefix))
    i = int(len(brackets) / 2)
    b1 = "\\".join(char for char in brackets[:i])
    b2 = "\\".join(char for char in brackets[i:])
    p = "\\".join(char for char in prefix)

    return rf"\{b1}\{p}[a-zA-Z_\d\-]{{{id_length}}}\{b2}"


class TokenMeta(type):
    def __getattr__(self, item):
        if item == "core":
            return Proxy()

        raise AttributeError(
            f"type object '{self.__name__}' has no attribute '{item}'"
        )


class Token(object, metaclass=TokenMeta):
    __prefix__: str = "$"
    __brackets__: str = "{{}}"
    __size__: int = 8
    __instances__: Dict[str, "Token"] = {}
    __regex__: Set[str] = set()

    def __init__(
            self,
            replacement: Union[Callable[[], Any], Any],
            *,
            full_match: bool = False,
            # TODO:
            #  - accept user defined matching method.
            #  - accept user defined replacing method.
            **kwargs,
    ):
        """
        An object for dynamically injecting values into strings.

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
        """

        brackets = kwargs.pop("brackets", self.__brackets__)
        prefix = kwargs.pop("prefix", self.__prefix__)
        size = kwargs.pop("size", self.__size__)

        _validate_prefix(prefix)
        _validate_brackets(brackets)
        _validate_size(size)

        placeholder = _generate_id(brackets, prefix, size)
        re_sec = _generate_regex(brackets, prefix, placeholder)

        # the placeholder value that will be replaced with
        # the final value at parsing or injection time.
        self.__placeholder__ = placeholder

        # updating the regular expression used for extracting
        # placeholders.
        self.__regex__.add(re_sec)

        # the meta data used for creating a placeholder, needed for
        # creating cached instances.
        self.__prefix__ = prefix
        self.__brackets__ = brackets
        self.__size__ = size

        # arguments passed to the __init__ method
        self.__replacement__ = replacement
        self.__full_match__ = full_match

        #
        self.__cached__ = {}

        #
        self.__instances__[placeholder] = self

    def __call__(self, key: Union[int, str] = None) -> "Token":
        if key is None:
            return self

        if not type(key) in (int, str):
            raise ValueError("a key can only be an <int> or a <str>")

        if key in self.__cached__:
            return self.__cached__[key]

        token = Token(
            self.replacement,
            prefix=self.__prefix__,
            brackets=self.__brackets__,
            size=self.__size__,
        )

        self.__cached__[key] = token
        return token

    def __str__(self):
        return self.__placeholder__

    def __repr__(self):
        return f"\'{self.__placeholder__}\'"

    def __hash__(self):
        return hash(self.__placeholder__)

    def __eq__(self, other):
        return str(self) == str(other)

    def __cleanup__(self, reset: _Cleanup):
        if type(reset) in (int, str):
            self.reset(reset)
        elif isinstance(reset, Iterable) and reset:
            if reset := tuple(reset):
                self.reset(*reset)
        elif reset:
            self.reset()

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

        if type(reset) == dict:
            for token, cleanup in reset.items():
                token.__cleanup__(cleanup)
        elif reset:
            for token in cls.__instances__.values():
                token.__cleanup__(reset)

    @property
    def replacement(self) -> Any:
        if type(self.__replacement__) == Proxy:
            return self.__replacement__.__resolve__()

        if callable(self.__replacement__):
            return self.__replacement__()

        return self.__replacement__

    @replacement.setter
    def replacement(self, value: Any):
        self.__replacement__ = value

    def inject_into(
            self,
            obj: Union["Token", str],
            *,
            reset: _Cleanup = False,
            deep: bool = True,
    ) -> Any:
        result = str(obj)
        cached = self.__cached__.values() if deep else []

        if self.__full_match__:
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
                result = result.replace(str(self), str(self.replacement))

            for token in cached:
                result = token.inject_into(result)

        self.__cleanup__(reset)
        return result

    def reset(self, *keys: Union[int, str]):
        if not keys:
            for token in self.__cached__.values():
                token.replacement = self.replacement

            return

        for key in keys:
            if token := self.__cached__.get(key):
                token.replacement = self.replacement
