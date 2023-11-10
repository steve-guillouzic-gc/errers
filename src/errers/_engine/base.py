# coding=utf-8
#
# SPDX-FileCopyrightText: 2023 His Majesty in Right of Canada
#
# SPDX-License-Identifier: LicenseRef-MIT-DND
#
# This file is part of the ERRERS package.

"""ERRERS: custom interface to regular expressions (base classes)

All elements of this module are implementation details that may change in
non-backward-compatible ways between minor or micro version releases.

The create_classes function of the base module returns BasePattern, BaseRule
and BaseRuleList classes that provide a custom interface to the regular
expression engine.

Metaclasses:
    MetaPattern -- custom interface to regular expression patterns
    MetaRule -- text substitution rule
    MetaRuleList -- list of Rule instances

Classes:
    Timer -- context manager to time and count execution of arbitrary code
    CatastrophicBacktracking -- exception raised when there is a suspected
        catastrophic backtracking in a regular expression
    Interruption -- exception raised when extraction is interrupted by user
    RegularExpressionError -- exception raised when there is a regular
        expression error

Function:
    create_classes -- create classes for patterns, rules and rule lists

The following elements are internal elements of the module.

Constants: logging
    _misc_logger -- miscellaneous log messages
    _pattern_logger -- output of patterns option
    _step_logger -- output of steps option
    _trace_logger -- output of trace option

Functions (internal):
    _quote -- return string enclosed in quotes
"""

__all__ = ['CatastrophicBacktracking', 'Interruption',
           'RegularExpressionError', 'create_classes']

import functools as ft
import inspect
import logging
from pathlib import Path
import platform
import sys
import textwrap
import time

# Logging (internal)
_misc_logger = logging.getLogger('errers.log')
_pattern_logger = logging.getLogger('errers.patterns')
_step_logger = logging.getLogger('errers.steps')
_trace_logger = logging.getLogger('errers.trace')


class MetaPattern:
    """Custom interface to regular expression patterns.

    Sub-classes must specify which regex module to use: the standard re module
    or the third-party regex module. They can also specify a timeout value for
    matching operations with the regex module and a list where to store class
    instances.

    Patterns are created with the following flags:
        1. MULTILINE: the ^ and $ symbols are interpreted as the beginning and
           end of line, respectively, rather than beginning and end of pattern;
           and
        2. VERBOSE: white space in patterns is ignored except in character
           classes or when preceded by unescaped backslash, and comments can be
           included using the # character.
    With the regex module, the VERSION1 flag is also specified (see regex
    module documentation: pypi.org/project/regex/).

    Additional options can be set on a per-rule basis using inline flags, such
    as (?s) to request that the period (.) also match the newline character.

    The class maintains a list of created patterns. For each pattern, it
    records:
        1. The user object that uses the regular expression (Pattern or Rule);
        2. The file, line number and scope where the user object was created;
        3. The compilation time of the pattern;
        4. The number of times that the pattern was applied; and
        5. The total run time.

    When used with the regex module, the class applies a timeout to pattern
    searches to detect likely instances of catastrophic backtracking.

    Class attribute:
        level -- how deep in the hierarchy of replacement functions is the rule
            currently being applied (top-level rules are level 0, rules called
            by their replacement functions are level 1, etc.). This is used for
            indenting the trace log.

    Class methods:
        __init_subclass__ -- subclass initializer

    Child class attributes:
        instances -- list of all instantiated patterns
        _flags -- flags used for compilation of regular expressions
        _timeout -- timeout parameter for matching operations

    Properties (read-only):
        user -- object to list in log file as user of the regular expression
            (either a pattern or rule object)
        file, line, scope -- file, line number and scope where pattern is
            defined
        compilation -- compilation timer
        run -- run timer
        matches -- number of matches

    Attributes:
        _user, _file, _line, _scope, _compilation, _run, _matches  -- storage
            of user, file, line, scope, compilation, run and matches property
            values
        _compact -- string representation of pattern for repr and str
        _compiled -- compiled pattern

    Methods:
        __init__ -- initializer
        __repr__ -- return printable representation
        __str__ -- return pretty printable representation
        search -- find location of first match
        findall -- find all matches, returning a list of strings
        finditer -- find all matches, returning an iterator over matches
        subn -- perform substitution and return number of substitutions done
        print_trace -- write Pattern or Rule to log
        _count_subs -- count matches from specific sub groups
    """

    level = 0

    def __init_subclass__(cls, re_module, timeout, interruption,
                          instances=None, InnerRuleList=None, **kwargs):
        """Specify class-level attributes.

        Argument:
            re_module -- regular expression module to use for pattern matching
            timeout -- timeout parameter for matching operations with
                third-party regex module
            instances -- storage list for pattern instances; a new one is
                created if None
            InnerRuleList -- consume InnerRuleList parameter used by mixin
                classes, if present, so it doesn't reach the __init_subclass__
                method of the object class and cause an error; not used by this
                class
        """
        super().__init_subclass__(**kwargs)
        cls.re_module = re_module
        cls.interruption = interruption
        cls.instances = [] if instances is None else instances
        cls._flags = re_module.MULTILINE | re_module.VERBOSE
        if re_module.__name__ == 'regex':
            cls._flags |= re_module.VERSION1
        if re_module.__name__ == 'regex' and timeout is not None:
            cls._timeout = {'timeout': timeout}
        else:
            cls._timeout = {}

    def __init__(self, pattern, *, compact=None, user=None, stack_index=1,
                 file=None, line=None, scope=None, **kwargs):
        """Initialize regular expression.

        Arguments:
            pattern -- regular expression pattern

        Keyword-only arguments:
            compact -- compact representation of pattern (set to pattern if
                None)
            user -- object to list in log files as user of regular expression
                (Pattern instance logged if none provided)
            stack_index -- index of frame entry in stack for pattern or rule
                instantiator; sub-classes that define __init__ must increment
                stack_index by 1 and pass it on to the next __init__; __init__
                methods of rule classes should set it to 2
            file, line, scope -- custom values for file, line number and scope
        """
        Pattern = type(self)
        super().__init__(**kwargs)
        # Save information for timing and tracing
        Pattern.instances.append(self)
        self._user = self if user is None else user
        frame_info = inspect.stack()[stack_index]
        try:
            self._file = (Path(frame_info.filename).name
                          if file is None else file)
            self._line = frame_info.lineno if line is None else line
            self._scope = frame_info.function if scope is None else scope
        finally:
            del frame_info
        self._run = Timer()
        self._matches = 0
        self._compact = pattern if compact is None else compact
        try:
            with Timer() as self._compilation:
                self._compiled = Pattern.re_module.compile(pattern,
                                                           Pattern._flags)
        except Pattern.re_module.error as err:
            if err.colno is None:
                _misc_logger.error('Error in search pattern '
                                   '(%s, line %i, %s): %s\n%r',
                                   self._file, self._line, self._scope,
                                   err, self)
            else:
                spaces = err.colno - 1
                _misc_logger.error(
                    'Error in search pattern '
                    '(%s, line %i, %s): %s\n%s\n%s\n%s',
                    self._file, self._line, self._scope,
                    err, err.pattern[0:err.pos],
                    '-' * spaces + '|',
                    ' ' * spaces + err.pattern[err.pos:])
            raise RegularExpressionError() from err
        if self._user is self and _pattern_logger.isEnabledFor(logging.DEBUG):
            message = ('%s, line %i, %s:\n%r\n'
                       % (self._file, self._line, self._scope, self))
            message += '-' * 80 + '\n'
            message += self._compiled.pattern
            if not message.endswith('\n'):
                message += '\n'
            message += '=' * 80
            _pattern_logger.debug(message)

    def __repr__(self):
        """Return official string representation."""
        string = "%s(%s)" % (type(self).__name__, _quote(self._compact))
        return string

    def __str__(self):
        """Return informal string representation."""
        return self._compact

    @property
    def user(self):
        """User of regular expression (pattern or rule object)."""
        return self._user

    @property
    def file(self):
        """File where regular expression user is defined."""
        return self._file

    @property
    def line(self):
        """Line where regular expression user is defined."""
        return self._line

    @property
    def scope(self):
        """Scope where regular expression user is defined."""
        return self._scope

    @property
    def compilation(self):
        """Output of compilation timer."""
        return self._compilation

    @property
    def run(self):
        """Output of run timer."""
        return self._run

    @property
    def matches(self):
        """Number of pattern matches."""
        return self._matches

    def search(self, string):
        """Find location of first match.

        Argument:
            string -- string to be searched

        Returns:
            re_module.match object
        """
        # pylint: disable=protected-access
        # Reason: Pattern is child class rather than client
        Pattern = type(self)
        self.print_trace('Applying')
        with self._run:
            try:
                match = self._compiled.search(string, **Pattern._timeout)
            except Exception as err:
                self.print_trace('Exception in', log_level=logging.ERROR)
                if type(err).__name__ == 'TimeoutError':
                    raise CatastrophicBacktracking(self._user) from err
                raise
        if match is not None:
            self._matches += 1
        return match

    def findall(self, string):
        """Find all matches.

        Argument:
            string -- string to be searched

        Returns:
            list of strings
        """
        Pattern = type(self)
        self.print_trace('Applying')
        with self._run:
            try:
                matches = self._compiled.findall(string, **Pattern._timeout)
            except Exception as err:
                self.print_trace('Exception in', log_level=logging.ERROR)
                if type(err).__name__ == 'TimeoutError':
                    raise CatastrophicBacktracking(self._user) from err
                raise
        self._matches += len(matches)
        return matches

    def finditer(self, string, count_matches=True):
        """Find all matches.

        Arguments:
            string -- string to be searched
            count_matches -- whether to count matches (set to False by
                _count_subs method to avoid double-counting)

        Returns:
            iterator over matches
        """
        Pattern = type(self)
        self.print_trace('Applying')
        with self._run:
            try:
                matches = self._compiled.finditer(string, **Pattern._timeout)
            except Exception as err:
                self.print_trace('Exception in', log_level=logging.ERROR)
                if type(err).__name__ == 'TimeoutError':
                    raise CatastrophicBacktracking(self._user) from err
                raise
        for match in matches:
            if count_matches:
                self._matches += 1
            yield match

    def subn(self, replacement, string, sub_matches=None):
        """Replace non-overlapping matches with specified replacement.

        The method also returns the number of substitutions performed.
        Substitutions from callable replacement specifications that do not
        change the text are excluded from this count, but
        they are included in the total match count for the pattern.

        Arguments:
            replacement -- replacement specification for substitutions
            string -- string on which to apply the substitutions
            sub_matches -- iterable of group names and indices indicating which
                match groups are actual substitutions (all groups are
                considered as such if set to None)

        Returns:
            2-tuple: string with substitution performed and number of
                substitutions (number of substitutions excludes those from
                callable replacement specifications that simply return the
                matched text)
        """
        # pylint: disable=protected-access
        # Reason: Pattern is child class rather than client
        Pattern = type(self)
        if Pattern.interruption is not None and Pattern.interruption.is_set():
            raise Interruption()
        self.print_trace('Applying')
        void_subs = 0
        if callable(replacement):
            def check_sub(match, replacement):
                nonlocal void_subs
                replacement_string = replacement(match)
                if replacement_string == match[0]:
                    void_subs += 1
                return replacement_string
            replacement = ft.partial(check_sub, replacement=replacement)
        with self._run:
            try:
                MetaPattern.level += 1
                newstring, subs = self._compiled.subn(replacement, string,
                                                      **Pattern._timeout)
                MetaPattern.level -= 1
            except Exception as err:
                self.print_trace('Exception in', log_level=logging.ERROR)
                if type(err).__name__ == 'TimeoutError':
                    raise CatastrophicBacktracking(self._user) from err
                raise
        if sub_matches is not None:
            subs = self._count_subs(string, sub_matches)
        effective_subs = subs - void_subs
        self._matches += subs
        return newstring, effective_subs

    def print_trace(self, intro, log_level=logging.DEBUG):
        """Log Pattern or Rule instance.

        Arguments:
            intro -- introductory word indicating context of trace: 'Created',
                'Applying' or 'Exception in'.

        """
        Pattern = type(self)
        if sys.exc_info()[0]:
            logger = _misc_logger
            indent = 0
        else:
            logger = _trace_logger
            indent = 4
        if self._scope == '':
            logger.log(log_level, '%*s%s %s, line %i: %s',
                       indent * Pattern.level, '',
                       intro, self._file, self._line,
                       repr(self._user))
        else:
            logger.log(log_level, '%*s%s %s, line %i, %s: %s',
                       indent * Pattern.level, '',
                       intro, self._file, self._line, self._scope,
                       repr(self._user))

    def _count_subs(self, string, sub_matches):
        """Count number of matches that match one of the sub groups.

        Arguments:
            string -- string on which to count number of substitution matches
            sub_matches -- iterable of group names and indices indicating which
                match groups are actual substitutions (all groups are
                considered as such if set to None)
        """
        subs = 0
        for match in self.finditer(string, False):
            for match_group in sub_matches:
                if match[match_group] is not None:
                    subs += 1
                    break
        return subs


class MetaRule:
    r"""Text substitution rule.

    Sub-classes must specify the class to use for pattern matching.

    The text substitution rule is composed of a regular expression and a
    replacement specification. The replacement can be specified as:
        1. A string or a function (see documentation of sub function in re
           module); or
        2. A class of function objects: the class is instantiated before being
           fed to the sub or subn method. The function object can then vary the
           replacement based on the matching order.

    The rule can be iterative or not. If iterative, it is applied until it no
    longer matches; if not it is applied only once. Iterative rules are for
    instance useful for the \footnote rule, which moves the footnote text to
    the end of the paragraph and can only move one at a time.

    Class methods:
        __init_subclass__ -- subclass initializer

    Child class attributes:
        Pattern -- class used internally for pattern matching

    Properties (read-only):
        pattern -- underlying search pattern
        iterative -- Boolean indicating if rule must be applied repeatedly
            until pattern no longer matches

    Attributes:
        _pattern, _iterative -- storage for pattern and iterative property
            values
        _sub_matches -- iterable of group names and indices indicating which
            match groups represent actual substitutions
        _compact -- unwrapped string representation of replacement string

    Methods:
        __init__ -- initializer
        __repr__ -- return printable representation
        sub -- perform substitution
        subn -- perform substitution and return number of substitutions done
        _replacement -- return replacement specification for use in sub/subn
    """

    def __init_subclass__(cls, Pattern, **kwargs):
        """Specify class-level attributes.

        Argument:
            Pattern -- class used internally for pattern matching
        """
        super().__init_subclass__(**kwargs)
        cls.Pattern = Pattern

    def __init__(self, pattern, replacement, *, iterative=False, compact=None,
                 file=None, line=None, scope=None, sub_matches=None):
        """Initialize text substitution rule.

        Arguments:
            pattern -- search pattern
            replacement -- replacement specification

        Keyword-only arguments:
            iterative -- Boolean indicating if rule should be applied
                repeatedly until pattern no longer matches
            compact -- compact representation of replacement string (set to
                replacement string if None)
            file, line, scope -- custom values for file, line number and scope
            sub_matches -- iterable of group names and indices indicating which
                match groups represent actual substitutions (all groups are
                considered as such if set to None)
        """
        Rule = type(self)
        self._sub_matches = sub_matches
        self._pattern = Rule.Pattern(pattern, user=self, stack_index=2,
                                     file=file, line=line, scope=scope)
        self._iterative = iterative
        if inspect.isclass(replacement):
            self._replacement = replacement
        else:
            self._replacement = lambda: replacement
        self._compact = replacement if compact is None else compact
        if _pattern_logger.isEnabledFor(logging.DEBUG):
            message = ('%s, line %i, %s:\n%r\n'
                       % (self._pattern.file, self._pattern.line,
                          self._pattern.scope, self))
            message += '-' * 80 + '\n'
            message += self._pattern._compiled.pattern
            if not message.endswith('\n'):
                message += '\n'
            message += '=' * 80
            _pattern_logger.debug(message)

    def __repr__(self):
        """Return official string representation."""
        args = [_quote(self._pattern._compact), _quote(self._compact)]
        if self._iterative:
            args.append('iterative=True')
        string = "%s(%s)" % (type(self).__name__, ', '.join(args))
        return string

    @property
    def pattern(self):
        """Underlying search pattern."""
        return self._pattern

    @property
    def iterative(self):
        """Whether to apply rule iteratively."""
        return self._iterative

    def sub(self, string, steps=False, **kwargs):
        """Apply substitution rule to string.

        Arguments:
            string -- string on which to apply the substitution rule
            steps -- whether to log text after applying rule
            kwargs -- other keyword arguments are passed to replacement
                function

        Returns:
            string with substitutions performed
        """
        return self.subn(string, steps, **kwargs)[0]

    def subn(self, string, steps=False, **kwargs):
        """Apply substitution rule to string.

        Arguments:
            string -- string on which to apply the substitution rule
            steps -- whether to log text after applying rule
            kwargs -- other keyword arguments are passed to replacement
                function

        Returns:
            2-tuple: string with substitutions performed and number of
            substitutions
        """
        Rule = type(self)
        try:
            nsubs_total = 0  # Total number of subs over all iterations
            iteration = 0
            while True:
                replacement = self._replacement()
                if callable(replacement):
                    replacement = ft.partial(replacement, **kwargs)
                string, nsubs = self._pattern.subn(replacement, string,
                                                   self._sub_matches)
                nsubs_total += nsubs
                iteration += 1
                if (steps and nsubs > 0
                        and _step_logger.isEnabledFor(logging.DEBUG)):
                    message = ('%s, line %i, %s:\n%r\n'
                               % (self._pattern.file, self._pattern.line,
                                  self._pattern.scope, self))
                    if self._iterative:
                        message += 'Iteration: %i\n' % iteration
                    message += 'Substitutions: %i\n' % nsubs
                    message += '-' * 80 + '\n'
                    message += string
                    message += '=' * 80
                    _step_logger.debug(message)
                if not self._iterative or nsubs == 0:
                    break
            return string, nsubs_total
        except (Rule.Pattern.re_module.error, IndexError) as err:
            if getattr(err, 'colno', None) is None:
                _misc_logger.error('Error in replacement string '
                                   '(%s, line %i, %s): %s\n%r',
                                   self._pattern.file, self._pattern.line,
                                   self._pattern.scope, err, self)
            else:
                spaces = err.colno - 1
                _misc_logger.error(
                    'Error in replacement string '
                    '(%s, line %i, %s): %s\n%s\n%s\n%s',
                    self._pattern.file, self._pattern.line,
                    self._pattern.scope, err,
                    err.pattern[0:err.pos],
                    '-' * spaces + '|',
                    ' ' * spaces + err.pattern[err.pos:])
            raise RegularExpressionError() from err


class MetaRuleList(list):
    """List of Rule instances.

    Sub-classes must specify the rule class to provide to rule functions.

    MetaRuleList inherits from the standard Python list class. It also includes
    additional attributes and methods to allow it to be used in place of a Rule
    object. Similarly to the Rule class, its instances can be iterative or not.
    If iterative, the list of rules is applied until none of them match.

    Class methods:
        __init_subclass__ -- subclass initializer

    Child class attributes:
        Rule -- rule class provided to rule functions

    Properties (read-only):
        iterative -- Boolean indicating if rule list must be applied repeatedly
            until pattern no longer matches

    Attributes:
        _iterative -- storage for iterative property value

    Methods:
        sub -- perform substitution for all rules in the list
        subn -- perform substitution for all rules in the list and return
            number of substitutions done
    """

    def __init_subclass__(cls, Rule, **kwargs):
        """Specify class-level attributes.

        Argument:
            Rule -- rule class provided to rule functions
        """
        super().__init_subclass__(**kwargs)
        cls.Rule = Rule

    def __init__(self, iterable=None, *, iterative=False):
        """Initialize text substitution rule.

        Arguments:
            iterable -- iterable over Rule instances

        Keyword-only arguments:
            iterative -- Boolean indicating if rule list must be applied
                repeatedly until pattern no longer matches
        """
        self._iterative = iterative
        super().__init__([] if iterable is None else iterable)

    @property
    def iterative(self):
        """Whether to apply rule list iteratively."""
        return self._iterative

    def sub(self, string, steps=False, **kwargs):
        """Apply substitution rules to string.

        Arguments:
            string -- string on which to apply the substitution rules
            steps -- whether to log text after applying each rule
            kwargs -- other keyword arguments are passed to replacement
                functions

        Returns:
            string with substitutions performed
        """
        return self.subn(string, steps, **kwargs)[0]

    def subn(self, string, steps=False, **kwargs):
        """Apply substitution rules to string.

        Arguments:
            string -- string on which to apply the substitution rules
            steps -- whether to log text after applying each rule
            kwargs -- other keyword arguments are passed to replacement
                functions

        Returns:
            2-tuple: string with substitutions performed and number of
                substitutions
        """
        nsubs_total = 0  # Total number of substitutions over all iterations
        while True:
            nsubs_first = 0  # Number of subs from first rule of iteration
            nsubs_other = 0  # Number of subs from other rules of iteration
            first_iter = False  # Is first rule iterative?
            first = True
            for rule in self:
                (string, nsubs) = rule.subn(string, steps, **kwargs)
                if first:
                    nsubs_first = nsubs
                    first_iter = rule.iterative
                    first = False
                else:
                    nsubs_other += nsubs
            nsubs_total += nsubs_first + nsubs_other
            # Third stopping criterion stops the iteration if the first rule is
            # iterative and the subsequent rules did not match. Without this
            # criterion, the outer_main rules in the list of rules returned by
            # the _select_rules function may sometimes be applied an extra time
            # unnecessarily.
            if (not self._iterative
                    or nsubs_first + nsubs_other == 0
                    or first_iter and nsubs_other == 0):
                break
        return string, nsubs_total


class Timer:
    """Context manager to time and count execution of arbitrary code.

    On Windows, measures clock time; on other platforms measures CPU time. This
    is done because the resolution of process_time function is too low on
    Windows; it also corresponds to the difference in definition of clock
    function.

    Methods:
        __init__ -- initializer
        __enter__ -- enter runtime context: start timing
        __exit__ -- exit runtime context: stop timing

    Properties (read-only):
        count -- number of times that context has been entered
        time -- execution time of code within context

    Attributes:
        _count, _time -- storage for count and time property values
    """

    def __init__(self):
        """Initialize timer."""
        self._count = 0
        self._time = 0

    def __enter__(self):
        """Start timing."""
        self._count += 1
        if platform.system() == 'Windows':
            self._start = time.perf_counter()
        else:
            self._start = time.process_time()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Stop timing."""
        if platform.system() == 'Windows':
            self._time += time.perf_counter() - self._start
        else:
            self._time += time.process_time() - self._start

    @property
    def count(self):
        """Number of times that contact has been entered."""
        return self._count

    @property
    def time(self):
        """Execution time of code within context."""
        return self._time


class CatastrophicBacktracking(Exception):
    """Suspected catastrophic backtracking in regular expression.

    Methods:
        __init__: initializer
    """

    def __init__(self, pattern_or_rule):
        """Initialize exception.

        Arguments:
            pattern_or_rule -- suspect pattern or rule
        """
        if isinstance(pattern_or_rule, MetaPattern):
            name = 'pattern'
            pattern = pattern_or_rule
        else:
            name = 'rule'
            pattern = pattern_or_rule._pattern
        message = ('The following %s exceeded the timeout of %s seconds, '
                   'which led to the interruption of the extraction:\n'
                   % (name, next(iter(pattern._timeout.values()))))
        message += 'File: %s\n' % pattern.file
        message += 'Line: %s\n' % pattern.line
        if pattern.scope != '':
            message += 'Scope: %s\n' % pattern.scope
        message += 'Object: %r\n' % pattern_or_rule
        message += textwrap.fill(textwrap.dedent("""\
                   Unless the issue is resolved by increasing the timeout value
                   slightly or external factors were reducing the computer's
                   performance during the extraction, the regular expression
                   pattern should be reviewed for sources of catastrophic
                   backtracking."""), width=1000)
        super().__init__(message)


class Interruption(Exception):
    """Extraction interrupted by user."""


class RegularExpressionError(Exception):
    """Extraction interrupted by regular expression error."""


def create_classes(re_module, timeout, interruption):
    """Create pattern and rule classes.

    The BasePattern, BaseRule and BaseRuleList classes returned by the class
    provide a custom interface to the regular expression engine.

    Arguments:
        re_module -- regular expression module
        timeout -- timeout for pattern matching with third-party regex module
        interruption -- event originating from the main thread indicating that
            the extraction thread must terminate

    Returns:
        3-tuple: BasePattern, BaseRule and BaseRuleList classes
    """
    class BasePattern(MetaPattern, re_module=re_module, timeout=timeout,
                      interruption=interruption):
        """Pattern class for non-customized regular expressions."""

    class BaseRule(MetaRule, Pattern=BasePattern):
        """Rule class for non-customized regular expressions."""

    class BaseRuleList(MetaRuleList, Rule=BaseRule):
        """Rule list class for non-customized regular expressions."""

    return BasePattern, BaseRule, BaseRuleList


# The following elements are internal elements of the module.


def _quote(string):
    """Return string enclosed in quotes.

    The function first tries to select quotes that do not appear in the string.
    For triple quotes, it also checks to make sure that the string does not end
    in the corresponding individual quote. If successful, the function formats
    the string as a raw string surrounded by the selected quotes and prepends
    it with 'r' if it contains backslashes. If not successful, it formats it as
    a non-raw string---surrounding it in single quotes, and escaping both
    backslashes and single quotes. For callable non-string objects, it returns
    '<function>'; for other non-strings, it returns its official string
    representation.

    Argument:
        string -- string that must be quoted

    Returns:
        string enclosed in properly selected quotes (and prepended with r if
            appropriate)
    """
    if isinstance(string, str):
        raw = 'r' if '\\' in string else ''
        for mark in ["'", '"', '"""', "'''"]:
            if mark not in string and len(string) and string[-1] != mark[0]:
                return ''.join((raw, mark, string, mark))
        enclosed = "'%s'" % string.replace('\\', '\\\\').replace("'", r"\'")
    elif callable(string):
        enclosed = '<function>'
    else:
        enclosed = repr(string)
    return enclosed
