import os
from setuptools import setup

with open("requirements.txt") as f:
    required = f.read().splitlines()

setup(
    name="cropcore",
    version="3.0",
    description="core functionality for the CROP digital twin",
    url="https://github.com/alan-turing-institute/CROP",
    author="The Alan Turing Institute Research Engineering Group",
    license="MIT",
    packages=["cropcore"],
    package_dir={"cropcore": "core"},
    install_requires=required,
    zip_safe=False,
)
