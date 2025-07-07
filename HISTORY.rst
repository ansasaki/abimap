=======
History
=======

0.4.0 (2025-07-07)
------------------

* Fixed Makefile clean targets to properly handle both files and directories
* Updated build system to use modern ``python -m build`` instead of deprecated ``python setup.py`` commands
* Fixed linting target to use ``python -m flake8`` for better reliability
* Added flake8 to development dependencies and requirements-test.txt
* Fixed documentation build by adding Sphinx dependencies and using ``python -m sphinx``
* Made Makefile portable by using dynamic make command detection with ``$(shell command -v make)``
* Updated development dependencies to include build tools (build, sphinx, sphinx-rtd-theme, watchdog)
* Made documentation linkcheck non-fatal to handle broken external links gracefully
* Improved development workflow with proper dependency management

0.3.2 (2019-08-05)
------------------

* Fixed broken builds due to changes in warning output
* Changed tests to check error messages
* Added python 3.7 to testing matrix
* Added requirement to verify SNI when checking URLs in docs

0.3.1 (2018-08-20)
------------------

* Fixed bug when sorting releases: the older come first
* Added missing runtime requirement for setuptools
* Added manpage generation

0.3.0 (2018-08-03)
------------------

* Complete rename of the project to abimap

0.2.5 (2018-07-26)
------------------

* Add tests using different program names
* Use the command line application name in output strings
* Add a new entry point symver-smap for console scripts
* Skip tests which use caplog if pytest version is < 3.4
* Added an alias for pytest in setup.cfg. This fixed setup.py for test target

0.2.4 (2018-06-15)
------------------

* Removed dead code, removed executable file permission
* Removed appveyor related files

0.2.3 (2018-06-15)
------------------

* Removed shebangs from scripts

0.2.2 (2018-06-01)
------------------

* Fixed a bug in updates with provided release information
* Fixed a bug in get_info_from_release_string()

0.2.1 (2018-05-30)
------------------

* Fixed a bug where invalid characters were accepted in release name

0.2.0 (2018-05-29)
------------------

* Added version information in output files
* Added sub-command "version" to output name and version
* Added option "--final" to mark modified release as released
* Prevent releases marked with the special comment "# Released" to be modified
* Allow existing release update
* Detect duplicated symbols given as input

0.1.0 (2018-05-09)
------------------

* First release on PyPI.
