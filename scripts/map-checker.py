import sys
import re

def is_valid(l):
    # Blank line
    if re.fullmatch(r'\s*', l) != None:
        return False

    # Comment line
    if re.match(r'\s*#+', l) != None:
        return False

    # Valid string
    return True

class ParserError(Exception):
    """
    Exception type raised by the map parser
    """

    def __str__(self):
        content = ''
        content += "%s: in line %d, column %d: %s\n" %(
            self.severity, self.line + 1, self.column, self.message)
        content += e.context
        content += " " * (e.column - 1)
        content += '^'
        return content

    def __init__(self, context, line, column, message, severity='Error'):
        self.context = context
        self.line = line
        self.column = column
        self.message = message
        self.severity = severity

class Map:
    """
    A linker map
    """

    def read(self, filename):
        """
        Read a linker map file (version script) and store the obtained releases

        :param filename:        The path to the file to be read
        :raises ParserError:    Raised when a syntax error is found in the file
        """
        releases = []
        current = 0

        # The parser FSM state. Can be:
        # 0: name:             searching for release name or 'EOF'
        # 1: opening:          searching for opening '{'
        # 2: element:           searching for visibility/symbol name or '}' closer
        # 3: element_closer:    searching for ':' or ';'
        # 4: previous:         searching for previous release name (can be empty)
        # 5: previous_closer:  searching for ';'
        state = 0

        with open(filename, "r") as f:
            self.filename = filename
            self.lines = f.readlines()
            try:
                for index, line in enumerate(self.lines):
                    if is_valid(line):
                        column = 0
                        while column < len(line):
                            # Remove whitespaces from the beginning of the line
                            m = re.match(r'\s+', line[column:])
                            if m != None:
                                column += m.end()
                                continue
                            # Searching for a release name or 'EOF'
                            if state == 0:
                                if self.debug != 0:
                                    print(">>Name")
                                m = re.match(r'\w+', line[column:])
                                if m == None:
                                    raise ParserError(line, index, column,
                                        "Invalid Release identifier")
                                else:
                                    column += m.end()
                                    # New release found
                                    r = Release()
                                    r.name = m.group(0)
                                    releases.append(r)
                                    state += 1
                                    continue
                            # Searching for the '{'
                            elif state == 1:
                                if self.debug != 0:
                                    print(">>Opening")
                                m = re.match(r'\{', line[column:])
                                if m == None:
                                    raise ParserError(line, index, column,
                                        "Missing \'{\'")
                                else:
                                    column += m.end()
                                    state += 1
                                    v = None
                                    continue
                            elif state == 2:
                                if self.debug != 0:
                                    print(">>Element")
                                m = re.match(r'\}', line[column:])
                                if m != None:
                                    if self.debug != 0:
                                        print(">>Release closer, jump to Previous")
                                    column += m.end()
                                    state = 4
                                    continue
                                m = re.match(r'\w+|\*', line[column:])
                                if m == None:
                                    raise ParserError(line, index, column,
                                        "Invalid identifier")
                                else:
                                    column += m.end()
                                    identifier = m.group(0)
                                    state += 1
                                    continue
                            elif state == 3:
                                if self.debug != 0:
                                    print(">>Element closer")
                                m = re.match(r';', line[column:])
                                if m == None:
                                    # It was not Symbol. Maybe a new visibility.
                                    m = re.match(r':', line[column:])
                                    if m == None:
                                        raise ParserError(line, index, column,
                                            "Missing \';\' or \':\'")
                                    else:
                                        # New visibility found
                                        v = (identifier, [])
                                        r.symbols.append(v)
                                        column += m.end()
                                        state = 2
                                        continue
                                else:
                                    if v == None:
                                        # There was no open visibility scope
                                        raise ParserError(line, index, column,
                                            "Missing visibility scope (global,"
                                            " local)")
                                    else:
                                        # Symbol found
                                        v[1].append(identifier)
                                        column += m.end()
                                        # Move back the state to find elements
                                        state = 2
                                        continue
                            elif state == 4:
                                if self.debug != 0:
                                    print(">>Previous")
                                m = re.match(r';', line[column:])
                                if m != None:
                                    if self.debug != 0:
                                        print(">>Empty previous")
                                    column += m.end()
                                    # Move back the state to find other releases
                                    state = 0
                                    continue
                                m = re.match(r'\w+', line[column:])
                                if m == None:
                                    raise ParserError(line, index, column, "Invalid"
                                        " identifier")
                                else:
                                    # Found previous release identifier
                                    column += m.end()
                                    identifier = m.group(0)
                                    state += 1
                                    continue
                            elif state == 5:
                                if self.debug != 0:
                                    print(">>Previous closer")
                                m = re.match(r';', line[column:])
                                if m == None:
                                    raise ParserError(line, index, column,
                                        "Missing \';\'")
                                else:
                                    # Found previous closer
                                    column += m.end()
                                    # Move back the state to find other releases
                                    state = 0
                                    continue
                            else:
                                # Should never reach this
                                raise ParserError(line, index, column, "Unknown"
                                    "parser state")
                    else:
                        continue
            except ParserError as e:
                raise e
        self.releases = releases

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

    def duplicates(self):
        """
        Find and return a list of duplicates for each release.

        If no duplicates are found, return an empty list

        :returns: A list of tuples in the form [(release, [(scope, [duplicates])])]
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

    #TODO complete this with checks in the version precedence
    def check(self):
        """
        Check the map structure
        """

        infos = []
        warnings = []
        have_wildcard = []
        seems_base = []

        # Find duplicated symbols
        d = self.duplicates()
        if d:
            for release, duplicates in d:
                message = 'WARNING: Duplicates found in release %s:' %(release)
                warnings.append(message)
                for scope, symbols in duplicates:
                    message = ' ' * 4 + scope + ':'
                    warnings.append(message)
                    for symbol in symbols:
                        message = ' ' * 8 + symbol
                        warnings.append(message)

        # Check '*' wildcard usage
        for release in self.releases:
            for scope, symbols in release.symbols:
                if scope == 'local':
                    if "*" in symbols:
                        message = "INFO : %s" %(release.name)
                        message += " contains the local \'*\' wildcard"
                        infos.append(message)
                        if release.previous:
                            # Release contain predecessor version and local: *;
                            message = "WARNING: %s should not contain the"
                            " local wildcard because it is not the base"
                            " version (it refers to version %s as its"
                            " predecessor" %(release.name, release.previous)
                            warnings.append(message)
                        else:
                            # Release seems to be base: empty predecessor
                            message = "INFO: %s" %(release.name)
                            message += " seems to be the base version"
                            infos.append(message)
                            seems_base.append(release.name)

                        # Append to the list of releases which contain the
                        # wildcard '*'
                        have_wildcard.append((release.name, scope))
                elif scope == 'global':
                    if "*" in symbols:
                        # Release contains '*' wildcard in global scope
                        message = "WARNING: %s contains the" %(release.name)
                        message += " \'*\' wildcard in global scope."
                        message += " It is probably exporting"
                        message += " symbols it should not."
                        warnings.append(message)
                        have_wildcard.append((release.name, scope))
                else:
                    # Release contains unknown visibility scopes (not global or
                    # local)
                    message = "WARNING: %s" %(release.name)
                    message += " contains unknown"
                    message += " scope named \'%s\'" %(scope)
                    message += " (different from \'global\' and \'local\')"
                    warnings.append(message)

        if have_wildcard:
            if len(have_wildcard) > 1:
                # The '*' wildcard was found in more than one place
                message = "WARNING: The \'*\' wildcard was found in more than"
                message += " one place:"
                warnings.append(message)
                for name, scope in have_wildcard:
                    warnings.append(" " * 4 + "%s: in \'%s\'" %(name, scope))
        else:
            warnings.append("WARNING: the \'*\' wildcard was not found")

        if seems_base:
            if len(seems_base) > 1:
                # There is more than one release without predecessor and
                # containing '*' wildcard in local scope
                message = "WARNING: More than one release seems the base"
                " version (contains the local wildcard and does not have a"
                " predecessor version):"
                warnings.append(message)
                for name in seems_base:
                    warnings.append(" " * 4 + "%s" %(name))
        else:
            warnings.append("WARNING: No base version release found")

        # Print all warnings
        if warnings:
            for warning in warnings:
                print(warning)

        # Print all infos
        if infos:
            for info in infos:
                print(info)

    #TODO
    def autoupdate(self):
        """
        Given the new list of symbols, update the map

        The new map will be generated by the following rules:
        - If new symbols are added, a new release is created containing the new
          symbols. This is a compatible update.
        - If a previous existing symbol is removed, then all releases are
          unified in a new release. This is an incompatible change, the SONAME
          of the library should be bumped
        """
        print("Not ready yet")

    def __next__(self):
        """
        Gets the next Release (for the iterator)
        """
        if self.index == len(self.releases):
            raise StopIteration
        self.index += 1
        return self.releases[self.index - 1]

    def __str__(self):
        """
        Print the map in a usable form for the linker
        """
        content = ''
        for release in self.releases:
            content += release.__str__()
            content += "\n"
        return content

    def __iter__(self):
        return self

    def __init__(self, debug=0, filename=None):
        # For debugging
        self.debug = debug
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

# The run script

try:
    l = Map(filename = sys.argv[1])

    l.check()

except ParserError as e:
    print(e)
except:
    raise
