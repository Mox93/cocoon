from cocoon.token_ import Token


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
