from cocoon.token_ import Token


def deep_inject(obj):
    if isinstance(obj, (str, Token)):
        return Token.parse(obj)

    if isinstance(obj, dict):
        return {
            key: deep_inject(value) for key, value in obj.items()
        }

    if isinstance(obj, (list, tuple, set)):
        return obj.__class__(deep_inject(value) for value in obj)

    return obj
