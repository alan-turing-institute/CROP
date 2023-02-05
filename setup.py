from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name="cropcore",
    version="3.0.0",
    url="https://github.com/alan-turing-institute/CROP",
    description="digital twin of an underground farm",
    install_requires=required,
    packages=['cropcore'],
    package_dir={"cropcore": "core"}
)
