#!/usr/bin/env python
from __future__ import print_function
import sys
import re

import argparse

# Errors severity/verbosity
QUIET = 0
ERROR = 1
WARNING = 2
INFO = 3
DEBUG = 4

SEVERITY_MSG = {1 : '[ERROR] ',
                2 : '[WARNING] ',
                3 : '[INFO] ',
                4 : '[DEBUG] '}

VERBOSITY_MAP = {'quiet'    : QUIET,
                 'error'    : ERROR,
                 'warning'  : WARNING,
                 'info'     : INFO,
                 'debug'    : DEBUG}

# Set global verbosity default
global_verbosity = WARNING

# Global functions

# Information printer helpers
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def print_msg(message):
    if global_verbosity > QUIET:
        print(message)

def print_info(message):
    if global_verbosity >= INFO:
        eprint(SEVERITY_MSG[INFO] + message)

def print_warning(message):
    if global_verbosity >= WARNING:
        eprint(SEVERITY_MSG[WARNING] + message)

def print_error(message):
    if global_verbosity >= ERROR:
        eprint(SEVERITY_MSG[ERROR] + message)

def print_debug(message):
    if global_verbosity >= DEBUG:
        eprint(SEVERITY_MSG[DEBUG] + message)

def get_version_from_string(version_string):
    m = re.findall(r'[a-zA-Z0-9]+', version_string)

    if m:
        if len(m) < 2:
            print_warning("Provide at least a major and a minor version digit"
            " (eg. '1.2.3' or '1_2')")
        if len(m) > 3:
            print_warning("Version has too many parts; provide 3 or less"
            "( e.g. '0.1.2')")
    else:
        print_error("Could not get version parts. Provide digits separated by"
        " non-alphanumeric characters. (e.g. 0_1_2 or 0.1.2)")

    version = []
    for i in m:
        version.append(int(i))

    return version

def get_info_from_release_string(release):
    """
    Get the information from a release name

    The given string is split in a prefix (usually the name of the lib) and a
    suffix (the version part, e.g. '_1_4_7'). A list with the version info
    converted to ints is also contained in the returned list.
    The 

    :param release: A string in format 'LIBX_1_0_0' or similar
    :returns: A list in format [release, prefix, suffix, [CUR, AGE, REV]]
    """
    version = [None, None, None]
    ver_suffix = ''
    prefix = ''
    tail = ''

    # Search for the first ocurrence of a version like sequence
    m = re.search(r'_+[0-9]+', release)
    if m:
        # If found, remove the version like sequence to get the prefix
        prefix = release[:m.start()]
        tail = release[m.start():]
    else:
        # The release does not have version info, but can have trailing '_'
        m = re.search(r'_+$', release)
        if m:
            # If so, remove the trailing '_'
            prefix = release[:m.start()]
        else:
            # Otherwise the prefix is the whole release name
            prefix = release

    if tail:
        # Search and get the version information
        #m = re.search(r'_([0-9]+)_*([0-9]*)_*([0-9]*)$', release)
        version = get_version_from_string(tail)
        if version:
            for i in version:
                ver_suffix += "_%d" %(i)

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
        if (version[0] != None):
            new_version.append(version[0] + 1)
        if len(version) > 1:
            for i in version[1:]:
                new_version.append(0)
    else:
        if (version[0] != None):
            new_version.append(version[0])
        if (version[1] != None):
            new_version.append(version[1] + 1)
        if len(version) > 2:
            for i in version[2:]:
                new_version.append(0)
    return new_version

def clean_symbols(symbols):
    """
    Receives a list of lines read from the input and returns a list of words

    :param symbols: A list of lines containing symbols
    :returns:       A list of the obtained symbols
    """

    # Split the lines into potential symbols and remove invalid characters
    clean = []
    while symbols:
        line = symbols.pop()
        parts = re.split(r'\W+', line)
        if parts:
            for symbol in parts:
                m = re.match(r'\w+', symbol)
                if m:
                    clean.append(m.group())

    return clean

# Error classes

class ParserError(Exception):
    """
    Exception type raised by the map parser
    """

    def __str__(self):
        content = ''
        content += SEVERITY_MSG[self.severity]
        content += 'in line %d, ' %(self.line + 1)
        content += 'column %d: ' %(self.column)
        content += "%s\n" %(self.message)
        content += self.context
        content += " " * (self.column - 1)
        content += '^'
        return content

    def __init__(self, context, line, column, message, severity=ERROR):
        """
        The constructor

        :param context:     The line where the error was detected
        :param line:        The index of the line where the error was detected
        :param column:      The index of the column where the error was detected
        :param message:     The error message
        :param severity:    Can be INFO, WARNING, ERROR, or DEBUG
        """
        self.context = context
        self.line = line
        self.column = column
        self.message = message
        self.severity = severity

class DependencyError(Exception):
    """
    Exception type raised by dependency checker
    """

    def __str__(self):
        content = ''
        content += '%s: ' %(SEVERITY_MSG[self.severity])
        content += self.message
        return content

    def __init__(self, message, severity = ERROR):
        self.message = message
        self.severity = severity

# Map class

class Map:
    """
    A linker map
    """

    def parse(self, lines):
        # The parser FSM state. Can be:
        # 0: name:             searching for release name or 'EOF'
        # 1: opening:          searching for opening '{'
        # 2: element:           searching for visibility/symbol name or '}' closer
        # 3: element_closer:    searching for ':' or ';'
        # 4: previous:         searching for previous release name (can be empty)
        # 5: previous_closer:  searching for ';'
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
                    if m != None:
                        column += m.end()
                        last = (index, column)
                        continue
                    # Searching for a release name
                    if state == 0:
                        print_debug(">>Name")
                        m = re.match(r'\w+', line[column:])
                        if m == None:
                            raise ParserError(lines[last[0]], last[0],
                                last[1], "Invalid Release identifier")
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
                            state += 1
                            if has_duplicate:
                                raise ParserError(lines[index], index,
                                column, "Duplicated Release identifier \'%s\'"
                                %(name), severity = WARNING)
                            continue
                    # Searching for the '{'
                    elif state == 1:
                        print_debug(">>Opening")
                        m = re.match(r'\{', line[column:])
                        if m == None:
                            raise ParserError(lines[last[0]], last[0], last[1],
                                "Missing \'{\'")
                        else:
                            column += m.end()
                            v = None
                            last = (index, column)
                            state += 1
                            continue
                    elif state == 2:
                        print_debug(">>Element")
                        m = re.match(r'\}', line[column:])
                        if m != None:
                            print_debug(">>Release closer, jump to Previous")
                            column += m.end()
                            last = (index, column)
                            state = 4
                            continue
                        m = re.match(r'\w+|\*', line[column:])
                        if m == None:
                            raise ParserError(lines[last[0]], last[0], last[1],
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
                        print_debug(">>Element closer")
                        m = re.match(r';', line[column:])
                        if m == None:
                            # It was not Symbol. Maybe a new visibility.
                            m = re.match(r':', line[column:])
                            if m == None:
                                # In this case the current position is used
                                raise ParserError(lines[index],
                                index, column, "Missing \';\' or \':\'"
                                " after \'%s\'" %(identifier))
                            else:
                                # New visibility found
                                v = (identifier, [])
                                r.symbols.append(v)
                                column += m.end()
                                last = (index, column)
                                state = 2
                                continue
                        else:
                            if v == None:
                                # There was no open visibility scope
                                v = ('global', [])
                                r.symbols.append(v)
                                raise ParserError(lines[last[0]],
                                    last[0], last[1], "Missing visibility"
                                    " scope before \'%s\'." 
                                    " Symbols considered in \'global:\'"
                                    %(identifier),
                                    severity = WARNING)
                            else:
                                # Symbol found
                                v[1].append(identifier)
                                column += m.end()
                                last = (index, column)
                                # Move back the state to find elements
                                state = 2
                                continue
                    elif state == 4:
                        print_debug(">>Previous")
                        m = re.match(r'^;', line[column:])
                        if m != None:
                            print_debug(">>Empty previous")
                            column += m.end()
                            last = (index, column)
                            # Move back the state to find other releases
                            state = 0
                            continue
                        m = re.match(r'\w+', line[column:])
                        if m == None:
                            raise ParserError(lines[last[0]], last[0], last[1], "Invalid"
                                " identifier")
                        else:
                            # Found previous release identifier
                            column += m.end()
                            identifier = m.group(0)
                            last = (index, column)
                            state += 1
                            continue
                    elif state == 5:
                        print_debug(">>Previous closer")
                        m = re.match(r'^;', line[column:])
                        if m == None:
                            raise ParserError(lines[last[0]], last[0], last[1],
                                "Missing \';\'")
                        else:
                            # Found previous closer
                            column += m.end()
                            r.previous = identifier
                            last = (index, column)
                            # Move back the state to find other releases
                            state = 0
                            continue
                    else:
                        # Should never reach this
                        raise ParserError(lines[last[0]], last[0], last[1], "Unknown"
                            "parser state")
                except ParserError as e:
                    # If the exception was not an error, continue
                    if e.severity != ERROR:
                        print_msg(e)
                        pass
                    else:
                        raise e
                except:
                    raise
        # Store the parsed releases
        self.releases = releases

    def read(self, filename):
        """
        Read a linker map file (version script) and store the obtained releases

        :param filename:        The path to the file to be read
        :raises ParserError:    Raised when a syntax error is found in the file
        """

        try:
            with open(filename, "r") as f:
                self.filename = filename
                self.lines = f.readlines()
                try:
                    self.parse(self.lines)
                    self.init = True
                except ParserError as e:
                    raise e
        except:
            raise

    def all_symbols(self):
        """
        Returns all symbols from all releases contained in the Map object

        :returns: A set containing all the symbols in all releases
        """

        symbols = []
        for release in self.releases:
            for scope, scope_symbols in release.symbols:
                symbols.extend(scope_symbols)
        return set(symbols)

    def all_global_symbols(self):
        """
        Returns all global symbols from all releases contained in the Map
        object

        :returns: A set containing all global symbols in all releases
        """

        symbols = []
        for release in self.releases:
            for scope, scope_symbols in release.symbols:
                if scope.lower() == 'global':
                    symbols.extend(scope_symbols)
        return set(symbols)

    def duplicates(self):
        """
        Find and return a list of duplicated symbols for each release

        If no duplicates are found, return an empty list

        :returns: A list of tuples in the form
        [(release, [(scope, [duplicates])])]
        """
        duplicates = []
        for release in self.releases:
            rel_dup = release.duplicates();
            if rel_dup:
                duplicates.append((release.name, rel_dup))
        return duplicates

    def contains(self, symbol):
        """
        Check if a symbol is contained in the map in any Release

        :param symbol:  The symbol to be searched
        :returns:       True if the symbol was found, False otherwise
        """
        for release in self.releases:
            if release.contains(symbol):
                return True
        return False

    def dependencies(self):
        """
        Construct the dependencies lists

        Contruct a list of dependency lists. Each dependency list contain the
        names of the releases in a dependency path.
        The heads of the dependencies lists are the releases not refered as a
        previous release in any release.

        :returns:   A list containing the dependencies lists
        """

        def get_dependency(releases, current):
            found = [release for release in releases if release.name == current]
            if not found:
                raise DependencyError("release \'%s\' not found" %(current))
            if len(found) > 1:
                raise DependencyError("defined more than 1 release "
                "\'%s\'" %(current))
            return found[0].previous

        solved = []
        deps = []
        for release in self.releases:
            if release.name in solved:
                continue
            else:
                current = [release.name]
                dep = release.previous
                while dep:
                    if dep in current:
                        msg = ''
                        msg += "Circular dependency detected!\n"
                        msg += "    "
                        for i in current:
                            msg += "%s->" %(i)
                        msg += "%s" %(dep)
                        raise DependencyError(msg)
                    current.append(dep)
                    # Squash dependencies
                    if dep in solved:
                        for i in deps:
                            if i[0] == dep:
                                deps.remove(i)
                    else:
                        solved.append(dep)
                    try:
                        dep = get_dependency(self.releases, dep)
                    except DependencyError:
                        raise
                solved.append(release.name)
                deps.append(current)
        return deps

    def check(self):
        """
        Check the map structure
        """

        have_wildcard = []
        seems_base = []

        # Find duplicated symbols
        d = self.duplicates()
        if d:
            for release, duplicates in d:
                message = 'Duplicates found in release %s:' %(release)
                print_warning(message)
                for scope, symbols in duplicates:
                    message = ' ' * 4 + scope + ':'
                    print_warning(message)
                    for symbol in symbols:
                        message = ' ' * 8 + symbol
                        print_warning(message)

        # Check '*' wildcard usage
        for release in self.releases:
            for scope, symbols in release.symbols:
                if scope == 'local':
                    if symbols:
                        if "*" in symbols:
                            message = "%s" %(release.name)
                            message += " contains the local \'*\' wildcard"
                            print_info(message)
                            if release.previous:
                                # Release contain predecessor version and local: *;
                                message = "%s" %(release.name)
                                message += " should not contain the local wildcard"
                                message += " because it is not the base version"
                                message += " (it refers to version"
                                message += " \'%s\' as its" %(release.previous)
                                message += " predecessor)"
                                print_warning(message)
                            else:
                                # Release seems to be base: empty predecessor
                                message = "%s" %(release.name)
                                message += " seems to be the base version"
                                print_info(message)
                                seems_base.append(release.name)

                            # Append to the list of releases which contain the
                            # wildcard '*'
                            have_wildcard.append((release.name, scope))
                elif scope == 'global':
                    if symbols:
                        if "*" in symbols:
                            # Release contains '*' wildcard in global scope
                            message = "%s contains the" %(release.name)
                            message += " \'*\' wildcard in global scope."
                            message += " It is probably exporting"
                            message += " symbols it should not."
                            print_warning(message)
                            have_wildcard.append((release.name, scope))
                else:
                    # Release contains unknown visibility scopes (not global or
                    # local)
                    message = "%s" %(release.name)
                    message += " contains unknown"
                    message += " scope named \'%s\'" %(scope)
                    message += " (different from \'global\' and \'local\')"
                    print_warning(message)

        if have_wildcard:
            if len(have_wildcard) > 1:
                # The '*' wildcard was found in more than one place
                message = "The \'*\' wildcard was found in more than"
                message += " one place:"
                print_warning(message)
                for name, scope in have_wildcard:
                    print_warning(" " * 4 + "%s: in \'%s\'" %(name, scope))
        else:
            print_warning("The \'*\' wildcard was not found")

        if seems_base:
            if len(seems_base) > 1:
                # There is more than one release without predecessor and
                # containing '*' wildcard in local scope
                message = "More than one release seems the base"
                " version (contains the local wildcard and does not have a"
                " predecessor version):"
                print_warning(message)
                for name in seems_base:
                    print_warning(" " * 4 + "%s" %(name))
        else:
            print_warning("No base version release found")

        try:
            dependencies = self.dependencies()
            print_info("Found dependencies: ")
            for release in dependencies:
                cur = '    '
                for dep in release:
                    cur += "%s->" %(dep)
                print_info(cur)
        except DependencyError as e:
            print_error(e)

    def guess_latest_release(self):
        """
        Try to guess the latest release

        :returns:   A list [release, prefix, suffix, version[CUR, AGE, REV]] 
        """
        if not self.init:
            print_error("Map not initialized, try to read a file first")
            return ''

        deps = self.dependencies()

        heads = (dep[0] for dep in deps)

        latest = [None, None, '_0_0_0', None]
        for release in heads:
            info = get_info_from_release_string(release)
            if info[2] > latest[2]:
                latest = info

        return latest


    def guess_name(self, abi_break = False, new_release = None, new_prefix =
    None, new_suffix = None, new_ver = None, prev_release = None, prev_prefix =
    None, prev_ver = None):
        """
        Use the given information to guess the name for the new release
        :param abi_break:   Boolean, indicates if the ABI was broken
        :param new_release: String, the name of the new release. If this is
        provided, the guessing is avoided and this will be used as the release
        name
        :param new_ver:     A list of int, the components of the version (e.g.
        [CURRENT, AGE, RELEASE]).
        :param libname:     String, the name of the library; will be used as the prefix
        for the name of the new release.
        :param prev_release:    The name of the previous release.
        :param prev_ver:    A list of int, the components of the previous
        version (e.g. [CURRENT, AGE, RELEASE])
        """

        # If the two required parts were given, just combine and return
        if new_prefix:
            if new_suffix:
                print_debug("[guess]: Two parts found, using them")
                return new_prefix.upper() + new_suffix
            elif new_ver:
                print_debug("[guess]: Prefix and version found, using them")
                new_suffix = ''
                for i in new_ver:
                    new_suffix += '_%d' %(i)
                return new_prefix.upper() + new_suffix

        # If the new release name was given (and could not be parsed), use it
        if new_release:
            print_debug("[guess]: New release found, using it")
            return new_release.upper()


        # The two parts necessary to make the release name
        # new_prefix
        # new_suffix

        # If the new prefix was not given:
        # - Try previous prefix, if given
        # - Try previous release name, if given
        #   - This will also set the version, if not set yet
        # - Try to find a common prefix between release names
        # - Try to find latest release

        # If the new suffix was not given:
        # - Try previous version, if given
        # - Try previous release name, if given
        #   - This will also set the prefix, if not set yet
        # - Try to find latest release version

        prev_info = None

        # If a previous release was given, extract info and check it
        if prev_release:
            print_debug("[guess]: Previous release found")
            prev_info = get_info_from_release_string(prev_release)
            # If the prefix was successfully extracted 
            if info[1]:
                # Use it as the new prefix, if none was given
                if not new_prefix:
                    new_prefix = info[1]

            # If the version was successfully extracted
            if info[3]:
                if not prev_ver:
                    prev_ver = info[3]

        if not new_prefix:
            if prev_prefix:
                print_debug("[guess]: Using previous prefix as the new")
                # Reuse the prefix from the previous release, if available
                new_prefix = prev_prefix
            else:
                print_debug("[guess]: Trying to find common prefix")
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
                        print_debug("[guess]: Common prefix found")
                        # Search and remove any version info found as prefix
                        m = re.search(r'_+[0-9]+|_+$', new_prefix)
                        if m:
                            new_prefix = new_prefix[:m.start()]
                    else:
                        print_debug("[guess]: Using prefix from latest")
                        # Try to use the latest_release prefix
                        head = self.guess_latest_release()
                        new_prefix = head[1]

        # At this point, new_prefix can still be None

        if not new_suffix:
            print_debug("[guess]: Guessing new suffix")

            # If the new version was given, make the suffix from it
            if new_ver:
                print_debug("[guess]: Using new version to make suffix")
                new_suffix = ''
                for i in new_ver:
                    new_suffix += "_%d" %(i)

            elif not prev_ver:
                print_debug("[guess]: Guessing latest release to make suffix")
                # Guess the latest release
                head = self.guess_latest_release()
                if head[3]:
                    print_debug("[guess]: Got suffix from latest")
                    prev_ver = head[3]

            if not new_suffix:
                if prev_ver:
                    print_debug("[guess]: Bumping release")
                    new_ver = bump_version(prev_ver, abi_break)
                    new_suffix = ''
                    for i in new_ver:
                        #if i:
                        new_suffix += "_%d" %(i)

        if not new_prefix or not new_suffix:
            # ERROR: could not guess the name
            raise Exception("Insufficient information to guess the new release"
            " name. Releases found do not have version information.")

        # Return the combination of the prefix and version
        return new_prefix.upper() + new_suffix

    def sort_releases_nice(self, top_release):
        """
        Sort the releases contained in a map file putting the dependencies of
        top_release first
        """

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

    # To make iterable
    def __next__(self):
        """
        Gets the next Release (for the iterator)
        """
        if self.index == len(self.releases):
            raise StopIteration
        self.index += 1
        return self.releases[self.index - 1]

    def __iter__(self):
        return self

    # To make printable
    def __str__(self):
        """
        Print the map in a usable form for the linker
        """
        content = ''
        for release in self.releases:
            content += release.__str__()
            content += "\n"
        return content

    # Constructor
    def __init__(self, verbosity=ERROR, filename=None):
        # The state
        self.init = False
        # For iterator
        self.index = 0
        self.releases = []
        # From the raw file
        self.filename = ''
        self.lines = []
        if (filename != None):
            try:
                self.read(filename)
            except ParserError as e:
                raise(e)

class Release:
    """
    A release version and its symbols
    """

    def contains(self, symbol):
        for scope, symbols in self.symbols:
            if symbol in symbols:
                return True
        return False

    #TODO should this search for duplicates between scopes?
    def duplicates(self):
        duplicates = []
        for scope, symbols in self.symbols:
            seen = []
            release_dups = []
            if symbols:
                for symbol in symbols:
                    if symbol not in seen:
                        seen.append(symbol)
                    else:
                        release_dups.append(symbol)
                if release_dups:
                    duplicates.append((scope, set(release_dups)))
        return duplicates

    def __next__(self):
        all_symbols = []
        for visibility, symbols in self.symbols:
            all_symbols.extend(symbols)
        if self.index >= len(all_symbols):
            raise StopIteration
        self.index += 1
        return all_symbols[self.index - 1]

    def __str__(self):
        content = ''
        content += self.name
        content += "\n{\n"
        for visibility, symbols in self.symbols:
            symbols.sort()
            content += "    "
            content += visibility
            content += ":\n"
            for symbol in symbols:
                content += "        "
                content += symbol
                content += ";\n"
        content += "} "
        content += self.previous
        content += ";\n"
        return content

    def __iter__(self):
        return self

    def __init__(self):
        self.name = ''
        self.previous = ''
        self.index = 0
        self.symbols = []

def check_files(out_arg, out_name, in_arg, in_name):
    # Check if the first file exists
    if os.path.isfile(out_name):
        # Check if given input file is the same as output
        if os.path.isfile(in_name):
            if os.path.samefile(out_name, in_name):
                msg = ''
                msg += "Given paths in \'%s\' and \'%s\'" %(out_arg, in_arg)
                msg += " are the same. Moving"
                msg += " \'%s\' to \'%s.old\'" %(in_name, in_name)
                print_warning(msg)
                try:
                    # If it is the case, copy to another file to
                    # preserve the content
                    shutil.copy2(in_name, in_name + ".old")
                except:
                    msg = ''
                    msg += "Could not copy"
                    msg += " \'%s\' to \'%s.old\'." %(in_name, in_name)
                    msg += " Aborting."
                    print_error(msg)
                    raise

                # Modify the name to point to the old file in case the original
                # was meant to be overwritten
                in_name = in_name + ".old"

#TODO
def compare(args):
    print_info("Command: compare")
    print_debug("Arguments provided: ")
    print_debug(args)

    old_map = Map(filename=args.old)
    new_map = Map(filename=args.new)

    #TODO: compare existing releases
    #TODO: compare set of symbols

def update(args):
    """
    Given the new list of symbols, update the map

    The new map will be generated by the following rules:
    - If new symbols are added, a new release is created containing the new
      symbols. This is a compatible update.
    - If a previous existing symbol is removed, then all releases are
      unified in a new release. This is an incompatible change, the SONAME
      of the library should be bumped
    """

    print_info("Command: update")
    print_debug("Arguments provided: ")
    print_debug(args.__str__())

    # If output would be overwritten, print a warning
    if args.out:
        print_warning("Overwriting existing file \'%s\'" %(args.out))

    # If both output and input files were given, check if are the same
    if args.out and args.input:
        check_files('--out', args.out, '--in', args.input)

    # If output is given, check with the file to be updated
    if args.out and args.file:
        check_files('--out', args.out, 'file', args.file)

    # Read the current map file
    cur_map = Map(filename=args.file)

    # Get all global symbols
    all_symbols = list(cur_map.all_global_symbols())

    # Generate the list of the new symbols
    new_symbols = []
    if args.input:
        with open(arsg.input, "r") as symbols_fp:
            lines = symbols_sp.readlines()
            for line in lines:
                new_symbols.extend(line.split())
    else:
        # Read from stdin
        lines = sys.stdin.readlines()
        for line in lines:
            new_symbols.extend(line.split())

    # Clean the input removing invalid symbols
    new_symbols = clean_symbols(new_symbols)

    # All symbols read
    new_set = set(new_symbols)

    added = []
    removed = []

    # If the list of all symbols are being compared
    if args.symbols:
        for symbol in new_set:
            if symbol not in all_symbols:
                added.append(symbol)

        for symbol in all_symbols:
            if symbol not in new_set:
                removed.append(symbol)
    # If the list of symbols are being added
    elif args.add:
        # Check the symbols and print a warning if already present
        for symbol in new_symbols:
            if symbol in all_symbols:
                msg = ''
                msg += "The symbol \'%s\' is already present in a" %(symbol)
                msg += " previous version."
                msg += " Keep the previous implementation to not break ABI."
                print_warning(msg)

        added.extend(new_symbols)
    # If the list of symbols are being removed
    elif args.delete:
        # Remove the symbols to be removed
        for symbol in new_symbols:
            if symbol in all_symbols:
                removed.append(symbol)
            else:
                msg = ''
                msg += "Requested to remove \'%s\'" %(symbol)
                msg += ", but not found."
                print_warning(msg)
    else:
        # Execution should never reach this point
        raise Exception("No strategy was provided (add/delete/symbols)")

    # Remove duplicates
    added = list(set(added))
    removed = list(set(removed))

    # Print the modifications
    if added:
        added.sort()
        msg = "Added:\n"
        for symbol in added:
            msg += "    %s\n" %(symbol)
        print_msg(msg)

    if removed:
        removed.sort()
        msg = "Removed:\n"
        for symbol in removed:
            msg += "    %s\n" %(symbol)
        print_msg(msg)

    # Guess the latest release
    latest = cur_map.guess_latest_release()

    if not added and not removed:
        print_msg("No symbols added or removed. Nothing done.")
        return

    if added:
        r = Release()
        # Guess the name for the new release
        r.name = cur_map.guess_name()
        r.name.upper()

        # Add the symbols added to global scope
        r.symbols.append(('global', added))

        # Add the name for the previous release
        r.previous = latest[0]

        # Put the release on the map
        cur_map.releases.append(r)

    if removed:
        if args.care:
            raise Exception("ABI break detected: symbols would be removed")

        print_warning("ABI break detected: symbols were removed.")
        print_msg("Merging all symbols in a single new release")
        new_map = Map()
        r = Release()

        # Guess the name of the new release
        r.name = cur_map.guess_name(abi_break=True)
        r.name.upper()

        # Add the symbols added to global scope
        all_symbols.extend(added)

        # Remove duplicates
        all_symbols = list(set(all_symbols))

        # Remove the symbols to be removed
        for symbol in removed:
            all_symbols.remove(symbol)

        # Remove the '*' wildcard, if present
        if '*' in all_symbols:
            print_warning("Wildcard \'*\' found in global. Removed to avoid"
            " exporting unexpected symbols.")
            all_symbols.remove('*')

        r.symbols.append(('global', all_symbols))

        # Add the wildcard to the local symbols
        r.symbols.append(('local', ['*']))

        # Put the release on the map
        new_map.releases.append(r)

        # Substitute the map
        cur_map = new_map

    # Do a structural check
    cur_map.check()

    # Sort the releases putting the new release and dependencies first
    cur_map.sort_releases_nice(r.name)

    # Write out to the output
    if args.out:
        with open(args.out, "w") as outfile:
            outfile.write("# This map file was automatically updated\n\n")
            outfile.write(cur_map.__str__())
    else:
        # Print to stdout
        sys.stdout.write("# This map file was automatically updated\n\n")
        sys.stdout.write(cur_map.__str__())

def new(args):
    print_info("Command: new")
    print_debug("Arguments provided: ")
    print_debug(args.__str__())

    print_debug("Files: out=\'%s\', in=\'%s\'" %(args.out, args.input))

    # If output would be overwritten, print a warning
    if args.out:
        print_warning("Overwriting existing file \'%s\'" %(args.out))

    # If both output and input files were given, check if are the same
    if args.out and args.input:
        check_files('--out', args.out, '--in', args.input)

    release_info = None
    if args.release:
        # Parse the release name string to get info
        release_info = get_info_from_release_string(args.release)
    elif args.name and args.version:
        # Parse the given version string to get the version information
        version = get_version_from_string(args.version)
        # Construct the release info list
        release_info = [None, args.name, None, version]
    else:
        print_error("It is necessary to provide either release name or name"
        " and version")
        raise Exception("Release name not provided")

    if not release_info:
        print_error("Could not retrieve release information.")

    print_debug("Release information:")
    print_debug(release_info.__str__())

    # Generate the list of the new symbols
    new_symbols = []
    if args.input:
        with open(args.input, "r") as symbols_fp:
            lines = symbols_sp.readlines()
            for line in lines:
                new_symbols.extend(line.split())
    else:
        # Read from stdin
        lines = sys.stdin.readlines()
        for line in lines:
            new_symbols.extend(line.split())

    # Clean the input removing invalid symbols
    new_symbols = clean_symbols(new_symbols)

    if new_symbols:
        new_map = Map()
        r = Release()

        name = new_map.guess_name(
        new_release = release_info[0],
        new_prefix = release_info[1],
        new_ver = release_info[3])

        print_debug("Generated name: \'%s\'" %(name))

        # Set the name of the new release
        r.name = name.upper()

        # Add the symbols to global scope
        r.symbols.append(('global', new_symbols))

        # Add the wildcard to the local symbols
        r.symbols.append(('local', ['*']))

        # Put the release on the map
        new_map.releases.append(r)

        # Do a structural check
        new_map.check()

        # Sort the releases putting the new release and dependencies first
        new_map.sort_releases_nice(r.name)

        # Write out to the output
        if args.out:
            with open(args.out, "w") as outfile:
                outfile.write("# This map file was created with"
                " symbol_version.py\n\n")
                outfile.write(new_map.__str__())
        else:
            # Print to stdout
            sys.stdout.write("# This map file was created with"
            " symbol_version.py\n\n")
            sys.stdout.write(new_map.__str__())
    else:
        print_warning("No valid symbols provided. Nothing done.")

# User interface
if __name__ == "__main__":
    # Used to check files
    import os
    # Used to preserve files
    import shutil

    # Common file arguments
    file_args = argparse.ArgumentParser(add_help = False)
    file_args.add_argument('-o', '--out',
    help='Output file (defaults to stdout)')
    file_args.add_argument('-i', '--in',
    help='Read from a file instead of stdio',
    dest='input')

    # Common verbosity arguments
    verb_args = argparse.ArgumentParser(add_help = False)
    group_verb = verb_args.add_mutually_exclusive_group()
    group_verb.add_argument('--verbosity', help='Set the program verbosity',
    choices=['quiet', 'error', 'warning', 'info', 'debug'], default='warning')
    group_verb.add_argument('--quiet', help='Makes the program quiet',
    dest='verbosity', action='store_const', const='quiet')
    group_verb.add_argument('--debug', help='Makes the program print debug info',
    dest='verbosity', action='store_const', const='debug')

    # Main arguments parser
    parser = argparse.ArgumentParser(description='Helper tools for linker version'
    ' script maintenance', epilog='Call a subcommand passing \'-h\' to see its'
    ' specific options')

    # Subcommands parser
    subparsers = parser.add_subparsers(title='Subcommands', description='Valid'
    ' subcommands:', help='These subcommands have their own set of options')

    # Compare subcommand parser
    parser_cmp = subparsers.add_parser('compare', help='Compare two map files')
    parser_cmp.add_argument('-n', '--new', help='The new map', required=True)
    parser_cmp.add_argument('-o', '--old', help='The old map', required=True)
    parser_cmp.set_defaults(func=compare)

    # Update subcommand parser
    parser_up = subparsers.add_parser('update', help='Update the map file',
    parents=[file_args, verb_args], epilog='A list of symbols is expected as'
    ' the input.\nIf a file is provided with \'-i\', the symbols are read'
    ' from the given file. Otherwise the symbols are read from stdin.')
    parser_up.add_argument('-c', '--care', help='Do not continue if the ABI would'
    ' break', action='store_true')
    group = parser_up.add_mutually_exclusive_group(required=True)
    group.add_argument('-a', '--add', help='Adds the symbols to the map file.',
    action='store_true')
    group.add_argument('-d', '--delete', help='Remove the symbols from the map'
    ' file. This breaks the ABI.', action='store_true')
    group.add_argument('-s', '--symbols', help='Compare the given symbol list with'
    ' the current map file and update accordingly. May break the ABI.',
    action='store_true')
    parser_up.add_argument('file', help='The map file being updated')
    parser_up.set_defaults(func=update)

    # New subcommand parser
    parser_new = subparsers.add_parser('new', help='Create a new map file',
    parents=[file_args, verb_args], epilog='A list of symbols is expected as'
    ' the input.\nIf a file is provided with \'-i\', the symbols are read'
    ' from the given file. Otherwise the symbols are read from stdin.')
    parser_new.add_argument('-n', '--name', help='The name of the library'
    ' (e.g. libx)')
    parser_new.add_argument('-v', '--version', help='The release version'
    ' (e.g. 1_0_0)')
    parser_new.add_argument('-r', '--release', help='The full name of the release'
    ' to be used (e.g. LIBX_1_0_0)')
    parser_new.set_defaults(func=new)

    # Parse arguments
    args = parser.parse_args()

    # Set program verbosity
    global_verbosity = VERBOSITY_MAP[args.verbosity]

    # Run command
    args.func(args)

