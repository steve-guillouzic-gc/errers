# coding=utf-8
#
# SPDX-FileCopyrightText: 2023 His Majesty in Right of Canada
#
# SPDX-License-Identifier: LicenseRef-MIT-DND
#
# This file is part of the ERRERS package.

"""ERRERS: extraction engine

All elements of this module are implementation details that may change in
non-backward-compatible ways between minor or micro version releases.

Constants:
    TIMEOUT -- default timeout for individual search patterns and
        substitution rules used as indication of catastrophic backtracking
    NOT_COMMENTED -- pattern prefix ensuring that LaTeX command is not in a
        comment
    NOT_ESCAPED -- pattern prefix ensuring that following character is not
        escaped, while recognizing newline commands

Metaclasses:
    MetaDocument -- read-only interface to content of a LaTeX document

Classes:
    EncodingError -- mismatch between file content and declared or implicit
        encoding

Function:
    extract -- extract text from LaTeX file

The following elements are internal elements of the module.

Constants: logging
    _misc_logger -- miscellaneous log messages
    _pattern_logger -- output of patterns option
    _step_logger -- output of steps option
    _trace_logger -- output of trace option

Functions (internal):
    _create_classes -- create pattern and rule classes
    _log_versions -- log software version information
    _log_options -- log option-specific info
    _log_left -- log list of remaining LaTeX commands
    _select_rules -- build rule list for LaTeX document
    _gather_rules -- gather rules for LaTeX classes, LaTeX packages and BibTeX
        style
    _seek_rules -- seek rule function and return output if found
    _write_times -- write run times to file
"""

__all__ = ['TIMEOUT', 'extract']

import collections
import csv
import functools as ft
try:
    import importlib.metadata
except ModuleNotFoundError:
    pass
import io
import logging
import platform
import sys
import textwrap

try:
    import pywintypes
    import win32api
except ModuleNotFoundError:
    pass

from errers import rules, __version__
from errers._engine import latex

# Constants
TIMEOUT = 5

# Pattern prefixes and suffixes
NOT_COMMENTED = textwrap.dedent(r"""
                # NOT COMMENTED
    ^           # Between start of line and following text,
    (?:         # only allow
        \\%     # escaped %
        |       # or
        [^%\n]  # any character beside %.
    )*
    """)
NOT_ESCAPED = textwrap.dedent(r"""
                     # NOT ESCAPED
    (?<!             # Don't match if preceded by one backslash
        (?<!         # Match if preceded by two backslashes (newline command)
            (?<!\\)  # Don't match if preceded by three backslashes
        \\)
    \\)
    """)

# Logging (internal)
_misc_logger = logging.getLogger('errers.log')
_pattern_logger = logging.getLogger('errers.patterns')
_step_logger = logging.getLogger('errers.steps')
_trace_logger = logging.getLogger('errers.trace')


class MetaDocument:
    """Read-only interface to content of LaTeX document.

    Sub-classes must specify the class to use for rule lists. Its embedded
    Pattern and Rule classes are used for pattern matching and substitution
    rules.

    The information is supplemented by the LaTeX log file, if present, in order
    to identify document classes and packages that are loaded indirectly (in
    other words, that are loaded by other classes and packages).

    Class methods:
        __init_subclass__ -- subclass initializer, which includes defining
            internal search patterns

    Child class attributes:
        RuleList -- class used for rule lists
        _encoding -- pattern to extract file encoding
        _class -- pattern to extract document class from LaTeX file
        _packages -- pattern to extract package names from LaTeX file
        _style -- pattern to extract bibliography style
        _comments -- rules to extract comments from content (commented lines
            are those that start with %; newlines are kept for non-commented
            lines so rule definition lines can be determined)
        _rule_specs -- pattern to extract rule specifications
        _flag -- pattern to extract flags
        _classes_log -- pattern to extract document classes from log file
        _packages_log -- pattern to extract package names from log file
        _unwrap -- rules to unwrap lines in replacement strings

    Attribute:
        path -- path of LaTeX document
        content -- content of LaTeX document
        comments -- commented lines of LaTeX document with % removed
        encoding -- return encoding specified using package inputenc
        log -- content of log file (None if missing)
        _sanitize -- rule used to sanitize class, package and style names

    Methods:
        __init__ -- initializer
        read_file -- read document from file
        document_classes -- return list of classes used by document
        packages -- return list of packages used in document
        bibliography_style -- return name of bibliographic style used
        rules -- return list of Rule objects defined in document
    """

    def __init_subclass__(cls, RuleList, **kwargs):
        """Specify class-level attributes.

        Argument:
            Pattern -- class used internally for pattern matching
        """
        super().__init_subclass__(**kwargs)
        cls.RuleList = RuleList
        Rule = RuleList.Rule
        Pattern = Rule.Pattern

        # Define search patterns to extract information from LaTeX file
        cls._encoding = Pattern(NOT_COMMENTED + r'\\usepackage%s{inputenc}',
                                scope=cls.__name__)
        cls._class = Pattern(NOT_COMMENTED + r'\\documentclass%s?%C',
                             scope=cls.__name__)
        cls._packages = Pattern(NOT_COMMENTED + r'\\usepackage%s?%C',
                                scope=cls.__name__)
        cls._style = Pattern(NOT_COMMENTED + r'\\bibliographystyle%C',
                             scope=cls.__name__)
        cls._comments = RuleList([
            # Clear lines that do not start with %.
            Rule(r'^[^%\n].*', '', scope=cls.__name__),
            # Uncomment those that do.
            Rule('^%(.*)', r'\1', scope=cls.__name__)
        ])
        cls._rule_specs = Pattern(textwrap.dedent(r"""
            (?s)                          # Period matches \n too
            ^                             # Beginning of line
            %h                            # Optional white space
            Rule\(                        # "Rule" and opening parenthesis
            %n                            # Optional white space
            (?P<rpat>r)?+                 # Optional raw string prefix
            (?P<qpat>"{3}|'''|"|')        # Opening quote of search pattern
            (?P<pat>                      # Matching pattern:
                (?:                       # as many characters as possible
                    (?!
                        (?<!\\)           # except non-escaped
                        (?P=qpat)         # quotes.
                    ).
                )*+
            )
            (?P=qpat),                    # Closing quote and comma
            %n                            # Optional white space
            (?P<rrep>r)?+                 # Optional raw string prefix
            (?P<qrep>"{3}|'''|"|')        # Opening quote of replacement string
            (?P<rep>                      # Replacement string:
                (?:                       # as many characters as possible
                    (?!
                        (?<!\\)           # except non-escaped
                        (?P=qrep)         # quotes.
                    ).
                )*+
            )
            (?P=qrep)                     # Closing quote
            (?:
                (?:                           # Optional iterative argument:
                    ,                         # comma,
                    %n                        # optional white space,
                    iterative                 # iterative keyword,
                    %n                        # optional white space,
                    =                         # assignment,
                    %n                        # optional white space, and
                    (?P<iterative>True|False) # True or False;
                )
                |                             # or
                (?:                           # optional phase argument:
                    ,                         # comma,
                    %n                        # optional white space,
                    phase                     # phase keyword,
                    %n                        # optional white space,
                    =                         # assignment,
                    %n                        # optional white space,
                    (?P<qphase>"{3}|'''|"|')  # Opening quote,
                    (?P<phase>                # String value
                        (?:                   # (as many characters as
                            (?!               #  possible,
                                (?<!\\)       #  except non-escaped
                                (?P=qphase)   #  quotes), and
                            ).
                        )*+
                    )
                    (?P=qphase)               # Closing quote.
                )
            ){0,2}                        # Both arguments may be present.
            %n                            # Optional white space
            \)                            # Closing parenthesis
            """), scope=cls.__name__)

        # Define search patterns to extract information from log file
        name_pattern = '[a-zA-Z0-9_-]++'
        cls._classes_log = Pattern(r'Document\ Class:\ (%s)' % name_pattern,
                                   scope=cls.__name__)
        cls._packages_log = Pattern(r'Package:\ (%s)' % name_pattern,
                                    scope=cls.__name__)

    def __init__(self, latex_doc):
        """Initialize Document object.

        Argument:
            latex_doc -- path of LaTeX file (or string containing LaTeX input)
        """
        Document = type(self)
        # Rule to sanitize LaTeX file names for use as Python identifiers.
        # Hyphens and periods are changed to underscores. Since file names may
        # start with a digit (0-9), a prefix must be prepended to the result.
        self._sanitize = Document.RuleList.Rule('[-.]', '_')
        try:
            # Try loading LaTeX document from file.
            with open(latex_doc, encoding='utf-8', errors='replace') as file:
                match = Document._encoding.search(file.read())
                if match:
                    self.encoding = match['s1']
                else:
                    self.encoding = 'utf-8'
            self.path = latex_doc
            self.content = self.read_file()
        except FileNotFoundError:
            if isinstance(latex_doc, str):
                # Assume document content is already in latex_doc.
                self.content = latex_doc
                self.path = None
            else:
                raise
        self.comments = Document._comments.sub(self.content)
        try:
            log_path = latex_doc.with_suffix('.log')
            with open(log_path, encoding='utf-8', errors='replace') as file:
                self.log = file.read()
                _misc_logger.info('LaTeX log: %s', log_path.name)
        except IOError:
            self.log = None
            no_log = 'LaTeX log file missing'
        except AttributeError:
            self.log = None
            no_log = 'No LaTeX log file for document read from memory'
        if self.log is None:
            _misc_logger.warning(
                    '%s: rules applied only for commands from packages and '
                    'document classes mentioned explicitly in LaTeX document. '
                    '(When LaTeX log file is available, rules are also '
                    'applied for packages and document classes that are '
                    'loaded indirectly by other packages and classes.)',
                    no_log)

    def read_file(self, file_path=None, default_extension='',
                  location_rules=None):
        """Read document from file.

        Argument:
            file_path -- path of file to insert (relative or absolute); if
                None, read file from self.path
            default_extension -- extension if file_path has none
            location_rules -- list of location rules gathered by _select_rules
                (None when reading main document)

        Returns:
            file content
        """
        if self.path is None:
            _misc_logger.error('Insertion of file "%s" failed because main '
                               'document read from memory rather than file.',
                               file_path)
            return ''
        if file_path is None:
            file_path = self.path
        else:
            file_path = self.path.parent.joinpath(file_path)
        if file_path.suffix == '':
            file_path = file_path.with_suffix(default_extension)
        try:
            relative_path = file_path.relative_to(self.path.parent)
        except ValueError:
            # Path to input file is not relative to path of main file
            relative_path = file_path
        try:
            with open(file_path, encoding=self.encoding) as file:
                _misc_logger.info('Loaded file: %s', relative_path)
                content = file.read()
        except FileNotFoundError:
            _misc_logger.error('Missing file: %s', relative_path)
            return ''
        except UnicodeDecodeError as err:
            raise EncodingError(relative_path, err)
        if location_rules:
            content = location_rules.sub(content, file_name=file_path.name)
        return content

    def document_classes(self):
        """Return list of document classes.

        This method returns a  list of classes because, while a document has
        only one class, each class may load other ones.
        """
        # pylint: disable=protected-access
        # Reason: Document is child class rather than client
        Document = type(self)
        if self.log is None:
            try:
                return [Document._class.search(self.content)
                                .group('c1').strip()]
            except AttributeError:
                # No \documentclass
                return []
        else:
            return [self._sanitize.sub(document_class)
                    for document_class
                    in Document._classes_log.findall(self.log)]

    def packages(self):
        """Return, as list, the names of packages used in document."""
        # pylint: disable=protected-access
        # Reason: Document is child class rather than client
        Document = type(self)
        if self.log is None:
            # Get list of packages from document.
            packages = [name.strip()
                        for match in Document._packages.finditer(self.content)
                        for name in match['c1'].split(',')]
        else:
            # Get list of packages from log file.
            packages = [self._sanitize.sub(package)
                        for package
                        in Document._packages_log.findall(self.log)]
        return packages

    def bibliography_style(self):
        """Return name of bibliographic style."""
        # pylint: disable=protected-access
        # Reason: Document is child class rather than client
        Document = type(self)
        try:
            style = Document._style.search(self.content).group('c1').strip()
            return self._sanitize.sub(style)
        except AttributeError:
            # No \bibliographystyle
            return None

    def rules(self):
        r"""Return rule list embedded in document.

        Returns:
            Dictionary of RuleList objects, one for each of the extraction
            phases: 'location', 'insertion', 'removal', 'setup', 'main' and
            'cleanup'

        Rules must be listed in commented lines, but can appear anywhere in the
        document and not necessarily contiguously. Each rule can span multiple
        lines. Example
        % Rule(r'\\mytitle%C', r'\n\g<c1>\n')
        % Rule(r'(?s)\\myfootnote(?:text)?%s?%C(?P<rest_of_para>.*?)\n%h\n',
        %      r'\g<rest_of_para> (\g<c1>)\n\n', iterative=True)

        The syntax for rules is the same as in the Python code, except that
        only replacement strings can be specified (functions and classes are
        not allowed). In order, here are the syntax element of each rule:
            1. Percent sign (%) at the beginning of the line;
            2. "Rule" and opening parenthesis;
            3. Matching pattern between pair of quotes of a given type (single
               quote, double quote or triplet of either; search pattern must
               not contain selected type of quote unless escaped)
            4. Comma;
            5. Same as 3, but for the replacement string;
            6. Optionally, another comma followed by iterative=True or
               iterative=False;
            7. Optionally, another comma followed by phase='X', where X is
                'location', 'insertion', 'removal', 'setup', 'main' or
                'cleanup'; and
            8. Closing parenthesis.
        An arbitrary amount of white space can be added after the percent sign,
        the opening parenthesis and commas, as well as before the closing
        parenthesis. This white space can include up to one newline character
        in each location, except between the percent sign and "Rule", but each
        line of a rule must start with a percent sign.
        """
        # pylint: disable=protected-access
        # Reason: Document is child class rather than client
        Document = type(self)
        RuleList = Document.RuleList
        Rule = RuleList.Rule
        # Extract rule specifications
        rule_specs = [(m['rpat'] == 'r',
                       m['pat'],
                       m['rrep'] == 'r',
                       m['rep'],
                       m['iterative'] == 'True',
                       'main' if m['phase'] is None else m['phase'],
                       m.start())
                      for m in Document._rule_specs.finditer(self.comments)]

        # Build and return rule list
        rlists = {'location': RuleList(),
                  'insertion': RuleList(),
                  'removal': RuleList(),
                  'setup': RuleList(),
                  'main': RuleList(),
                  'cleanup': RuleList()}
        for (raw_pat, pat, raw_rep, rep,
                iterative, phase, start) in rule_specs:
            line = self.comments.count('\n', 0, start) + 1
            rule = Rule(pat, rep, iterative=iterative,
                        file='<string>' if self.path is None
                        else self.path.name,
                        line=line, scope='')
            try:
                rlists[phase].append(rule)
            except KeyError:
                _misc_logger.error('Unknown extraction phase in document rule '
                                   '(line %d): %s; rule ignored',
                                   line, phase)
            else:
                rule_str = repr(rule)
                _misc_logger.info('Document rule (line %d): %s',
                                  line, f'{rule_str[:-1]}, phase={phase})')
                if '\\' in pat and not raw_pat or '\\' in rep and not raw_rep:
                    _misc_logger.warning("'r' prefix missing in document rule "
                                         "at line %d: %s", line, rule)
        return rlists


class EncodingError(Exception):
    """Mismatch between file content and declared or implicit encoding

    Methods:
        __init__: initializer
    """

    def __init__(self, file, error):
        """Initialize exception.

        Arguments:
            file -- faulty input file
            error -- encoding error
        """
        message = textwrap.fill(textwrap.dedent("""\
                  Content of file %s does not match declared or implicit
                  encoding. More precisely, %s. Files are assumed to be encoded
                  as UTF-8 unless declared otherwise using
                  \\usepackage[CODEC]{inputenc} in main LaTeX file, where CODEC
                  is the desired encoding.""" % (file, error)), width=1000)
        super().__init__(message)


def extract(latex_doc, re_module, *, auto=True, default=True, local=True,
            timeout=TIMEOUT, interruption=None):
    r"""Extract text from LaTeX document.

    Arguments:
        latex_doc -- path of LaTeX file or string containing LaTeX input
        re_module -- regular expression module for extraction (standard re
            module or third party regex module)
        auto -- whether to define rules automatically for LaTeX commands
            defined in document using \newcommand, \renewcommand,
            \providecommand, \def, \edef, \gdef and \xdef.
        default -- whether to apply default rules
        local -- whether to apply local rules
        timeout -- timeout in seconds for individual pattern matching and
            substitution rules used to indicate likely catastrophic
            backtracking
        interruption -- event originating from the main thread indicating that
            the extraction thread must terminate

    Returns:
        2-tuple: extracted text as string, and CSV string with detailed times

    Logging:
        Messages are recorded using the logging module. Three loggers are used:
            errers.patterns -- output from patterns option;
            errers.trace -- output from trace option;
            errers.steps -- output from steps option; and
            errers.misc -- everything else.

    Exceptions:
        FileNotFoundError -- input file not found
        CatastrophicBacktracking -- likely catastrophic backtracking detected
            in one of the regular expressions
        Interruption -- extraction interrupted by user
        RegularExpressionError -- extraction interrupted by raised exception
    """
    # Write software version information and impact of various options to log.
    _log_versions(re_module)
    _log_options(re_module, auto, default, local)
    # Obtain classes customized for specified regular expression module.
    _misc_logger.info('Starting extraction')
    Pattern, _, Document \
        = _create_classes(re_module, timeout, interruption)
    # Process LaTeX file
    document = Document(latex_doc)
    location_rules, other_rules = _select_rules(document, auto, default, local)
    if _step_logger.isEnabledFor(logging.DEBUG):
        message = document.content + '=' * 80
        _step_logger.debug(message)
    file_name = '<string>' if document.path is None else document.path.name
    text = location_rules.sub(document.content, steps=True,
                              file_name=file_name)
    text = other_rules.sub(text, steps=True)
    # Report on remaining commands and compilation + run times.
    left = Pattern(r'\\(?:[a-zA-Z]++|.)').findall(text)
    if left and _misc_logger.isEnabledFor(logging.WARNING):
        _log_left(left, auto, default, local, document.log is None)
    _misc_logger.info('Extraction done')
    with io.StringIO() as times_file:
        _write_times(Pattern, times_file)
        times = times_file.getvalue()
    return (text, times)


# The following elements are implementation details that may change in
# non-backward-compatible ways between minor or micro version releases.


def _create_classes(re_module, timeout, interruption):
    """Create pattern and rule classes.

    Arguments:
        re_module -- regular expression module
        timeout -- timeout for pattern matching with third-party regex module
        interruption -- event originating from the main thread indicating that
            the extraction thread must terminate

    Returns:
        3-tuple: Pattern, RuleList and Document classes
    """

    Pattern, _, RuleList \
        = latex.create_classes(re_module, timeout, interruption)

    class Document(MetaDocument, RuleList=RuleList):
        """Read-only interface to content of LaTeX document."""

    return Pattern, RuleList, Document


def _log_versions(re_module):
    """Log software version information.

    Arguments:
        re_module -- regular expression module
    """
    _misc_logger.info('ERRERS version: %s', __version__)
    _misc_logger.info('Bundled application: %s',
                      'Yes' if getattr(sys, 'frozen', False) else 'No')
    _misc_logger.info('Python version: %s', platform.python_version())
    if re_module.__name__ == 'regex' and 'importlib.metadata' in sys.modules:
        try:
            version = '%s (%s)' % (re_module.__version__,
                                   importlib.metadata.version('regex'))
        except importlib.metadata.PackageNotFoundError:
            version = re_module.__version__
    else:
        version = re_module.__version__
    _misc_logger.info('Regular expression module: %s %s',
                      re_module.__name__, version)
    if 'win32api' in sys.modules:
        # Try two ways of getting version info for pywin32: from library
        # file and from package metadata. Version is unknown if both are
        # unavailable.
        #
        # Refs for first method:
        # jcalderone.livejournal.com/54911.html
        # timgolden.me.uk/python/win32_how_do_i/get_dll_version.html
        # timgolden.me.uk/pywin32-docs/win32api.html
        # learn.microsoft.com/en-us/windows/win32/api/verrsrc/ns-verrsrc-vs_fixedfileinfo
        try:
            info = win32api.GetFileVersionInfo(win32api.__file__, '\\')
        except pywintypes.error:
            if 'importlib.metadata' in sys.modules:
                try:
                    version = importlib.metadata.version('pywin32')
                except importlib.metadata.PackageNotFoundError:
                    version = 'unknown'
            else:
                version = 'unknown'
        else:
            version = win32api.HIWORD(info['FileVersionLS'])
        _misc_logger.info('pywin32 version: %s', version)
    _misc_logger.info('System: %s %s (%s)', platform.system(),
                      platform.release(), platform.version())
    _misc_logger.info('Machine: %s', platform.machine())


def _log_options(re_module, auto, default, local):
    """Log option-specific information.

    Arguments:
        re_module -- regular expression module
        auto -- whether to define rules automatically for LaTeX commands
            defined in document
        default -- whether to apply default rules
        local -- whether to apply local rules
    """
    if re_module.__name__ == 'regex':
        _misc_logger.info(
                'Using third-party regex module: automatic detection of '
                'catastrophic backtracking activated.')
    else:
        _misc_logger.warning(
                'Using standard re module: automatic detection of '
                'catastrophic backtracking deactivated. Ill-designed '
                'substitution rules may cause application to freeze (elapsed '
                'time in status bar will stop updating), and it may need to '
                'be forcibly stopped using task manager. Trace option can be '
                'used to determine offending substitution rule.')
        if sys.version_info < (3, 11, 5):
            _misc_logger.warning(
                    'Likelihood of catastrophic backtracking is higher when '
                    'using re module from Python versions prior to 3.11.5, '
                    'because possessive quantifiers (*+, ++ and ?+) cannot be '
                    'used. This is especially true when LaTeX commands '
                    r'defined in the document using \newcommand, '
                    r'\renewcommand, \providecommand, \def, \edef, \gdef and '
                    r'\xdef involve multiple levels of curly brackets. The '
                    'issue with these definitions can be mitigated by placing '
                    r'them between pairs of \makeatletter and \makeatother '
                    'commands, and defining substitution rules for them '
                    'manually.')
    # Report on usage of auto rules.
    if auto:
        _misc_logger.info('Automatic rules applied')
    else:
        _misc_logger.warning('Automatic rules not applied')
    # Report on usage of default rules.
    if default:
        _misc_logger.info('Default rules applied')
    else:
        _misc_logger.warning('Default rules not applied')
    # Report on usage of local rules.
    if 'errers.rules.local' in sys.modules:
        if local:
            _misc_logger.info('Local rules applied')
        else:
            _misc_logger.warning('Local rules not applied')


def _log_left(left, auto, default, local, nolog):
    """Log list of remaining LaTeX commands after extraction.

    Arguments:
        left -- list of remaining commands
        auto -- whether to define rules automatically for LaTeX commands
            defined in document
        default -- whether to apply default rules
        local -- whether to apply local rules
        nolog -- whether the LaTeX log file was missing
    """
    message = 'LaTeX commands left after extraction. '
    missing = ((['automatic'] if not auto else [])
               + (['default'] if not default else [])
               + (['local'] if not local
                   and 'errers.rules.local' in sys.modules else []))
    if nolog:
        message += ('The LaTeX log file being unavailable may have '
                    'contributed to this, in which case the issue could '
                    'be resolved by compiling the LaTeX document '
                    'before running this application or making sure to '
                    r'add \usepackage commands in the document for '
                    'packages that are loaded indirectly by other '
                    'packages. ')
        played = 'also played'
    else:
        played = 'played'
    if missing:
        if len(missing) > 1:
            which = '%s and %s' % (', '.join(missing[:-1]), missing[-1])
        else:
            which = missing[0]
        message += ('The fact that %s rules were not applied may have '
                    '%s a role in this, and you may want to consider '
                    're-running the extraction with those rules '
                    'activated. ' % (which, played))
    if missing or nolog:
        verb = 'could also be'
        please = 'If so, please'
    else:
        verb = 'would be'
        please = 'Please'
    message += ('Additional substitution rules %s required to eliminate '
                'the remaining commands. %s consider proposing new rules '
                'for inclusion in the next version of the application. '
                % (verb, please))
    left_unique = sorted(set(left))
    left_count = collections.Counter(left)
    message += ('Remaining commands (count in parentheses): %s.'
                % ', '.join(['"%s" (%d)' % (command, left_count[command])
                             for command in left_unique]))
    _misc_logger.warning(message)


def _select_rules(document, auto, default, local):
    r"""Build rule list for LaTeX document.

    Rules for phase 1 are returned separately because they need an extra
    parameter:
        1. Location rules;

    Rules for other phases are put together in this order:
        2. Insertion rules;
        3. Removal rules;
        4. Miscellaneous setup rules;
        5. Main rules;
        6. Brace-cleanup rules; and
        7. Remaining cleanup rules.

    At each phase, rules are run in the following order:
        a) Rules defined in document;
        b) Rules for document class, LaTeX packages and bibliography style; and
        c) Core rules.
    However, only core rules are applied for phase 6 (brace cleanup). For
    sub-phases (b) and (c), rules from the rules.local module are loaded first
    and those from rules.standard are loaded second. Rules for document class
    are obtained from class_%s_%s function, where the first %s is the document
    class and the second %s is one of six suffixes ('location', 'insertion',
    'removal', 'setup', 'main' and 'cleanup') that indicate when rules are
    applied. Rules for each document package are obtained from package_%s_%s
    function, where the first %s is the package name and the second %s is one
    of the six suffixes. Rules for bibliography style are obtained from
    style_%s_%s function, where the first %s is the bibliography style and the
    second %s is one of the six suffixes.

    Arguments:
        document -- Document object representing document
        auto -- whether to define rules automatically for LaTeX commands
            defined in document using \newcommand, \renewcommand,
            \providecommand, \def, \edef, \gdef and \xdef
        default -- whether to include default rules
        local -- whether to include local rules

    Returns:
        2-tuple of rule lists: location rules and other rules
    """
    RuleList = type(document).RuleList
    Rule = RuleList.Rule
    single_pass = Rule.Pattern.re_module.__name__ == 'regex'

    # Define arguments for rule functions
    rule_function_kwargs = {'Rule': RuleList.Rule,
                            'RuleList': RuleList,
                            'logger': _misc_logger,
                            'auto': auto,
                            'default': default,
                            'document': document,
                            'not_commented': NOT_COMMENTED,
                            'not_escaped': NOT_ESCAPED,
                            'single_pass': single_pass}
    # Get document rules.
    doc_rules = document.rules()
    # Gather rules from rule functions with specified suffix for LaTeX classes,
    # LaTeX packages and BibTeX styles.
    cps_rules = ft.partial(_gather_rules,
                           document=document,
                           local=local,
                           rule_function_kwargs=rule_function_kwargs)

    # Seek rules from specific rule function.
    def core_rules(phase):
        return _seek_rules('core_' + phase,
                           RuleList=RuleList,
                           local=local,
                           rule_function_kwargs=rule_function_kwargs)

    # Get all rules for given phase
    def phase_rules(phase):
        return [doc_rules[phase]] + cps_rules(phase) + [core_rules(phase)]

    # Prepare read_file argument to rule functions.
    location_rules = RuleList(phase_rules('location'))
    read_file = ft.partial(document.read_file, location_rules=location_rules)
    rule_function_kwargs['read_file'] = read_file
    # Select rules for document class, packages and bibliography style
    # Build rule list
    other_rules = RuleList()
    # The insertion, removal and setup lists are run only once.
    other_rules.extend(phase_rules('insertion'))
    other_rules.extend(phase_rules('removal'))
    other_rules.extend(phase_rules('setup'))
    # The inner_main list is run iteratively if using the re module.
    inner_main = RuleList(iterative=not single_pass)
    inner_main.extend(phase_rules('main'))
    # The outer_main list is run iteratively if using the re module.
    outer_main = RuleList(iterative=not single_pass)
    outer_main.append(inner_main)
    outer_main.append(core_rules('cleanup_braces'))
    other_rules.append(outer_main)
    # The cleanup list is run only once.
    other_rules.extend(phase_rules('cleanup'))
    return location_rules, other_rules


def _gather_rules(function_suffix, document, local, rule_function_kwargs):
    r"""Gather rules for LaTeX classes, LaTeX packages and BibTex style.

    Arguments:
        function_suffix -- suffix of function names being sought
        document -- Document object representing document
        local -- whether to include local rules
        rule_function_kwargs == keyword arguments for rule functions

    Returns:
        RuleList object
    """
    RuleList = type(document).RuleList
    # Identify rule-function names
    rfuncs = ['class_%s_%s' % (document_class, function_suffix)
              for document_class in document.document_classes()]
    rfuncs.extend(['package_%s_%s' % (package, function_suffix)
                   for package in document.packages()])
    bibliography_style = document.bibliography_style()
    if bibliography_style is not None:
        rfuncs.append('style_%s_%s' % (bibliography_style, function_suffix))
    rlist = RuleList()
    # Build and return rule lists.
    for rule_function in rfuncs:
        rlist.append(_seek_rules(rule_function, RuleList, local,
                                 rule_function_kwargs))
    return rlist


def _seek_rules(function_name, RuleList, local, rule_function_kwargs):
    r"""Seek rule function and return its output if found.

    The rule function is sought in the errers.rules.standard module and, if
    available and local=True, in the errers.rules.local module. When both rule
    modules are present, the rules from errers.rules.local are executed first.

    Arguments:
        function_name -- function name being sought
        RuleList -- class to use for rule lists
        local -- whether to include local rules
        rule_function_kwargs == keyword arguments for rule functions

    Returns:
        RuleList object
    """
    if local and 'errers.rules.local' in sys.modules:
        modules = [rules.local, rules.standard]
    else:
        modules = [rules.standard]
    rlist = RuleList()
    for module in modules:
        if hasattr(module, function_name):
            _misc_logger.info('Getting rules from %s.%s',
                              module.__name__.split('.')[-1],
                              function_name)
            rule_function = getattr(module, function_name)
            rlist.extend(rule_function(**rule_function_kwargs))
    return rlist


def _write_times(Pattern, times_file):
    """Write rule compilation and run times to file.

    Arguments:
        Pattern -- pattern class for which to print times
        timesfile -- file to which times must be written
    """
    writer = csv.writer(times_file)
    writer.writerow(['File', 'Line', 'Scope', 'Compilation Time',
                     'Run Time', 'Run Count', 'Matches', 'Object'])
    for pattern in Pattern.instances:
        writer.writerow([pattern.file,
                         pattern.line,
                         pattern.scope,
                         pattern.compilation.time,
                         pattern.run.time,
                         pattern.run.count,
                         pattern.matches,
                         repr(pattern.user)])
