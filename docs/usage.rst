=====
Usage
=====

This project delivers a script, ``smap``. This is my first project in python, so feel free to point out ways to improve it.

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

  $ smap update lib_example.map < symbols_list

or (setting an output)::

  $ smap update lib_example.map -o new.map < symbols_list

or::

  $ cat symbols_list | smap update lib_example.map -o new.map

or (to create a new map)::

  $ cat symbols_list | smap new -r lib_example_1_0_0 -o new.map

or (to check the content of a existing map)::

  $ smap check my.map

or (to check the current version)::

  $ smap version

Long version
------------

Running  ``smap -h`` will give::

  usage: smap [-h] {update,new,check,version} ...
  
  Helper tools for linker version script maintenance
  
  optional arguments:
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

Running ``smap update -h`` will give::

  usage: smap update [-h] [-o OUT] [-i INPUT] [-d]
                     [--verbosity {quiet,error,warning,info,debug} | --quiet | --debug]
                     [-l LOGFILE] [-n NAME] [-v VERSION] [-r RELEASE]
                     [--no_guess] [--allow-abi-break] [-f] [-a | --remove]
                     file
  
  positional arguments:
    file                  The map file being updated
  
  optional arguments:
    -h, --help            show this help message and exit
    -o OUT, --out OUT     Output file (defaults to stdout)
    -i INPUT, --in INPUT  Read from this file instead of stdio
    -d, --dry             Do everything, but do not modify the files
    --verbosity {quiet,error,warning,info,debug}
                          Set the program verbosity
    --quiet               Makes the program quiet
    --debug               Makes the program print debug info
    -l LOGFILE, --logfile LOGFILE
                          Log to this file
    -n NAME, --name NAME  The name of the library (e.g. libx)
    -v VERSION, --version VERSION
                          The release version (e.g. 1_0_0 or 1.0.0)
    -r RELEASE, --release RELEASE
                          The full name of the release to be used (e.g.
                          LIBX_1_0_0)
    --no_guess            Disable next release name guessing
    --allow-abi-break     Allow removing symbols, and to break ABI
    -f, --final           Mark the modified release as final, preventing later
                          changes.
    -a, --add             Adds the symbols to the map file.
    --remove              Remove the symbols from the map file. This breaks the
                          ABI.
  
  A list of symbols is expected as the input. If a file is provided with '-i',
  the symbols are read from the given file. Otherwise the symbols are read from
  stdin.

Running ``smap new -h`` will give::

  usage: smap new [-h] [-o OUT] [-i INPUT] [-d]
                  [--verbosity {quiet,error,warning,info,debug} | --quiet | --debug]
                  [-l LOGFILE] [-n NAME] [-v VERSION] [-r RELEASE] [--no_guess]
                  [-f]
  
  optional arguments:
    -h, --help            show this help message and exit
    -o OUT, --out OUT     Output file (defaults to stdout)
    -i INPUT, --in INPUT  Read from this file instead of stdio
    -d, --dry             Do everything, but do not modify the files
    --verbosity {quiet,error,warning,info,debug}
                          Set the program verbosity
    --quiet               Makes the program quiet
    --debug               Makes the program print debug info
    -l LOGFILE, --logfile LOGFILE
                          Log to this file
    -n NAME, --name NAME  The name of the library (e.g. libx)
    -v VERSION, --version VERSION
                          The release version (e.g. 1_0_0 or 1.0.0)
    -r RELEASE, --release RELEASE
                          The full name of the release to be used (e.g.
                          LIBX_1_0_0)
    --no_guess            Disable next release name guessing
    -f, --final           Mark the new release as final, preventing later
                          changes.
  
  A list of symbols is expected as the input. If a file is provided with '-i',
  the symbols are read from the given file. Otherwise the symbols are read from
  stdin.

Running ``smap check -h`` will give::

  usage: smap check [-h]
                    [--verbosity {quiet,error,warning,info,debug} | --quiet | --debug]
                    [-l LOGFILE]
                    file
  
  positional arguments:
    file                  The map file to be checked
  
  optional arguments:
    -h, --help            show this help message and exit
    --verbosity {quiet,error,warning,info,debug}
                          Set the program verbosity
    --quiet               Makes the program quiet
    --debug               Makes the program print debug info
    -l LOGFILE, --logfile LOGFILE
                          Log to this file

Running ``smap version -h`` will give::

  usage: smap version [-h]
  
  optional arguments:
    -h, --help  show this help message and exit

Import as a library:
--------------------

To use smap in a project as a library::

	from smap import symver
