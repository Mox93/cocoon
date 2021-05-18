from cocoon.token_ import Token


# TODO: (use cases)
#  - pass a token for None so it doesn't get filter out by FastAPI. [DONE]
#  - generate a new fake value for each token instance. [DONE]
#  - have multiple proxy instances share the same fake value. [DONE]
#  - define custom proxies. [DONE]
#  - configure the Faker instance used for generating values. [DONE]


# For use in the Field example argument instead of <None> because
# FastAPI ignores it
# >>> ... address: str = Field(None, example=NONE)
# // will show in openapi.json as such:
# ..."address":{..."type":"string","example":null}
NONE = Token(None, full_match=True)

# Placeholders for dynamically generated fake values for use in
# examples
ADDRESS = Token(Token.core.address)
FIRST_NAME = Token(Token.core.first_name)
NAME = Token(Token.core.name)
TEXT = Token(Token.core.text)
