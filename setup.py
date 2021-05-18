from setuptools import (
    find_packages,
    setup,
)

from cocoon import (
    __version__,
    __author__,
    __license__,
)


setup(
    name="cocoon",
    packages=find_packages(include=["cocoon"]),
    version=__version__,
    description=(
        "A python library inspired by Postman's dynamic variables"
    ),
    author=__author__,
    license=__license__,
    extras_require={
        "faker": ["Faker==8.1.3"]
    },
)
