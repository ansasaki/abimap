# -*- coding: utf-8 -*-

import os

here = os.path.abspath(os.path.dirname(__file__))

# Version info -- read without importing
_locals = {}
with open(os.path.join(here, 'src', 'abimap', '_version.py')) as fp:
    exec(fp.read(), None, _locals)
version = _locals["__version__"]

def get_version():
    """
    Print and return the version based on _version.py

    :returns: abimap current version
    """

    print(version)

    return version


def get_name_version():
    """
    Print and return the name and version based on _version.py

    :returns: abimap name and version
    """

    name_version = "abimap-" + version

    print (name_version)

    return name_version


if __name__ == "__main__":
    get_name_version()
