NOTES
=====

Why use symbol versioning?
--------------------------

The main reason is to be able to keep the library ``[ABI]`` stable.

If a library is intended to be used for a long time, it will need updates for
eventual bug fixes and/or improvement.
This can lead to changes in the ``[API]`` and, in the worst case, changes to the
``[ABI]``.

Using symbol versioning, it is possible to make compatible changes and keep the
applications working without recompiling.
If incompatible changes were made (breaking the ``[ABI]``), symbol versioning allows both
incompatible versions to live in the same system without conflict.
And even more uncommon situations, like an application to be linked to
different (incompatible) versions of the same library.

For more information, I strongly recommend reading:

- ``[HOW_TO]`` How to write shared libraries, by Ulrich Drepper

How to add symbol versioning to my library?
-------------------------------------------

Adding version information to the symbols is easy.
Keeping the ``[ABI]`` stable, unfortunately, is not. This project intends to help in the first part.

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
The ``*`` wildcard in ``local`` catches all other symbols, meaning only ``symbol`` and ``another_symbol`` are globally exported as part of the library ``[API]``.

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

References:
-----------

- ``[ABI]`` https://en.wikipedia.org/wiki/Application_binary_interface
- ``[API]`` https://en.wikipedia.org/wiki/Application_programming_interface
- ``[HOW_TO]`` https://www.akkadia.org/drepper/dsohowto.pdf, How to write shared libraries by Ulrich Drepper
