from pynamic.parser import parse, dynamic_openapi
from pynamic.token import Token


__author__ = "Mohamed Ragaey Saleh"
__license__ = "MIT"
__version__ = "0.1.0"
__maintainer__ = "Mohamed Ragaey Saleh"
__email__ = "mohamed.ragaiy.saleh@gmail.com"
__status__ = "Prototype"


__all__ = (
    dynamic_openapi,
    parser,
    Token,
)


# TODO: (use cases)
#  - pass a token for None so it doesn't get filter out by FastAPI. [DONE]
#  - generate a new fake value for each token instance. [DONE]
#  - have multiple token instances share the same fake value. [DONE]
#  - define custom proxies. [DONE]
#  - configure the Faker instance used for generating values. [DONE]
