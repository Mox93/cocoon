# Pynamic

> A FastAPI extension for making openapi.json values dynamic.

Easily and quickly give openapi.json customizable dynamic values. Pynamic provides built-in dynamic variables that can be used as examples (e.g. `FULL_NAME`, `EMAIL`, `PHONE_NUMBER`, etc...), it also provides the ability to create custom tokens that can be used anywhere.

## Installation

This package can be install with or without Faker. If the built-in dynamic variables will be used, then install it as following:

```bash
pip install pynamic[faker]
```

Otherwise, simply install the package only:

```bash
pip install pynamic
```

> Faker can be installed afterward if dynamic variables were needing later on.

## Usage Examples

### Example 1

```python
from fastapi import FastAPI, Query
from fastapi.openapi.utils import get_openapi
from pynamic import dynamic_openapi, dynamic_variables as dv

app = FastAPI()


@app.get("/greeting")
async def greet(name: str = Query(None, example=dv.FIRST_NAME)):
    return {"greeting": f"Hello {name or 'World'}"}


app.openapi = dynamic_openapi(app, get_openapi)
```

To get dynamically generated values with pynamic, there are only two steps:

**step 1:** assign a token instance to the variable the needs a dynamic value.

```python
example=dv.FIRST_NAME
```

**step 2:** replace the app's default openapi method with the output of the dynamic openapi function.

```python
app.openapi = dynamic_openapi(app, get_openapi)
```

### Example 2

```python
from pynamic import Token, dynamic_variables as dv


def bla_bla_factory(count: int = 1):
    def inner_func():
        nonlocal count
        result = ("bla " * count)[:-1]
        count += 1
        return result

    return inner_func


bla_bla = Token(bla_bla_factory())

conversation = f"""
{dv.FIRST_NAME[1]}: {bla_bla}
{dv.FIRST_NAME[2]}: {bla_bla["whaterver"]}
{dv.FIRST_NAME[1]}: {bla_bla}
{dv.FIRST_NAME[2]}: {bla_bla}
{dv.FIRST_NAME[1]}: {bla_bla["whaterver"]}
{dv.FIRST_NAME[2]}: {bla_bla}
"""

print(Token.parse(conversation))

# Output:
"""
Erin: bla
Jeremy: bla bla
Erin: bla bla bla
Jeremy: bla bla bla bla
Erin: bla bla
Jeremy: bla bla bla bla bla
"""
```

In this example there are a couple of concepts:

1. **Custom tokens:** To create a token with special behavior, a function that returns the desired values is passed to a new token instance. In this example the passed function will increase the number of times it repeats the phrase "bla" by one each time it's called.

   ```python
   bla_bla = Token(bla_bla_factory())
   ```
   
   > Notice that the function bla_bla_factory returns a function, and that's what will be used to generate the dynamic values. The reason it's written that way is to keep track of the count variable, this is something called closures.
   
1. **Caching tokens:** In some use cases it might be required to use the same dynamic value in multiple places *(like in the case of this fake conversation between two random people)*. This is achieved by passing a key *(of type integer or string)* to the token instance, a cached instance of the token with a static value will be returned.

   ```python
   bla_bla["whaterver"]
   ```

1. **Parsing strings:** When it's time to convert the raw string containing the tokens into its final form, the raw string should be passed to the token's class method `parse`.

   ```python
   print(Token.parse(conversation))
   ```

   
