#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import os
from glob import glob
from os.path import basename
from os.path import splitext

from setuptools import find_packages
from setuptools import setup
from version import get_version

package_name = "symver-smap"
here = os.path.abspath(os.path.dirname(__file__))

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = []

setup_requirements = ['pytest-runner']

test_requirements = ['pytest', 'pyyaml', 'pytest-cov', 'pytest-console-scripts']

version = get_version()

setup(
    author="Anderson Toshiyuki Sasaki",
    author_email='ansasaki@redhat.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    description="A helper for library maintainers to use symbol versioning ",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='symver smap symbol version versioning linker script library maintenance',
    name=package_name,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob(
        os.path.join(here, 'src', 'smap', '*.py'))],
    entry_points={
        'console_scripts': ['smap=smap.main:main']
    },
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/ansasaki/smap',
    version=version,
    zip_safe=False,
)
