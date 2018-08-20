SUBCOMMANDS
===========

``abimap update``
-----------------

   Update an existing map file
   ::

      abimap update [-h] [-o OUT] [-i INPUT] [-d]
                    [--verbosity {quiet,error,warning,info,debug} | --quiet | --debug]
                    [-l LOGFILE] [-n NAME] [-v VERSION]
                    [-r RELEASE] [--no_guess] [--allow-abi-break]
                    [-f] [-a | --remove]
                    file

   ``file``
      The map file being updated

   ``-o OUT, --out OUT``
      Output file (defaults to stdout)

   ``-i INPUT, --in INPUT``
      Read from this file instead of stdio

   ``-d, --dry``
      Do everything, but do not modify the files

   ``--verbosity {quiet,error,warning,info,debug}``
      Set the program verbosity

   ``--quiet``
      Makes the program quiet

   ``--debug``
      Makes the program print debug info

   ``-l LOGFILE, --logfile LOGFILE``:
      Log to this file

   ``-n NAME, --name NAME``
      The name of the library (e.g. libx)

   ``-v VERSION, --version VERSION``
      The release version (e.g. 1_0_0 or 1.0.0)

   ``-r RELEASE, --release RELEASE``
      The full name of the release to be used (e.g. LIBX_1_0_0)

   ``--no_guess``
      Disable next release name guessing

   ``--allow-abi-break``
      Allow removing symbols, and to break ABI

   ``-f, --final``
      Mark the modified release as final, preventing later changes.

   ``-a, --add``
      Adds the symbols to the map file.

   ``--remove``
      Remove the symbols from the map file. This breaks the ABI.

``abimap new``
--------------

   Create a new map file
   ::

      abimap new [-h] [-o OUT] [-i INPUT] [-d]
                 [--verbosity {quiet,error,warning,info,debug} | --quiet | --debug]
                 [-l LOGFILE] [-n NAME] [-v VERSION] [-r RELEASE]
                 [--no_guess] [-f]

   ``-o OUT, --out OUT``
      Output file (defaults to stdout)

   ``-i INPUT, --in INPUT``
      Read from this file instead of stdio

   ``-d, --dry``
      Do everything, but do not modify the files

   ``--verbosity {quiet,error,warning,info,debug}``
      Set the program verbosity

   ``--quiet``
      Makes the program quiet

   ``--debug``
      Makes the program print debug info

   ``-l LOGFILE, --logfile LOGFILE``
      Log to this file

   ``-n NAME, --name NAME``
      The name of the library (e.g. libx)

   ``-v VERSION, --version VERSION``
      The release version (e.g. 1_0_0 or 1.0.0)

   ``-r RELEASE, --release RELEASE``
      The full name of the release to be used (e.g. LIBX_1_0_0)

   ``--no_guess``
      Disable next release name guessing

   ``-f, --final``
      Mark the new release as final, preventing later changes.

``abimap check``
----------------

   Check the syntax of a map file
   ::

      abimap check [-h]
                   [--verbosity {quiet,error,warning,info,debug} | --quiet | --debug]
                   [-l LOGFILE]
                   file

   ``file``
      The map file to be checked

   ``--verbosity {quiet,error,warning,info,debug}``
      Set the program verbosity

   ``--quiet``
      Makes the program quiet

   ``--debug``
      Makes the program print debug info

   ``-l LOGFILE, --logfile LOGFILE``
      Log to this file

``abimap version``
------------------

   Prints the tool version number

   ``usage``::

      abimap version [-h]

