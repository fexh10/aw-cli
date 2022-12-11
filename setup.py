from setuptools import find_packages, setup
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="aw-cli",
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
    py_modules=['aw-cli'],
>>>>>>> b274f43 (Update setup.py)
=======
    packages=find_packages(include=["aw-cli"]),
>>>>>>> d6df4ff (Update setup.py)
=======
    packages=find_packages(include=["aw_cli"]),
>>>>>>> 80a9cd3 (Update setup.py)
=======
    packages=find_packages(include=["aw-cli"]),
>>>>>>> 400b07f (Update setup.py)
=======
    packages=find_packages(include=["awcli"]),
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> 46c4374 (Update setup.py)
    version="1.0",
=======
    version="1.1",
>>>>>>> 4d011ad (Update setup.py)
=======
    version="1.0.2",
>>>>>>> 9aefcc1 (Aggiunta la descrizione al setup e modificata la versione)
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
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
     entry_points="[console_scripts]aw-cli=aw-cli:main",
     py_modules=['aw-cli'],
=======
    entry_points="[console_scripts]aw-cli=awcli.run:main",
>>>>>>> 46c4374 (Update setup.py)

=======
    entry_points="[console_scripts]aw-cli=aw-cli:main",
>>>>>>> b274f43 (Update setup.py)
=======
    entry_points="[console_scripts]\aw-cli=aw_cli.run_aw_cli:main",
=======
    entry_points="[console_scripts]\aw-cli=aw-cli.run:main",
>>>>>>> 400b07f (Update setup.py)

>>>>>>> d6df4ff (Update setup.py)
=======
    entry_points="[console_scripts]\naw-cli=awcli.run:main",
>>>>>>> 4d011ad (Update setup.py)
)
