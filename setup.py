from setuptools import find_packages, setup
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="aw-cli",
    packages=find_packages(include=["awcli"]),
    version="1.2",
    python_requires=">3.10",
    description="guarda anime dal terminale e molto altro!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="fexh10",
    url="https://github.com/fexh10/aw-cli",
    license="GPL-3.0",
    install_requires=[
        "bs4",
        "requests",
        "python-mpv",
        "lxml",
        "pySmartDL",
        "hpcomt",
        "wheel",
    ],
    entry_points="[console_scripts]\naw-cli=awcli.run:main",
)