# Pynamic

> A FastAPI extension for making openapi.json values dynamic.

Easily and quickly give openapi.json customizable dynamic values. Pynamic provides built-in dynamic variables that can be used as examples (e.g. `FULL_NAME`, `EMAIL`, `PHONE_NUMBER`, etc...), it also provides the ability to create custom tokens that can be used anywhere.

## Installation

This package can be install with or without Faker. If the built-in dynamic variables are going to be used, then install it as following:

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

**step 1:** Assign a token instance to the variable the needs a dynamic value.

```python
example=dv.FIRST_NAME
```

**step 2:** Replace the app's default openapi method with the output of the dynamic openapi function.

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




## API

---

**`Token(...)`**

The Token class is a subclass of string. Creating an instance of Token returns a placeholder used for injecting the replacement value.

Arguments:

​	[required]

* `replacement`: \<any\>
  The value or callable (that returns a value) that gets injected at the time of parsing.

​	[optional]

* `full_match`: \<bool\> `=False`
  Whether the replacement value should be a stand alone token or can be part of a string.
* `anonymous`: \<bool\> `=False`
  Whether this instance should be held onto for parsing or not.
* `call_depth`: \<int\> `=10`
  The number of nested callables a replacement can have.
* `always_replace`: \<bool\> `=False`
  Determines how to handle the replacement after exceeding the `call_depth`. If `True` the replacement will be returned regardless of its type. If `False` a `RuntimeError` will be raised if the replacement is still a callable.

```python
NONE = Token(None, full_match=True)
```

---

**`Token.core`** *(class property)*

Returns a proxy object that can be used as if it's the Faker instance. This should only be used for the replacement argument while creating a Token instance.

```python
NAME = Token(Token.core.first_name)

ALPHA_NUMERIC = Token(
    Token.core.random_element(
        elements=(
            Token.core.random_digit(),
            Token.core.random_lowercase_letter(),
        )
    )
)
```

> **Notes:**
>
> * In the example above, passing the function itself `Token.core.first_name` or calling it `Token.core.first_name()` will be handled the same.
> * By default the core property represents a Faker instance, so Faker should be installed in order for it to work out of the box. It is possible to have core represent a **customized instance of Faker** *(e.g. with support for other languages)*  or **different random value generator** by passing the generator to `Token.set_core(new_core)`.

---

**`Token.set_core(...)`** *(class method)*

Used for replacing the instance of Faker that is used by the proxy object.

Arguments:

​	[required]

* `core`: \<any\>
  The instance of the random value generator that will be used by proxy object.

​	[optional]

* `reset`: \<bool\> `=True`
  Weather or not values of the cached tokens using the old core should be replaced with valued using the new core.

---

**`Token.parse(...)`** *(class method)*

---

**`Token.reset_all_cache(...)`** *(class method)*

---

**`token.value`** *(instance property)*

---

**`token.inject_into(...)`** *(instance method)*

---

**`token.reset_cache(...)`** *(instance method)*

---

**`parse(...)`**

---

**`dynamic_openapi(...)`**

---
