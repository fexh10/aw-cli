from setuptools import find_packages, setup
    
setup(
    name="aw-cli",
    packages=find_packages(include=["awcli"]),
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
    entry_points="[console_scripts]aw-cli=awcli.run:main",

)

