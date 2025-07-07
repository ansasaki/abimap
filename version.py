# -*- coding: utf-8 -*-

import os
import sys

here = os.path.abspath(os.path.dirname(__file__))

# Add src directory to path so we can import the package
sys.path.insert(0, os.path.join(here, 'src'))

try:
    from abimap._version import __version__
    version = __version__
except ImportError:
    # Fallback to reading file directly
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
