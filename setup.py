from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

installRequires = [
        "requests",
        "lxml",
        "pySmartDL",
        "wheel",
        "regex",]

setup(
    name="aw-cli",
    packages=find_packages(include=["awcli"]),
    version="2.0",
    python_requires=">3.10",
    description="guarda anime dal terminale e molto altro!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="fexh10",
    url="https://github.com/fexh10/aw-cli",
    license="GPL-3.0",
    install_requires=installRequires,
    entry_points="[console_scripts]\naw-cli=awcli.run:main",
    include_package_data=True,
)
