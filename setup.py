from setuptools import setup

from pynamic import (
    __package__,
    __author__,
    __email__,
    __license__,
    __version__,
)


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name=__package__,
    version=__version__,
    author=__author__,
    author_email=__email__,
    url="https://github.com/Mox93/pynamic",
    description="A package for injecting dynamic values into strings.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license=__license__,
    packages=[__package__],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Operating System :: POSIX :: Linux",
        "Environment :: Console",
        "Environment :: MacOS X",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet",
    ],
    py_modules=[__package__],
    extras_require={"faker": ["Faker==8.1.3"]},
    python_requires=">=3.6",
)
