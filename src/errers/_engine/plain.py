# coding=utf-8
#
# SPDX-FileCopyrightText: 2023 His Majesty in Right of Canada
#
# SPDX-License-Identifier: LicenseRef-MIT-DND
#
# This file is part of the ERRERS package.

"""ERRERS: custom interface to regular expressions (plain rules)

All elements of this module are implementation details that may change in
non-backward-compatible ways between minor or micro version releases.

The create_classes function of plain module returns PlainPattern, PlainRule and
PlainRuleList classes, which are similar to the ones from the base module aside
from the fact that they remove comments and spaces from verbose regular
expressions when printing them and that they remove atomic operators and
possessive quantifiers when used with the standard re module from Python
versions prior to 3.11.5.

Metaclasses:
    CompactMixin -- rules for removing comments and spaces from verbose regular
        expressions
    NonAtomicMixin -- base rules for removing atomic groups and possessive
        quantifiers from regular expressions with standard re module prior to
        version 3.11.5

Function:
    create_classes -- create classes for patterns, rules and rule lists
"""

__all__ = ['create_classes']

import sys

from errers._engine import base


class CompactMixin:
    r"""Rules for removing comments and spaces from regular expressions.

    This is a mixin class. Sub-classes must specify the class to use for
    internal rule lists.

    A compact representation that removes comments and white space from regular
    expressions is determined for display purposes-only.

    Class methods:
        __init_subclass__ -- subclass initializer, which includes defining
            internal rules

    Child class attribute:
        _uncomment -- rules to cleanup verbose regular expressions

    Methods:
        __init__ -- initializer
    """

    def __init_subclass__(cls, InnerRuleList, **kwargs):
        """Specify class-level attributes.

        Argument:
            InnerRuleList -- class to use for rule lists in this class
        """
        super().__init_subclass__(InnerRuleList=InnerRuleList, **kwargs)
        Rule = InnerRuleList.Rule

        # Define rules to make verbose patterns more compact. Spaces and
        # comments introduced by # are removed unless escaped by \. In
        # principle, # and spaces should be safe in [] too, but rules to keep
        # them would be more complicated and were not implemented.
        cls._uncomment = InnerRuleList([
            Rule(r'(?<!\\)\#.*', '', scope=cls.__name__),   # Comments
            Rule(r'(?<!\\)\ ', '', scope=cls.__name__),     # Spaces
            Rule(r'\n', '', scope=cls.__name__)             # Newlines
        ])

    def __init__(self, pattern, *, compact=None, stack_index=1, **kwargs):
        """Apply rules to pattern.

        Arguments:
            pattern -- regular expression pattern

        Keyword-only arguments:
            compact -- compact representation of pattern (set to pattern if
                None)
            stack_index -- index of frame entry in stack for pattern or rule
                instantiator; sub-classes that define __init__ must increment
                stack_index by 1 and pass it on to the next __init__; __init__
                methods of rule classes should set it to 2
            file, line, scope -- custom values for file, line number and scope
        """
        cls = type(self)
        if compact is None:
            compact = cls._uncomment.sub(pattern)
        super().__init__(pattern, compact=compact,
                         stack_index=stack_index + 1, **kwargs)


class NonAtomicMixin:
    r"""Rules for removing atomic groups and non-possessive quantifiers.

    This is a mixin class. Sub-classes must specify the class to use for
    internal rule lists.

    If using the standard re module with a Python version prior to 3.11.5,
    possessive quantifiers and atomic groups are respectively replaced by
    greedy quantifiers and non-capturing groups.

    Class methods:
        __init_subclass__ -- subclass initializer, which includes defining
            internal rules

    Child class attribute:
        _re -- rules replacing regex-specific constructs with ones compatible
            with the re module

    Methods:
        __init__ -- initializer
    """

    def __init_subclass__(cls, InnerRuleList, **kwargs):
        """Specify class-level attributes.

        Argument:
            InnerRuleList -- class to use for rule lists in this class
        """
        super().__init_subclass__(InnerRuleList=InnerRuleList, **kwargs)
        Rule = InnerRuleList.Rule

        # Define rules to replace possessive quantifiers and atomic groups by
        # greedy quantifiers and non-capturing groups, respectively, for the re
        # module prior to Python 3.11.5.
        cls._re = InnerRuleList([
            Rule(r'([+*?])\+', r'\1', scope=cls.__name__),
            Rule(r'\(\?>', '(?:', scope=cls.__name__)
        ])

    def __init__(self, pattern, *, stack_index=1, **kwargs):
        """Apply base rules to pattern.

        Arguments:
            pattern -- regular expression pattern

        Keyword-only arguments:
            compact -- compact representation of pattern (set to pattern if
                None)
            stack_index -- index of frame entry in stack for pattern or rule
                instantiator; sub-classes that define __init__ must increment
                stack_index by 1 and pass it on to the next __init__; __init__
                methods of rule classes should set it to 2
            file, line, scope -- custom values for file, line number and scope
        """
        cls = type(self)
        if cls.re_module.__name__ == 're' and sys.version_info < (3, 11, 5):
            pattern = cls._re.sub(pattern)
        super().__init__(pattern, stack_index=stack_index + 1, **kwargs)


def create_classes(re_module, timeout, interruption):
    """Create pattern and rule classes.

     The PlainPattern, PlainRule and PlainRuleList classes returned by this
     function:
        1. Remove comments and spaces from verbose regular expressions when
           printing them, and
        2. Replace atomic operators and possessive quantifiers with
           non-capturing groups and greedy operators, respectively, when used
           with the standard re module from Python versions prior to 3.11.5.

    Arguments:
        re_module -- regular expression module
        timeout -- timeout for pattern matching with third-party regex module
        interruption -- event originating from the main thread indicating that
            the extraction thread must terminate

    Returns:
        3-tuple: PlainPattern, PlainRule and PlainRuleList classes
    """
    BasePattern, _, BaseRuleList \
        = base.create_classes(re_module, timeout, interruption)

    class PlainPattern(CompactMixin, NonAtomicMixin, base.MetaPattern,
                       InnerRuleList=BaseRuleList,
                       re_module=re_module, timeout=timeout,
                       interruption=interruption,
                       instances=BasePattern.instances):
        """Pattern class for implementing LaTeX matching patterns."""

    class PlainRule(base.MetaRule, Pattern=PlainPattern):
        """Rule class for implementing LaTeX matching patterns."""

    class PlainRuleList(base.MetaRuleList, Rule=PlainRule):
        """Rule list class for implementing LaTeX matching patterns."""

    return PlainPattern, PlainRule, PlainRuleList
