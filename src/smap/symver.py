#!/usr/bin/env python
from __future__ import print_function

import argparse
import logging
import os
import re
import shutil
import sys
from itertools import chain

from ._version import __version__

VERBOSITY_MAP = {"debug": logging.DEBUG,
                 "info": logging.INFO,
                 "warning": logging.WARNING,
                 "error": logging.ERROR,
                 "quiet": logging.CRITICAL}


###############################################################################
# Classes
###############################################################################

class Single_Logger(object):
    """
    A singleton logger for the module

    This class is a singleton logger factory. It takes advantage of the
    uniqueness of class attributes to hold a unique instance of the logger for
    the module.
    It logs to the default log output, and prints WARNING and ERROR messages to
    stderr.
    It allows the caller to provide a file to receive the log (the messages will
    be logged by all handlers: to stderr if WARNING or ERROR, to default log,
    and to the provided file)

    Attributes:
        __instance: Holds the unique instance given by the factory when called.
    """
    __instance = None

    @classmethod
    def getLogger(cls, name, filename=None):
        """
        Get the unique instance of the logger

        :param name: The name of the module (usually just __name__)
        :returns: An instance of logging.Logger
        """

        if Single_Logger.__instance is None:
            # Get logger
            logger = logging.getLogger(name)

            # Setup a handler to print warnings and above to stderr
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            console_format = "[%(levelname)s] %(message)s"
            console_formatter = logging.Formatter(console_format)
            console_handler.setFormatter(console_formatter)

            logger.addHandler(console_handler)

            Single_Logger.__instance = logger

        if filename:
            # If a new logfile is added, a handler is added
            file_handler = logging.FileHandler(filename)
            file_format = "[%(levelname)s] (%(asctime)s) in"\
                          " %(filename)s, line %(lineno)d:"\
                          " %(message)s"
            file_formatter = logging.Formatter(file_format)
            file_handler.setFormatter(file_formatter)
            Single_Logger.__instance.addHandler(file_handler)

        return Single_Logger.__instance


class ParserError(Exception):
    """
    Exception type raised by the map parser

    Used mostly to keep track where an error was found in the given file

    Attributes:
        filename:    The name (path) of the file being parsed
        context:     The line where the error was detected
        line:        The index of the line where the error was detected
        column:      The index of the column where the error was detected
        message:     The error message
    """

    def __str__(self):
        content = ("In file {0.filename}, line {1}, column {0.column}: "
                   "{0.message}\n"
                   "{0.context}"
                   "{2:>{0.column}}").format(self, self.line + 1, '^')
        return content

    def __init__(self, filename, context, line, column, message):
        """
        The constructor

        :param filename:    The name (path) of the file being parsed
        :param context:     The line where the error was detected
        :param line:        The index of the line where the error was detected
        :param column:      The index of the column where the error was detected
        :param message:     The error message
        """
        self.filename = filename
        self.context = context
        self.line = line
        self.column = column
        self.message = message


class Map(object):
    """
    A linker map (version script) representation

    This class is an internal representation of a version script.
    It is intended to be initialized by calling the method ``read()`` and
    passing the path to a version script file.
    The parser will parse the file and check the file syntax, creating a list of
    releases (instances of the ``Release`` class), which is stored in ``releases``.

    Attributes:
        init:       Indicates if the object was initialized by calling
                    ``read()``
        logger:     The logger object; can be specified in the constructor
        filename:   Holds the name (path) of the file read
        lines:      A list containing the lines of the file
    """

    # To make printable
    def __str__(self):
        """
        Print the map in a usable form for the linker

        :returns: A string containing the whole map file as it would be written
                  in a file
        """

        content = "".join((str(release) + "\n" for release in self.releases if
                           release))
        return content

    # Constructor
    def __init__(self, filename=None, logger=None):
        """
        The constructor.

        :param filename: The name of the file to be read. If provided the
                         ``read()`` method is called using this name.
        :param logger:   A logger object. If not provided, the module based
                         logger will be used
        """

        # The state
        self.init = False
        self.releases = []
        # Logging
        self.logger = Single_Logger.getLogger(__name__)
        # From the raw file
        self.filename = ''
        self.lines = []
        if filename:
            self.read(filename)

    def parse(self, lines):
        """
        A simple version script parser.

        This is the main initializator of the ``releases`` list.
        This simple parser receives the lines of a given version script, check its
        syntax, and construct the list of releases.
        Some semantic aspects are checked, like the existence of the ``*`` wildcard
        in global scope and the existence of duplicated release names.

        It works by running a finite state machine:

         The parser states. Can be:
            0. name: The parser is searching for a release name or ``EOF``
            1. opening: The parser is searching for the release opening ``{``
            2. element: The parser is searching for an identifier name or ``}``
            3. element_closer: The parser is searching for ``:`` or ``;``
            4. previous: The parser is searching for previous release name
            5. previous_closer: The parser is searching for ``;``

        :param lines: The lines of a version script file
        """

        state = 0

        # The list of releases parsed
        releases = []
        last = (0, 0)

        for index, line in enumerate(lines):
            column = 0
            while column < len(line):
                try:
                    # Remove whitespaces or comments
                    m = re.match(r'\s+|\s*#.*$', line[column:])
                    if m:
                        column += m.end()
                        last = (index, column)
                        continue
                    # Searching for a release name
                    if state == 0:
                        self.logger.debug(">>Name")
                        m = re.match(r'\w+', line[column:])
                        if m is None:
                            raise ParserError(self.filename,
                                              lines[last[0]], last[0],
                                              last[1],
                                              "Invalid Release identifier")
                        else:
                            # New release found
                            name = m.group(0)
                            # Check if a release with this name is present
                            has_duplicate = [release for release in releases if
                                             release.name == name]
                            column += m.end()
                            r = Release()
                            r.name = m.group(0)
                            releases.append(r)
                            last = (index, column)

                            if has_duplicate:
                                msg = "Duplicated Release identifier \'{}\'"\
                                      .format(name)
                                # This is non-critical, only warning
                                self.logger.warn(ParserError(self.filename,
                                                             lines[index],
                                                             index,
                                                             column, msg))

                            # Search for the special release marker comment
                            m = re.match(r'\s*#.\s*released.*$',
                                         line[column:],
                                         re.IGNORECASE)
                            if m:
                                column += m.end()
                                r.released = True
                                last = (index, column)

                            # Advance to the next state
                            state += 1
                            continue
                    # Searching for the '{'
                    elif state == 1:
                        self.logger.debug(">>Opening")
                        found = line.find('{', column)
                        if found < 0:
                            raise ParserError(self.filename,
                                              lines[last[0]], last[0], last[1],
                                              "Missing \'{\'")
                        else:
                            column += (found + 1)
                            v = None
                            last = (index, column)
                            state += 1
                            continue
                    elif state == 2:
                        self.logger.debug(">>Element")
                        found = line.find('}', column)
                        if found >= 0:
                            self.logger.debug(">>Closer, jump to Previous")
                            column += (found + 1)
                            last = (index, column)
                            state = 4
                            continue
                        m = re.match(r'\w+|\*', line[column:])
                        if m is None:
                            raise ParserError(self.filename,
                                              lines[last[0]], last[0], last[1],
                                              "Invalid identifier")
                        else:
                            # In this case the position before the
                            # identifier is stored
                            last = (index, m.start())
                            column += m.end()
                            identifier = m.group(0)
                            state += 1
                            continue
                    elif state == 3:
                        self.logger.debug(">>Element closer")
                        found = line.find(';', column)
                        if found < 0:
                            # It was not Symbol. Maybe a new visibility.
                            found = line.find(':', column)
                            if found != column:
                                msg = "Missing \';\' or \':\' after"" \'{0}\'"\
                                      .format(identifier)
                                # In this case the current position is used
                                raise ParserError(self.filename,
                                                  lines[index], index,
                                                  column, msg)
                            else:
                                # New visibility found
                                if identifier in r.symbols:
                                    v = r.symbols[identifier]
                                else:
                                    v = []
                                    r.symbols[identifier] = v
                                column += (found + 1)
                                last = (index, column)
                                state = 2
                                continue
                        elif found == column:
                            if v is None:
                                # There was no open visibility scope
                                v = []
                                r.symbols['global'] = v
                                msg = "Missing visibility scope before"\
                                      " \'{0}\'. Symbols considered in"\
                                      " 'global:\'".format(identifier)
                                # Non-critical, only warning
                                self.logger.warn(ParserError(self.filename,
                                                             lines[last[0]],
                                                             last[0], last[1],
                                                             msg))
                            else:
                                # Symbol found
                                v.append(identifier)
                                column += (found + 1)
                                last = (index, column)
                                # Move back the state to find elements
                                state = 2
                                continue
                        else:
                            msg = "Missing \';\' or \':\' after"" \'{0}\'"\
                                  .format(identifier)
                            # In this case the current position is used
                            raise ParserError(self.filename,
                                              lines[index], index,
                                              column, msg)
                    elif state == 4:
                        self.logger.debug(">>Previous")
                        found = line.find(";", column)
                        if found == column:
                            self.logger.debug(">>Empty previous")
                            column += (found + 1)
                            last = (index, column)
                            # Move back the state to find other releases
                            state = 0
                            continue
                        m = re.match(r'\w+', line[column:])
                        if m is None:
                            raise ParserError(self.filename,
                                              lines[last[0]], last[0], last[1],
                                              "Invalid identifier")
                        else:
                            # Found previous release identifier
                            column += m.end()
                            identifier = m.group(0)
                            last = (index, column)
                            state += 1
                            continue
                    elif state == 5:
                        self.logger.debug(">>Previous closer")
                        found = line.find(";", column)
                        if found < 0:
                            raise ParserError(self.filename,
                                              lines[last[0]], last[0], last[1],
                                              "Missing \';\'")
                        elif found == column:
                            # Found previous closer
                            column += (found + 1)
                            r.previous = identifier
                            last = (index, column)
                            # Move back the state to find other releases
                            state = 0
                            continue
                        else:
                            raise ParserError(self.filename,
                                              lines[index], index,
                                              column,
                                              "Unexpected character")

                except ParserError as e:
                    # Any exception raised is considered an error
                    self.logger.error(e)
                    raise e
        # Store the parsed releases
        self.releases = releases

    def read(self, filename):
        """
        Read a linker map file (version script) and store the obtained releases

        Obtain the lines of the file and calls ``parse()`` to parse the file

        :param filename:        The path to the file to be read
        :raises ParserError:    Raised when a syntax error is found in the file
        """

        with open(filename, "r") as f:
            self.lines = f.readlines()

        self.filename = filename
        self.parse(self.lines)
        # Check the map read
        self.check()

    def all_global_symbols(self):
        """
        Returns all global symbols from all releases contained in the Map
        object

        :returns: A set containing all global symbols in all releases
        """

        if not self.init:
            msg = "Map not checked, run check()"
            self.logger.error(msg)
            raise Exception(msg)

        symbols = []
        for release in self.releases:
            if 'global' in release.symbols:
                symbols.extend(release.symbols['global'])
        return set(symbols)

    def duplicates(self):
        """
        Find and return a list of duplicated symbols for each release

        If no duplicates are found, return an empty list

        :returns: A list of tuples [(release, [(scope, [duplicates])])]
        """

        duplicates = []
        for release in self.releases:
            rel_dup = release.duplicates()
            if rel_dup:
                duplicates.append((release.name, rel_dup))
        return duplicates

    def dependencies(self):
        """
        Construct the dependencies lists

        Contruct a list of dependency lists. Each dependency list contain the
        names of the releases in a dependency path.
        The heads of the dependencies lists are the releases not refered as a
        previous release in any release.

        :returns:   A list containing the dependencies lists
        """

        def get_dependency(releases, head):
            found = [release for release in releases if release.name == head]
            if not found:
                msg = "Release \'{0}\' not found".format(head)
                self.logger.error(msg)
                raise Exception(msg)
            if len(found) > 1:
                msg = "defined more than 1 release \'{0}\'".format(head)
                self.logger.error(msg)
                raise Exception(msg)
            return found[0].previous

        solved = set()
        deps = []
        for release in self.releases:
            # If the dependencies of the current release were resolved, skip
            if release.name in solved:
                continue
            else:
                current = [release.name]
                dep = release.previous
                # Construct the current release dependency list
                while dep:
                    # If the found dependency was already in the list
                    if dep in current:
                        msg = ("Circular dependency detected!\n"
                               "    {0}".format("->".join(chain(current,
                                                                [dep]))))
                        self.logger.error(msg)
                        raise Exception(msg)
                    # Append the dependency to the current list
                    current.append(dep)

                    # Remove the releases that are not heads from the list
                    if dep in solved:
                        deps = [i for i in deps if i[0] != dep]
                    else:
                        solved.add(dep)
                    dep = get_dependency(self.releases, dep)
                solved.add(release.name)
                deps.append(current)
        return deps

    def check(self):
        """
        Check the map structure.

        Reports errors found in the structure of the map in form of warnings.
        """

        if not self.releases:
            msg = "Empty map"
            self.logger.error(msg)
            raise Exception(msg)

        have_wildcard = []
        seems_base = []

        # Find duplicated symbols
        d = self.duplicates()
        if d:
            for release, duplicates in d:
                self.logger.warn("Duplicates found in release \'%s\':", release)
                for scope, symbols in duplicates:
                    self.logger.warn("    %s:", scope)
                    self.logger.warn("\n".join(
                        (" " * 8 + symbol for symbol in symbols)))

        # Check '*' wildcard usage
        for release in self.releases:
            for scope, symbols in release.symbols.items():
                if scope == 'local':
                    if symbols:
                        if "*" in symbols:
                            self.logger.info("%s contains the local \'*\'"
                                             " wildcard", release.name)
                            if release.previous:
                                # Predecessor version and local: *; are present
                                self.logger.warn("%s should not contain the"
                                                 " local wildcard because it"
                                                 " is not the base version"
                                                 " (it refers to version %s"
                                                 " as its predecessor)",
                                                 release.name,
                                                 release.previous)
                            else:
                                # Release seems to be base: empty predecessor
                                msg = "{} seems to be the base version"\
                                      .format(release.name)
                                self.logger.info(msg)
                                seems_base.append(release.name)

                            # Append to the list of releases which contain the
                            # wildcard '*'
                            have_wildcard.append((release.name, scope))
                elif scope == 'global':
                    if symbols:
                        if "*" in symbols:
                            # Release contains '*' wildcard in global scope
                            self.logger.warn("%s contains the \'*\' wildcard"
                                             " in global scope. It is probably"
                                             " exporting symbols"
                                             " it should not.",
                                             release.name)
                            have_wildcard.append((release.name, scope))
                else:
                    # Release contains unknown visibility scopes (not global or
                    # local)
                    self.logger.warn("%s contains unknown scope named %s"
                                     " (different from \'global\' and"
                                     " \'local\')", release.name, scope)

        if have_wildcard:
            if len(have_wildcard) > 1:
                # The '*' wildcard was found in more than one place
                self.logger.warn("The \'*\' wildcard was found in more than"
                                 " one place:")
                for name, scope in have_wildcard:
                    self.logger.warn("    %s: in \'%s\'", name, scope)
        else:
            self.logger.warn("The \'*\' wildcard was not found")

        if seems_base:
            if len(seems_base) > 1:
                # There is more than one release without predecessor and
                # containing '*' wildcard in local scope
                self.logger.warn("More than one release seem to be the base"
                                 " version (contain the local wildcard and"
                                 " do not have a predecessor version):")
                for name in seems_base:
                    self.logger.warn("    %s", name)
        else:
            self.logger.warn("No base version release found")

        dependencies = self.dependencies()
        self.logger.info("Found dependencies:")
        for release in dependencies:
            content = "".join(chain(" " * 4,
                                    (dep + "->" for dep in release)))
            self.logger.info(content)

        # After calling a check, the map is considered initialized
        self.init = True

    def guess_latest_release(self):
        """
        Try to guess the latest release

        It uses the information found in the releases present in the version
        script read. It tries to find the latest release using heuristics.

        :returns:   A list [release, prefix, suffix, version[CUR, AGE, REV]]
        """

        if not self.init:
            msg = "Map not checked, run check()"
            self.logger.error(msg)
            raise Exception(msg)

        deps = self.dependencies()

        heads = (dep[0] for dep in deps)

        latest = [None, None, '_0_0_0', None]
        for release in heads:
            info = get_info_from_release_string(release)
            # This check is necessary because the suffix can be missing
            if info[2]:
                if info[2] > latest[2]:
                    latest = info

        return latest

    def guess_name(self, new_release, abi_break=False, guess=False):
        """
        Use the given information to guess the name for the new release

        The two parts necessary to make the release name:
            - The new prefix: Usually the library name (e.g. LIBX)
            - The new suffix: The version information (e.g. _1_2_3)

        If the new release is not provided, try a guess strategy:
            If the new prefix is not provided:
                1. Try to find a common prefix between release names
                2. Try to find latest release

            If the new suffix is not provided:
                1. Try to find latest release version and bump

        :param new_release: String, the name of the new release. If this is
        :param abi_break:   Boolean, indicates if the ABI was broken
        :param guess:       Boolean, indicates if should try to guess
        :returns: The guessed release name (new prefix + new suffix)
        """

        new_prefix = None
        new_suffix = None

        if new_release:
            new_prefix = new_release[1]
            new_suffix = new_release[2]

        # If the two required parts were given, just combine and return
        if new_prefix:
            if new_suffix:
                self.logger.debug("[guess]: Two parts found, using them")
                return new_prefix.upper() + new_suffix

        if guess:
            if not new_prefix:
                self.logger.debug("[guess]: Trying to find common prefix")
                # Find a common prefix between all releases
                names = [release.name for release in self.releases]
                if names:
                    s1 = min(names)
                    s2 = max(names)
                    for i, c in enumerate(s1):
                        if c != s2[i]:
                            break
                    if s1[i] != s2[i]:
                        new_prefix = s1[:i]
                    else:
                        new_prefix = s1

                    # If a common prefix was found, use it
                    if new_prefix:
                        self.logger.debug("[guess]: Common prefix found")
                        # Search and remove any version info found as prefix
                        m = re.search(r'_+[0-9]+|_+$', new_prefix)
                        if m:
                            new_prefix = new_prefix[:m.start()]
                    else:
                        self.logger.debug("[guess]: Using prefix from latest")
                        # Try to use the latest_release prefix
                        head = self.guess_latest_release()
                        new_prefix = head[1]

            # At this point, new_prefix can still be None

            if not new_suffix:
                self.logger.debug("[guess]: Guessing new suffix")
                self.logger.debug("[guess]: find latest release")
                # Guess the latest release
                head = self.guess_latest_release()
                if head[3]:
                    self.logger.debug("[guess]: Got suffix from latest")
                    prev_ver = head[3]

                    # Bump the previous release version
                    self.logger.debug("[guess]: Bumping release")
                    new_ver = bump_version(prev_ver, abi_break)
                    new_suffix = "".join(("_" + str(i) for i in new_ver if i is
                                          not None))

        if not new_prefix or not new_suffix:
            # ERROR: could not guess the name
            msg = "Insufficient information to guess the new release"\
                  " name. Releases found do not have version"\
                  " information or a valid library name. Please"\
                  " provide the complete name of the release."
            self.logger.error(msg)
            raise Exception(msg)

        # Return the combination of the prefix and version
        return new_prefix.upper() + new_suffix

    def sort_releases_nice(self, top_release):
        """
        Sort the releases contained in a map file putting the dependencies of
        ``top_release`` first. This changes the order of the list in
        ``releases``.

        :param top_release: The release whose dependencies should be prioritized
        """

        if not self.init:
            msg = "Map not checked, run check()"
            self.logger.error(msg)
            raise Exception(msg)

        self.releases.sort(key=lambda release: release.name)
        dependencies = self.dependencies()
        top_dependency = next((dependency for dependency in dependencies if
                               dependency[0] == top_release))

        new_list = []
        index = 0

        while self.releases:
            release = self.releases.pop()
            if release.name in top_dependency:
                new_list.insert(index, release)
                index += 1
            else:
                new_list.append(release)

        self.releases = new_list


class Release(object):
    """
    A internal representation of a release version and its symbols

    A release is usually identified by the library name (suffix) and the release
    version (suffix). A release contains symbols, grouped by their visibility
    scope (global or local).

    In this class the symbols of a release are stored in a list of dictionaries
    mapping a visibility scope name (e.g. \"global\") to a list of the contained
    symbols:
    ::

        ([{"global": [symbols]}, {"local": [local_symbols]}])

    Attributes:
        name: The release name
        previous: The previous release to which this release is dependent
        symbols: The symbols contained in the release, grouped by the visibility
                 scope.
    """

    def __init__(self):
        self.name = ''
        self.previous = ''
        self.released = False
        self.symbols = dict()

    def __str__(self):
        released = ""
        vs = []
        visibilities = sorted(self.symbols.keys())
        if self.released:
            released = "    # Released"
        for v in visibilities:
            symbols = sorted(self.symbols[v])
            vs.extend([" " * 4, v, ":\n",
                       "".join((" " * 8 + symbol + ";\n"
                                for symbol in symbols))])
        content = "".join(chain(self.name, released, "\n",
                                "{\n", vs, "} ",
                                self.previous, ";\n"))
        return content

    def duplicates(self):
        duplicates = []
        for scope, symbols in (self.symbols.items()):
            seen = set()
            release_dups = set()
            if symbols:
                for symbol in symbols:
                    if symbol not in seen:
                        seen.add(symbol)
                    else:
                        release_dups.add(symbol)
                if release_dups:
                    duplicates.append((scope, list(release_dups)))
        return duplicates


###############################################################################
# Utility functions
###############################################################################

def get_version_from_string(version_string):
    """
    Get the version numbers from a string

    :param version_string: A string composed by numbers separated by non \
                           alphanumeric characters (e.g. 0_1_2 or 0.1.2)
    :returns: A list of the numbers in the string
    """

    # Get logger
    logger = Single_Logger.getLogger(__name__)

    m = re.findall(r'[0-9]+', version_string)

    if m:
        if len(m) < 2:
            logger.warn("Provide at least a major and a minor"
                        " version digit (eg. '1.2.3' or '1_2')")
        if len(m) > 3:
            logger.warn("Version has too many parts; provide 3 or less"
                        " ( e.g. '0.1.2')")
    else:
        msg = "Could not get version parts. Provide digits separated"\
              " by non-alphanumeric characters. (e.g. 0_1_2 or 0.1.2)"
        logger.error(msg)
        raise Exception(msg)

    version = [int(i) for i in m]

    return version


def get_info_from_release_string(release):
    """
    Get the information from a release name

    The given string is split in a prefix (usually the name of the lib) and a
    suffix (the version part, e.g. '_1_4_7'). A list with the version info
    converted to ints is also contained in the returned list.

    :param release: A string in format 'LIBX_1_0_0' or similar
    :returns: A list in format [release, prefix, suffix, [CUR, AGE, REV]]
    """

    # Get logger
    logger = Single_Logger.getLogger(__name__)

    version = [None, None, None]
    ver_suffix = None
    prefix = None
    tail = None

    if not release:
        logger.warn("No release provided")
        return None

    # Remove eventual white spaces
    release = release.lstrip()

    # Search for the first ocurrence of a version like sequence
    m = re.search(r'_+[0-9]+', release)
    if m:
        # If found, remove the version like sequence to get the prefix
        prefix = release[:m.start()]
        tail = release[m.start():]
    else:
        # Check if the prefix contain at least a letter
        m = re.findall(r'[a-zA-Z]+', release)
        if m:
            prefix = release
        else:
            # If not, reject the prefix
            logger.warn("Release provided is not well formed"
                        " (a well formed release contain the library"
                        " identifier and the version information)."
                        " Suggested: something like LIBNAME_1_2_3")
            return None

    if tail:
        # Search and get the version information
        version = get_version_from_string(tail)
        ver_suffix = "".join(["_" + str(i) for i in version if i is not None])

    if prefix:
        # The prefix can have trailing '_'
        prefix = prefix.rstrip("_")

    # Return the information got
    return [release, prefix, ver_suffix, version]


# TODO: Make bump strategy customizable
def bump_version(version, abi_break):
    """
    Bump a version depending if the ABI was broken or not

    If the ABI was broken, CUR is bumped; AGE and REV are set to zero.
    Otherwise, CUR is kept, AGE is bumped, and REV is set to zero.
    This also works with versions without the REV component (e.g. [1, 4, None])

    :param version:     A list in format [CUR, AGE, REV]
    :param abi_break:   A boolean indication if the ABI was broken
    :returns:           A list in format [CUR, AGE, REV]
    """

    new_version = []
    if abi_break:
        if version[0] is not None:
            new_version.append(version[0] + 1)
        new_version.extend([0] * len(version[1:]))
    else:
        if version[0] is not None:
            new_version.append(version[0])
        if version[1] is not None:
            new_version.append(version[1] + 1)
        new_version.extend([0] * len(version[2:]))
    return new_version


def clean_symbols(symbols):
    """
    Receives a list of lines read from the input and returns a list of words

    :param symbols: A list of lines containing symbols
    :returns:       A list of the obtained symbols
    """

    # Get logger
    logger = Single_Logger.getLogger(__name__)

    # Split the lines into potential symbols and remove invalid characters
    clean = []
    if symbols:
        no_invalid = chain(*(re.split(r'\W+', i) for i in symbols))
        clean.extend((i for i in no_invalid if i))

    # Report duplicated symbols
    if clean:
        previous = None
        duplicates = set()
        for i in clean:
            if not previous:
                previous = i
            else:
                if previous == i:
                    duplicates.add(previous)
                previous = i
        if duplicates:
            dup_list = "".join((" " * 4 + dup + "\n" for dup in
                                sorted(duplicates)))
            logger.warn("Duplicated symbols provided:\n%s", dup_list)

    return clean


def check_files(out_arg, out_name, in_arg, in_name, dry):
    """
    Check if output and input are the same file. Create a backup if so.

    :param out_arg:  The name of the option used to receive output file name
    :param out_name: The received string as output file path
    :param in_arg:   The name of the option used to receive input file name
    :param in_name:  The received string as input file path
    """

    # Get logger
    logger = Single_Logger.getLogger(__name__)

    # Check if the first file exists
    if os.path.isfile(out_name):
        # Check if given input file is the same as output
        if os.path.isfile(in_name):
            if os.path.samefile(out_name, in_name):
                logger.warn("Given paths in \'%s\' and \'%s\' are the same.",
                            str(out_arg), str(in_arg))

                # Avoid changing the files if this is a dry run
                if dry:
                    return

                logger.warn("Moving \'%s\' to \'%s.old\'.", str(in_name),
                            str(in_name))
                try:
                    # If it is the case, copy to another file to
                    # preserve the content
                    shutil.copy2(str(in_name), str(in_name) + ".old")
                except Exception as e:
                    logger.error("Could no copy \'%s\' to \'%s.old\'."
                                 " Aborting.", str(in_name), str(in_name))
                    raise e


def get_info_from_args(args):
    """
    Get the release information from the provided arguments

    It is possible to set the new release name to be used through the command
    line arguments.

    :param args: Arguments given in command line parsed by argparse
    """

    # Get logger
    logger = Single_Logger.getLogger(__name__)

    release_info = None
    if args.release:
        # Parse the release name string to get info
        release_info = get_info_from_release_string(args.release)

        if args.name:
            m = re.search(r'\w+', args.name)
            if m:
                release_info[1] = m.group()
        if args.version:
            version = get_version_from_string(args.version)
            new_suffix = "".join(("_" + str(i) for i in version))
            release_info[2] = new_suffix
            release_info[3] = version

        if release_info:
            if release_info[1] and release_info[2]:
                release_info[0] = release_info[1] + release_info[2]
    elif args.name and args.version:
        # Parse the given version string to get the version information
        version = get_version_from_string(args.version)
        # Create a release string
        rel_string = "_".join([args.name] + [str(i) for i in version])
        # Parse the release string
        release_info = get_info_from_release_string(rel_string)
    else:
        if not args.guess or args.func == new:
            msg = "It is necessary to provide either release name or"\
                  " name and version"
            logger.error(msg)
            raise Exception(msg)

    return release_info


###############################################################################
# INTERFACE
###############################################################################

def update(args):
    """
    Given the new list of symbols, update the map

    The new map will be generated by the following rules:
        - If new symbols are added, a new release is created containing the new
          symbols. This is a compatible update.
        - If a previous existing symbol is removed, then all releases are
          unified in a new release. This is an incompatible change, the SONAME
          of the library should be bumped

    The symbols provided are considered all the exported symbols in the
    new version. Such set of symbols is compared to the previous existing
    symbols. If symbols are added, but nothing removed, it is a compatible
    change. Otherwise, it is an incompatible change and the SONAME of the
    library should be bumped.

    If --add is provided, the symbols provided are considered new symbols to be
    added. This is a compatible change.

    If --remove is provided, the symbols provided are considered the symbols to
    be removed. This is an incompatible change and the SONAME of the library
    should be bumped.

    :param args: Arguments given in command line parsed by argparse
    """

    # Get logger
    logger = Single_Logger.getLogger(__name__, filename=args.logfile)

    logger.info("Command: update")
    logger.debug("Arguments provided: ")
    logger.debug(str(args))

    # Set the verbosity if provided
    if args.verbosity:
        logger.setLevel(VERBOSITY_MAP[args.verbosity])

    # If output would be overwritten, print a warning
    if args.out:
        if os.path.isfile(args.out):
            logger.warn("Overwriting existing file \'%s\'", args.out)

    # If both output and input files were given, check if are the same
    if args.out and args.input:
        check_files('--out', args.out, '--in', args.input, args.dry)

    # If output is given, check with the file to be updated
    if args.out and args.file:
        check_files('--out', args.out, 'file', args.file, args.dry)

    # Get the release information provided in the arguments
    release_info = get_info_from_args(args)

    # Read the current map file
    cur_map = Map(filename=args.file, logger=logger)

    # Get all global symbols (it is a set)
    all_symbols = cur_map.all_global_symbols()

    # Generate the list of the new symbols
    new_symbols = []
    lines = None
    if args.input:
        with open(args.input, "r") as symbols_fp:
            lines = symbols_fp.readlines()
    else:
        # Read from stdin
        lines = sys.stdin.readlines()

    for line in lines:
        new_symbols.extend(line.split())

    # Clean the input removing invalid symbols
    new_symbols = clean_symbols(new_symbols)

    # All symbols read
    new_set = set(new_symbols)

    added_set = set()
    removed_set = set()

    # If the list of symbols are being added
    if args.add:
        # Check the symbols and print a warning if already present
        for symbol in new_set:
            if symbol in all_symbols:
                logger.warn("The symbol \'%s\' is already"
                            " present in a previous version. Keep the"
                            " previous implementation to not break ABI.",
                            symbol)

        added_set.update(new_set)
    # If the list of symbols are being removed
    elif args.remove:
        # Remove the symbols to be removed
        for symbol in new_set:
            if symbol in all_symbols:
                removed_set.add(symbol)
            else:
                logger.warn("Requested to remove \'%s\', but not found.",
                            symbol)
    # If the list of all symbols are being compared (the default option)
    else:
        for symbol in new_set:
            if symbol not in all_symbols:
                added_set.add(symbol)

        for symbol in all_symbols:
            if symbol not in new_set:
                removed_set.add(symbol)

    # Make lists from the sets
    added = list(added_set)
    removed = list(removed_set)

    # Print the modifications
    if added:
        added.sort()
        msg = "".join(chain("Added:\n",
                            ("    " + symbol + "\n" for symbol in added)))
        print(msg)

    if removed:
        removed.sort()
        msg = "".join(chain("Removed:\n",
                            ("    " + symbol + "\n" for symbol in removed)))
        print(msg)

    # Guess the latest release
    latest = cur_map.guess_latest_release()

    if not added and not removed:
        print("No symbols added or removed. Nothing done.")
        return

    r = None

    if added:
        if release_info:
            for to_up in (rs for rs in cur_map.releases if rs and rs.name ==
                          release_info[0]):
                # If the release to be modified is released
                if to_up.released:
                    msg = "Released releases cannot be modified. Abort."
                    logger.error(msg)
                    raise Exception(msg)

                r = to_up
        else:
            r = Release()
            # Guess the name for the new release
            r.name = cur_map.guess_name(release_info, guess=args.guess)
            r.name.upper()
            r.symbols['global'] = []

            if not removed:
                # Add the name for the previous release
                r.previous = latest[0]

                # Put the release on the map
                cur_map.releases.append(r)

        # If this is the final change to the release, mark as released
        if args.final:
            r.released = True

        # Add the symbols added to global scope
        r.symbols['global'].extend(added)
    if removed:
        if not args.allow_abi_break:
            msg = "ABI break detected: symbols would be removed"
            logger.error(msg)
            raise Exception(msg)

        logger.warn("ABI break detected: symbols were removed.")
        print("Merging all symbols in a single new release")
        new_map = Map()
        r = Release()

        # Guess the name of the new release
        r.name = cur_map.guess_name(release_info, abi_break=True,
                                    guess=args.guess)
        r.name.upper()

        # Add the symbols added to global scope
        all_symbols.update(added_set)

        # Remove the '*' wildcard, if present
        if '*' in all_symbols:
            logger.warn("Wildcard \'*\' found in global. Removed to avoid"
                        " exporting unexpected symbols.")
            all_symbols.remove('*')

        # Remove the symbols to be removed and convert to a list
        all_symbols_list = [symbol for symbol in all_symbols if
                            symbol not in removed_set]

        # Update the global symbols
        r.symbols.update({'global': all_symbols_list})

        # Add the wildcard to the local symbols
        r.symbols.update({'local': ['*']})

        # If this is the final change to the release, mark as released
        if args.final:
            r.released = True

        # Put the release on the map
        new_map.releases.append(r)

        # Substitute the map
        cur_map = new_map

    # Do a structural check
    cur_map.check()

    # Sort the releases putting the new release and dependencies first
    cur_map.sort_releases_nice(r.name)

    if args.dry:
        print("This is a dry run, the files were not modified.")
        return

    try:
        if args.out:
            f = open(args.out, "w")
        else:
            f = sys.stdout
        f.write("# This map file was updated with"
                " smap-{0}\n\n".format(__version__))
        f.write(str(cur_map))
    finally:
        if args.out:
            f.close()


def new(args):
    """
    \'new\' subcommand

    Create a new version script file containing the provided symbols.

    :param args: Arguments given in command line parsed by argparse
    """

    # Get logger
    logger = Single_Logger.getLogger(__name__, filename=args.logfile)

    logger.info("Command: new")
    logger.debug("Arguments provided: ")
    logger.debug(str(args))

    # Set the verbosity if provided
    if args.verbosity:
        logger.setLevel(VERBOSITY_MAP[args.verbosity])

    # If output would be overwritten, print a warning
    if args.out:
        if os.path.isfile(args.out):
            logger.warn("Overwriting existing file \'%s\'.", args.out)

    # If both output and input files were given, check if are the same
    if args.out and args.input:
        check_files('--out', args.out, '--in', args.input, args.dry)

    # Get the release information provided in the arguments
    release_info = get_info_from_args(args)

    # In the new command, there is no way to guess the name, since there are
    # not previous information. So the exception have to be raised early to
    # avoid collecting the new symbols and then find out we do not have a name
    if not release_info:
        msg = "Please provide the release name."
        logger.error(msg)
        raise Exception(msg)

    logger.debug("Release info in args:")
    logger.debug(str(release_info))

    # Generate the list of the new symbols
    new_symbols = []
    lines = None
    if args.input:
        with open(args.input, "r") as symbols_fp:
            lines = symbols_fp.readlines()
    else:
        # Read from stdin
        lines = sys.stdin.readlines()

    for line in lines:
        new_symbols.extend(line.split())

    # Clean the input removing invalid symbols
    new_symbols = clean_symbols(new_symbols)

    new_symbols_set = set(new_symbols)

    if new_symbols:
        new_map = Map()
        r = Release()

        name = new_map.guess_name(release_info)

        debug_msg = "Generated name: \'{}\'".format(name)
        logger.debug(debug_msg)

        # Set the name of the new release
        r.name = name.upper()

        # Add the symbols to global scope
        r.symbols['global'] = list(new_symbols_set)

        # Add the wildcard to the local symbols
        r.symbols['local'] = ['*']

        if args.final:
            r.released = True

        # Put the release on the map
        new_map.releases.append(r)

        # Do a structural check
        new_map.check()

        # Sort the releases putting the new release and dependencies first
        new_map.sort_releases_nice(r.name)

        if args.dry:
            print("This is a dry run, the files were not modified.")
            return

        try:
            if args.out:
                f = open(args.out, "w")
            else:
                f = sys.stdout
            f.write("# This map file was created with"
                    " smap-{0}\n\n".format(__version__))
            f.write(str(new_map))
        finally:
            if args.out:
                f.close()
    else:
        logger.warn("No valid symbols provided. Nothing done.")


def check(args):
    """
    \'check\' subcommand

    Check the content of a symbol version script

    :param args: Arguments given in command line parsed by argparse
    """

    # Get logger
    logger = Single_Logger.getLogger(__name__, filename=args.logfile)

    logger.info("Command: check")
    logger.debug("Arguments provided: ")
    logger.debug(str(args))

    # Set the verbosity if provided
    if args.verbosity:
        logger.setLevel(VERBOSITY_MAP[args.verbosity])

    # Read the map file
    smap = Map(filename=args.file, logger=logger)

    # Check the map file
    smap.check()


def version(args):
    """
    \'version\' subcommand

    Prints and returns the program name and version.

    :param args: Arguments given in command line parsed by argparse
    :returns: A string containing the program name and version
    """

    name_version = "smap-" + __version__

    print(name_version)

    return name_version


def get_arg_parser():
    """
    Get a parser for the command line arguments

    The parser is capable of checking requirements for the arguments and
    possible incompatible arguments.

    :returns: A parser for command line arguments. (argparse.ArgumentParser)
    """
    # Common file arguments
    file_args = argparse.ArgumentParser(add_help=False)
    file_args.add_argument('-o', '--out',
                           help='Output file (defaults to stdout)')
    file_args.add_argument('-i', '--in',
                           help='Read from this file instead of stdio',
                           dest='input')
    file_args.add_argument('-d', '--dry',
                           help='Do everything, but do not modify the files',
                           action='store_true')

    # Common verbosity arguments
    verb_args = argparse.ArgumentParser(add_help=False)
    group_verb = verb_args.add_mutually_exclusive_group()
    group_verb.add_argument('--verbosity', help='Set the program verbosity',
                            choices=['quiet', 'error', 'warning', 'info',
                                     'debug'],
                            default='warning')
    group_verb.add_argument('--quiet', help='Makes the program quiet',
                            dest='verbosity', action='store_const',
                            const='quiet')
    group_verb.add_argument('--debug', help='Makes the program print debug info',
                            dest='verbosity', action='store_const', const='debug')
    verb_args.add_argument('-l', '--logfile',
                           help='Log to this file')

    # Common release name arguments
    name_args = argparse.ArgumentParser(add_help=False)
    name_args.add_argument("-n", "--name",
                           help="The name of the library (e.g. libx)")
    name_args.add_argument("-v", "--version",
                           help="The release version (e.g. 1_0_0 or 1.0.0)")
    name_args.add_argument("-r", "--release",
                           help="The full name of the release to be used"
                           " (e.g. LIBX_1_0_0)")
    name_args.add_argument("--no_guess",
                           help="Disable next release name guessing",
                           action="store_false", dest="guess")

    # Main arguments parser
    parser = argparse.ArgumentParser(description="Helper tools for linker"
                                     " version script maintenance",
                                     epilog="Call a subcommand passing \'-h\'"
                                     " to see its specific options")

    # Subcommands parser
    subparsers = parser.add_subparsers(title="Subcommands",
                                       help="These subcommands have their own"
                                       " set of options", dest="subcommand")
    subparsers.required = True

    # Update subcommand parser
    parser_up = subparsers.add_parser("update", help="Update the map file",
                                      parents=[file_args, verb_args,
                                               name_args],
                                      epilog="A list of symbols is expected as"
                                      " the input.\nIf a file is provided with"
                                      " \'-i\', the symbols are read"
                                      " from the given file. Otherwise the"
                                      " symbols are read from stdin.")
    parser_up.add_argument("--allow-abi-break",
                           help="Allow removing symbols, and to break ABI",
                           action='store_true')
    parser_up.add_argument("-f", "--final",
                           help="Mark the modified release as final,"
                           " preventing later changes.",
                           action='store_true')
    group = parser_up.add_mutually_exclusive_group()
    group.add_argument("-a", "--add", help="Adds the symbols to the map file.",
                       action='store_true')
    group.add_argument("--remove", help="Remove the symbols from the map"
                       " file. This breaks the ABI.", action="store_true")
    parser_up.add_argument('file', help='The map file being updated')
    parser_up.set_defaults(func=update)

    # New subcommand parser
    parser_new = subparsers.add_parser("new",
                                       help="Create a new map file",
                                       parents=[file_args, verb_args,
                                                name_args],
                                       epilog="A list of symbols is expected"
                                       " as the input.\nIf a file is provided"
                                       " with \'-i\', the symbols are read"
                                       " from the given file. Otherwise the"
                                       " symbols are read from stdin.")
    parser_new.add_argument("-f", "--final",
                            help="Mark the new release as final,"
                                 " preventing later changes.",
                            action='store_true')
    parser_new.set_defaults(func=new)

    # Check subcommand parser
    parser_check = subparsers.add_parser("check", help="Check the map file",
                                         parents=[verb_args])
    parser_check.add_argument("file", help="The map file to be checked")
    parser_check.set_defaults(func=check)

    # Version subcommand parser
    parser_version = subparsers.add_parser("version", help="Print version")
    parser_version.set_defaults(func=version)

    return parser


# User interface
if __name__ == "__main__":

    class C(object):
        """
        Empty class used as a namespace
        """
        pass

    ns = C()

    # Get the arguments parser
    parser = get_arg_parser()

    # Parse arguments
    args = parser.parse_args(namespace=ns)

    # Run command
    ns.func(args)
