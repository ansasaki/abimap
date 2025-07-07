=====
Usage
=====

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
