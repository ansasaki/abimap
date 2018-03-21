import sys
import re

def get_info_from_release(release):
    version = [None, None, None]
    ver_suffix = ''
    prefix = ''

    m = re.search(r'_+[0-9]+', release)
    if m:
        prefix = release[:m.start()]

    m = re.search(r'_([0-9]+)_*([0-9]*)_*([0-9]*)$', release)
    if m:
        for i in range(1, 4):
            if m.group(i):
                version[i - 1] = int(m.group(i))
                ver_suffix += "_%s" %(m.group(i))
    return [release, prefix, ver_suffix, version]

def bump_version(version, abi_break):
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

class ParserError(Exception):
    """
    Exception type raised by the map parser
    """

    INFO = 0
    WARNING = 1
    ERROR = 2

    severity_msg = {0 : 'INFO',
                    1 : 'WARNING',
                    2 : 'ERROR'}

    def __str__(self):
        content = ''
        content += "%s: in line %d, column %d: %s\n" %(
            self.severity_msg[self.severity],
            self.line + 1,
            self.column,
            self.message)
        content += self.context
        content += " " * (self.column - 1)
        content += '^'
        return content

    def __init__(self, context, line, column, message, severity=ERROR):
        self.context = context
        self.line = line
        self.column = column
        self.message = message
        self.severity = severity

#TODO
class DependencyError(Exception):
    """
    Exception type raised by dependency checker
    """

    def __str__(self):
        return self.message

    def __init__(self, message):
        self.message = message

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
                        if self.debug != 0:
                            print(">>Name")
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
                                %(name), severity = ParserError.WARNING)
                            continue
                    # Searching for the '{'
                    elif state == 1:
                        if self.debug != 0:
                            print(">>Opening")
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
                        if self.debug != 0:
                            print(">>Element")
                        m = re.match(r'\}', line[column:])
                        if m != None:
                            if self.debug != 0:
                                print(">>Release closer, jump to Previous")
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
                        if self.debug != 0:
                            print(">>Element closer")
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
                                    severity = ParserError.WARNING)
                            else:
                                # Symbol found
                                v[1].append(identifier)
                                column += m.end()
                                last = (index, column)
                                # Move back the state to find elements
                                state = 2
                                continue
                    elif state == 4:
                        if self.debug != 0:
                            print(">>Previous")
                        m = re.match(r'^;', line[column:])
                        if m != None:
                            if self.debug != 0:
                                print(">>Empty previous")
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
                        if self.debug != 0:
                            print(">>Previous closer")
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
                    if e.severity != e.ERROR:
                        print(e)
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

        with open(filename, "r") as f:
            self.filename = filename
            self.lines = f.readlines()
            try:
                self.parse(self.lines)
            except ParserError as e:
                raise e
        self.init = True

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
        Find and return a list of duplicated symbols for each release.

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

    def dependencies(self):
        """
        Construct the dependencies lists

        :returns:   A list containing the dependencies lists
        """

        def get_dependency(releases, current):
            found = [release for release in releases if release.name == current]
            if not found:
                raise DependencyError("ERROR: release \'%s\' not found"
                %(current))
            if len(found) > 1:
                raise DependencyError("ERROR: defined more than 1 release"
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
                        msg += "ERROR: circular dependency detected!\n"
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
                        message = "INFO: %s" %(release.name)
                        message += " contains the local \'*\' wildcard"
                        infos.append(message)
                        if release.previous:
                            # Release contain predecessor version and local: *;
                            message = "WARNING: %s" %(release.name)
                            message += " should not contain the local wildcard"
                            message += " because it is not the base version"
                            message += " (it refers to version"
                            message += " \'%s\' as its" %(release.previous)
                            message += " predecessor)"
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

        try:
            dependencies = self.dependencies()
            print("Found dependencies: ")
            for release in dependencies:
                cur = '    '
                for dep in release:
                    cur += "%s->" %(dep)
                print(cur)
        except DependencyError as e:
            print(e)

        # Print all warnings
        if warnings:
            for warning in warnings:
                print(warning)

        # Print all infos
        if infos:
            for info in infos:
                print(info)

    def guess_latest_release(self):
        """
        Try to guess the latest release

        :returns:   A list [release, prefix, suffix, version[CUR, AGE, REV]] 
        """
        if not self.init:
            print("Map not initialized, try to read a file first")
            return ''

        deps = self.dependencies()

        heads = (dep[0] for dep in deps)

        latest = [None, None, '_0_0_0', None]
        for release in heads:
            info = get_info_from_release(release)
            if info[2] > latest[2]:
                latest = info

        #TODO If not max_head[4] --> use longest dependency ?

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

        # Check if the map object was initialized
        if not self.init:
            print("Map not initialized, try to read a file first")
            # TODO raise error instead
            return ''

        # If the new release name was given, just use it
        if new_release:
            if self.debug != 0:
                print("[guess]: New release found, using it")
            return new_release

        # If the two required parts were given, just combine and return
        if new_prefix:
            if new_suffix:
                if self.debug != 0:
                    print("[guess]: Two parts found, using them")
                return new_prefix + new_suffix
            elif new_ver:
                if self.debug != 0:
                    print("[guess]: Prefix and version found, using them")
                new_suffix = ''
                for i in new_ver:
                    new_suffix += '_%d' %(i)
                return new_prefix + new_suffix

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
            if self.debug != 0:
                print("[guess]: Previous release found")
            prev_info = get_info_from_release(prev_release)
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
                if self.debug != 0:
                    print("[guess]: Using previous prefix as the new")
                # Reuse the prefix from the previous release, if available
                new_prefix = prev_prefix
            else:
                if self.debug != 0:
                    print("[guess]: Trying to find common prefix")
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
                        if self.debug != 0:
                            print("[guess]: Common prefix found")
                        # Search and remove any version info found as prefix
                        m = re.search(r'_+[0-9]+|_+$', new_prefix)
                        if m:
                            new_prefix = new_prefix[:m.start()]
                    else:
                        if self.debug != 0:
                            print("[guess]: Using prefix from latest")
                        # Try to use the latest_release prefix
                        head = self.guess_latest_release()
                        new_prefix = head[1]

        # At this point, new_prefix can still be None

        if not new_suffix:
            if self.debug != 0:
                print("[guess]: Guessing new suffix")

            # If the new version was given, make the suffix from it
            if new_ver:
                if self.debug != 0:
                    print("[guess]: Using new version to make suffix")
                new_suffix = ''
                for i in new_ver:
                    new_suffix += "_%d" %(i)

            elif not prev_ver:
                if self.debug != 0:
                    print("[guess]: Guessing latest release to make suffix")
                # Guess the latest release
                head = self.guess_latest_release()
                if head[3]:
                    if self.debug != 0:
                        print("[guess]: Got suffix from latest")
                    prev_ver = head[3]

            if not new_suffix:
                if prev_ver:
                    if self.debug != 0:
                        print("[guess]: Bumping release")
                    new_ver = bump_version(prev_ver, abi_break)
                    new_suffix = ''
                    for i in new_ver:
                        #if i:
                        new_suffix += "_%d" %(i)

        if not new_prefix or not new_suffix:
            # ERROR: could not guess the name
            raise Exception("Could not guess the name")

        # Return the combination of the prefix and version
        return new_prefix + new_suffix

    #TODO
    def autoupdate(self, new_symbols, dry=False):
        """
        Given the new list of symbols, update the map

        The new map will be generated by the following rules:
        - If new symbols are added, a new release is created containing the new
          symbols. This is a compatible update.
        - If a previous existing symbol is removed, then all releases are
          unified in a new release. This is an incompatible change, the SONAME
          of the library should be bumped
        """

        new_set = set(new_symbols)

        all_symbols = list(self.all_symbols())

        added = []
        removed = []
        for symbol in new_set:
            if symbol not in all_symbols:
                added.append(symbol)

        for symbol in all_symbols:
            if symbol not in new_set:
                removed.append(symbol)

        if added:
            added.sort()
            msg = "Added:\n"
            for symbol in added:
                msg += "    %s\n" %(symbol)
            print(msg)

        if removed:
            removed.sort()
            msg = "Removed:\n"
            for symbol in removed:
                msg += "    %s\n" %(symbol)
            print(msg)

        latest = self.guess_latest_release()

        # TODO Order the releases
        # TODO User interface
        # TODO Check before print map
        if not dry:
            if removed:
                print("ABI break detected: symbols were removed since last"
                " version")
                print("Merging all symbols in a single new release")
                new_map = Map()
                r = Release()
                r.name = self.guess_name(abi_break=True)
                for symbol in removed:
                    all_symbols.remove(symbol)
                all_symbols.extend(added)
                r.symbols.append(('global', all_symbols))
                new_map.releases.append(r)
                r.symbols.append(('local', ['*']))
                print(new_map)
            else:
                if added:
                    r = Release()
                    r.name = self.guess_name()
                    r.symbols.append(('global', added))
                    r.previous = latest[0]
                    self.releases.append(r)
                    print(self)


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
        # The state
        self.init = False
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
#    l = Map(filename = sys.argv[1], debug=1)
    l = Map(filename = sys.argv[1])
    l.check()

    new_symbols = []
    lines = sys.stdin.readlines()
    for line in lines:
        new_symbols.extend(line.split())
    if new_symbols:
        l.autoupdate(new_symbols)
#    new_name = l.guess_name()
#    print("Guessed name: %s" %(new_name))
#    new_name = l.guess_name(new_ver = [6, 6, 6])
#    print("Guessed name: %s" %(new_name))
#    new_name = l.guess_name(new_prefix = 'libwhatever')
#    print("Guessed name: %s" %(new_name))
#    new_name = l.guess_name(new_prefix = 'libwhatever', prev_ver = [6, 6, 6])
#    print("Guessed name: %s" %(new_name))

#    new_name = l.guess_name(abi_break=True)
#    print("Guessed name: %s" %(new_name))
#    new_name = l.guess_name(new_ver = [6, 6, 6], abi_break=True)
#    print("Guessed name: %s" %(new_name))
#    new_name = l.guess_name(new_prefix = 'libwhatever', abi_break=True)
#    print("Guessed name: %s" %(new_name))
#    new_name = l.guess_name(new_prefix = 'libwhatever', new_ver = [6, 6, 6], abi_break=True)
#    print("Guessed name: %s" %(new_name))
#    new_name = l.guess_name(new_prefix = 'libwhatever', prev_ver = [6, 6, 6],
#    abi_break=True)
#    print("Guessed name: %s" %(new_name))
except ParserError as e:
    print(e)
except:
    raise
