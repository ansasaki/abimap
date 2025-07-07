#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import os
from glob import glob
from os.path import basename
from os.path import splitext

from setuptools import find_packages
from setuptools import setup

package_name = "abimap"
here = os.path.abspath(os.path.dirname(__file__))

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

setup(
    author="Anderson Toshiyuki Sasaki",
    author_email='ansasaki@redhat.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
    description="A helper for library maintainers to use symbol versioning ",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='symver abimap symbol version versioning linker script library maintenance',
    name=package_name,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob(
        os.path.join(here, 'src', 'abimap', '*.py'))],
    entry_points={
        'console_scripts': ['abimap=abimap.main:main']
    },
    url='https://github.com/ansasaki/abimap',
    zip_safe=False,
)
