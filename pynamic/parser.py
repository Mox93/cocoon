from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    overload,
    Protocol,
    Sequence,
    TypeVar,
    Union,
)

from .token import Token
from .utils import deep_apply


__all__ = ("parse", "dynamic_openapi")


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
    return deep_apply(obj, lambda x: isinstance(x, str), Token.parse)


JsonLike = Dict[str, Any]
OpenAPIGenerator = Callable[..., JsonLike]
BaseRoute = TypeVar("BaseRoute")


class FastAPI(Protocol):
    title: str
    version: str
    openapi_version: str
    description: str
    routes: Sequence[BaseRoute]
    servers: Optional[List[Dict[str, Union[str, Any]]]]
    openapi_schema: JsonLike


def dynamic_openapi(
        app: FastAPI,
        get_openapi: OpenAPIGenerator,
) -> Callable[[], JsonLike]:
    """
    TODO write documentation
    :param app:
    :param get_openapi:
    :return:
    """
    def custom_openapi():
        if not app.openapi_schema:
            app.openapi_schema = get_openapi(
                title=app.title,
                version=app.version,
                description=app.description,
                routes=app.routes,
                servers=app.servers
            )

        result = parse(app.openapi_schema)
        Token.reset_all_cache()

        return result

    return custom_openapi
