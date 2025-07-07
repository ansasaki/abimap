.. start-badges

|docs| |ci| |coveralls| |codecov|

.. |docs| image:: https://readthedocs.org/projects/abimap/badge/?style=flat
    :target: https://readthedocs.org/projects/abimap
    :alt: Documentation Status

.. |ci| image:: https://github.com/ansasaki/abimap/workflows/CI/badge.svg
    :target: https://github.com/ansasaki/abimap/actions
    :alt: GitHub Actions CI Status



.. |coveralls| image:: https://coveralls.io/repos/github/ansasaki/abimap/badge.svg?branch=master
    :alt: Coverage Status
    :target: https://coveralls.io/github/ansasaki/abimap?branch=master

.. |codecov| image:: https://codecov.io/github/ansasaki/abimap/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/ansasaki/abimap


.. end-badges

abimap
======

A helper for library maintainers to use symbol versioning

Why use symbol versioning?
--------------------------

The main reason is to be able to keep the library [ABI]_ stable.

If a library is intended to be used for a long time, it will need updates for
eventual bug fixes and/or improvement.
This can lead to changes in the [API]_ and, in the worst case, changes to the
[ABI]_.

Using symbol versioning, it is possible to make compatible changes and keep the
applications working without recompiling.
If incompatible changes were made (breaking the [ABI]_), symbol versioning allows both
incompatible versions to live in the same system without conflict.
And even more uncommon situations, like an application to be linked to
different (incompatible) versions of the same library.

For more information, I strongly recommend reading:

- [HOW_TO]_ How to write shared libraries, by Ulrich Drepper

How to add symbol versioning to my library?
-------------------------------------------

Adding version information to the symbols is easy.
Keeping the [ABI]_ stable, unfortunately, is not. This project intends to help in the first part.

To add version information to symbols of a library, one can use version scripts (in Linux).
Version scripts are files used by linkers to map symbols to a given version.
It contains the symbols exported by the library grouped by the releases where they were introduced. For example::

  LIB_EXAMPLE_1_0_0
    {
      global:
        symbol;
        another_symbol;
      local:
        *;
    };

In this example, the release ``LIB_EXAMPLE_1_0_0`` introduces the symbols ``symbol`` and ``another_symbol``.
The ``*`` wildcard in ``local`` catches all other symbols, meaning only ``symbol`` and ``another_symbol`` are globally exported as part of the library [API]_.

If a compatible change is made, it would introduce a new release, like::

  LIB_EXAMPLE_1_0_0
  {
      global:
          symbol;
          another_symbol;
      local:
          *;
  };

  LIB_EXAMPLE_1_1_0
  {
      global:
          new_symbol;
  } LIB_EXAMPLE_1_0_0;


The new release ``LIB_EXAMPLE_1_1_0`` introduces the symbol ``new_symbol``.
The ``*`` wildcard should be only in one version, usually in the oldest version.
The ``} LIB_EXAMPLE_1_0_0;`` part in the end of the new release means the new release depends on the old release.

Suppose a new incompatible version ``LIB_EXAMPLE_2_0_0`` released after ``LIB_EXAMPLE_1_1_0``. Its map would look like::

  LIB_EXAMPLE_2_0_0
  {
      global:
          a_newer_symbol;
          another_symbol;
          new_symbol;
      local:
          *;
  };

The symbol ``symbol`` was removed (and that is why it was incompatible). And a new symbol was introduced, ``a_newer_symbol``.

Note that all global symbols in all releases were merged in a unique new release.

Installation:
-------------

At the command line::

  pip install abimap

Usage:
------

This project delivers a script, ``abimap``. This is my first project in python, so feel free to point out ways to improve it.

The sub-commands ``update`` and ``new`` expect a list of symbols given in stdin. The list of symbols are words separated by non-alphanumeric characters (matches with the regular expression ``[a-zA-Z0-9_]+``). For example::

  symbol, another, one_more

and::

  symbol
  another
  one_more

are valid inputs.

The last sub-command, ``check``, expects only the path to the map file to be
checked.

tl;dr
-----
::

  $ abimap update lib_example.map < symbols_list

or (setting an output)::

  $ abimap update lib_example.map -o new.map < symbols_list

or::

  $ cat symbols_list | abimap update lib_example.map -o new.map

or (to create a new map)::

  $ cat symbols_list | abimap new -r lib_example_1_0_0 -o new.map

or (to check the content of a existing map)::

  $ abimap check my.map

or (to check the current version)::

  $ abimap version

Long version
------------

Running  ``abimap -h`` will give::

  usage: abimap [-h] {update,new,check,version} ...
  
  Helper tools for linker version script maintenance
  
  options:
    -h, --help            show this help message and exit
  
  Subcommands:
    {update,new,check,version}
                          These subcommands have their own set of options
      update              Update the map file
      new                 Create a new map file
      check               Check the map file
      version             Print version
  
  Call a subcommand passing '-h' to see its specific options

Call a subcommand passing '-h' to see its specific options
There are four subcommands, ``update``, ``new``, ``check``, and ``version``

Running ``abimap update -h`` will give::

  usage: abimap update [-h] [-o OUT] [-i INPUT] [-d] [--verbosity {quiet,error,warning,info,debug} | --quiet | --debug] [-l LOGFILE] [-n NAME] [-v VERSION] [-r RELEASE] [--no_guess]
                       [--allow-abi-break] [-f] [-a | --remove]
                       file
  
  positional arguments:
    file                  The map file being updated
  
  options:
    -h, --help            show this help message and exit
    -o, --out OUT         Output file (defaults to stdout)
    -i, --in INPUT        Read from this file instead of stdio
    -d, --dry             Do everything, but do not modify the files
    --verbosity {quiet,error,warning,info,debug}
                          Set the program verbosity
    --quiet               Makes the program quiet
    --debug               Makes the program print debug info
    -l, --logfile LOGFILE
                          Log to this file
    -n, --name NAME       The name of the library (e.g. libx)
    -v, --version VERSION
                          The release version (e.g. 1_0_0 or 1.0.0)
    -r, --release RELEASE
                          The full name of the release to be used (e.g. LIBX_1_0_0)
    --no_guess            Disable next release name guessing
    --allow-abi-break     Allow removing symbols, and to break ABI
    -f, --final           Mark the modified release as final, preventing later changes.
    -a, --add             Adds the symbols to the map file.
    --remove              Remove the symbols from the map file. This breaks the ABI.
  
  A list of symbols is expected as the input. If a file is provided with '-i', the symbols are read from the given file. Otherwise the symbols are read from stdin.

Running ``abimap new -h`` will give::

  usage: abimap new [-h] [-o OUT] [-i INPUT] [-d] [--verbosity {quiet,error,warning,info,debug} | --quiet | --debug] [-l LOGFILE] [-n NAME] [-v VERSION] [-r RELEASE] [--no_guess] [-f]
  
  options:
    -h, --help            show this help message and exit
    -o, --out OUT         Output file (defaults to stdout)
    -i, --in INPUT        Read from this file instead of stdio
    -d, --dry             Do everything, but do not modify the files
    --verbosity {quiet,error,warning,info,debug}
                          Set the program verbosity
    --quiet               Makes the program quiet
    --debug               Makes the program print debug info
    -l, --logfile LOGFILE
                          Log to this file
    -n, --name NAME       The name of the library (e.g. libx)
    -v, --version VERSION
                          The release version (e.g. 1_0_0 or 1.0.0)
    -r, --release RELEASE
                          The full name of the release to be used (e.g. LIBX_1_0_0)
    --no_guess            Disable next release name guessing
    -f, --final           Mark the new release as final, preventing later changes.
  
  A list of symbols is expected as the input. If a file is provided with '-i', the symbols are read from the given file. Otherwise the symbols are read from stdin.

Running ``abimap check -h`` will give::

  usage: abimap check [-h] [--verbosity {quiet,error,warning,info,debug} | --quiet | --debug] [-l LOGFILE] file
  
  positional arguments:
    file                  The map file to be checked
  
  options:
    -h, --help            show this help message and exit
    --verbosity {quiet,error,warning,info,debug}
                          Set the program verbosity
    --quiet               Makes the program quiet
    --debug               Makes the program print debug info
    -l, --logfile LOGFILE
                          Log to this file

Running ``abimap version -h`` will give::

  usage: abimap version [-h]
  
  options:
    -h, --help  show this help message and exit

Import as a library:
--------------------

To use abimap in a project as a library::

	from abimap import symver

Documentation:
--------------

Check in `Read the docs`_

References:
-----------
.. [ABI] https://en.wikipedia.org/wiki/Application_binary_interface
.. [API] https://en.wikipedia.org/wiki/Application_programming_interface
.. [HOW_TO] https://www.akkadia.org/drepper/dsohowto.pdf, How to write shared libraries by Ulrich Drepper
.. _Read the docs: https://abimap.readthedocs.io/en/latest/index.html
