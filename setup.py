from setuptools import setup

setup(
    name="aw-cli",
    py_modules=['aw-cli'],
    version="1.0",
    python_requires=">3.10",
    description="guarda anime dal terminale e molto altro!",
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
    ],
     entry_points="[console_scripts]\naw-cli=aw-cli:main",
)

