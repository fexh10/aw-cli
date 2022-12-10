from setuptools import find_packages, setup
    
setup(
    name="aw-cli",
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
<<<<<<< HEAD
<<<<<<< HEAD
     entry_points="[console_scripts]aw-cli=aw-cli:main",
     py_modules=['aw-cli'],

=======
    entry_points="[console_scripts]aw-cli=aw-cli:main",
>>>>>>> b274f43 (Update setup.py)
=======
    entry_points="[console_scripts]\aw-cli=aw_cli.run_aw_cli:main",

>>>>>>> d6df4ff (Update setup.py)
)

