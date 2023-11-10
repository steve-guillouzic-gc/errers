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

The create_classes function of the latex module returns Pattern, Rule and
RuleList classes, which provide latex-specific pattern elements (such as %c and
%n). See documentation of LaTeXMixIn class for more information.

Metaclasses:
    MetaBrackets -- function object providing bracket pair matching for
        Pattern instances
    LaTeXMixin -- regular expression pattern extended for matching LaTeX code
    KeyValueMixin -- provide class method returning rule to extract key-value
        parameters

Function:
    create_classes -- create classes for patterns, rules and rule lists

The following elements are internal elements of the module.

Constants:
    _TEMPLATE_CRS_RE -- template for %c, %r and %s search patterns (re
        module)
    _TEMPLATE_CRS_REGEX -- template for %c, %r and %s search patterns (regex
        module)
    _TEMPLATE_C_RE -- template for %C search pattern (re module)
    _TEMPLATE_C_REGEX -- template for %C search pattern (regex module)
"""

__all__ = ['create_classes']

import string
import textwrap

from errers._engine import base, plain

# Constants: templates for regex module
_TEMPLATE_CRS_REGEX = string.Template(textwrap.dedent(r"""
                          # $name-BRACKET ARGUMENT
    (?>                   # Atomic non-capt group for quantifiers
        %n                # Drop white space (one \n max)
        $ob               # Opening bracket
            (?P<$B1>      # Start capturing group
                (?:       # Non-capt group for alternative
                    $nb++
                                     # Non-brackets
                    |                # Or
                    (?:              # Balanced brackets
                        $ob          # Opening bracket
                            (?&$B1)  # Recursive pattern
                        $cb          # Closing bracket
                    )
                )*+       # Capture as much as possible
            )             # End capturing group
        $cb               # Closing bracket
    )                     # End non-capt group
    """))
_TEMPLATE_C_REGEX = string.Template(textwrap.dedent(r"""
                             # $name-BRACKET ARGUMENT
    (?>                      # Atomic non-capt group for quantifiers
        %n                   # Drop white space (one \n max)
        (?P<${B1}_ob>$ob)?+  # Opening bracket (optional)
            (?P<$B1>             # Start capturing group
                (?<=$ob)         # Case 1: bracketed content
                (?:                # Non-capt group for alternative
                    $nb++
                                     # Non-brackets
                    |                # Or
                    (?:              # Balanced brackets
                        $ob          # Opening bracket
                            (?&$B1)  # Recursive pattern
                        $cb          # Closing bracket
                    )
                )*+                # Capture as much as possible
                |                # Or
                (?<!$ob)         # Case 2: non-bracketed LaTeX macro
                %m
                |                # Or
                (?<!$ob)         # Case 3: non-bracketed character
                (?![\ \t\n])$nb
            )                # End capturing group
        (?(${B1}_ob)$cb)     # Closing bracket (case 1 only)
    )                        # End non-capt group
    """))

# Constants: templates for re module
_TEMPLATE_CRS_RE = string.Template(textwrap.dedent(r"""
                                # $name-BRACKET ARGUMENT
    (?:                         # Non-capt group for quantifiers
        %n                      # Drop white space (one \n max)
        $ob                     # Opening bracket
            (?=                 # Lookahead to ensure atomicity
                (?P<$B1>        # Start capturing group
                    (?:         # Non-capt. group for alternative:
                        $nb++
                                       # Non-brackets
                        |              # Or
                        (?:            # Balanced brackets
                            $ob        # Opening bracket
                                $nb*+
                                       # No bracket
                            $cb        # Closing bracket
                        )
                    )*+         # Capture as much as possible
                )               # End capturing group
            )                   #
            (?P=$B1)            # Consume text matched by lookahead
        $cb                     # Closing bracket
    )                           # End non-capt group
    """))
_TEMPLATE_C_RE = string.Template(textwrap.dedent(r"""
                                # $name-BRACKET ARGUMENT
    (?:                         # Non-capt group for quantifiers
        %n                      # Drop white space (one \n max)
        (?P<${B1}_ob>$ob)?+     # Opening bracket (optional)
            (?=                 # Lookahead to ensure atomicity
                (?P<$B1>        # Start capturing group
                    (?<=$ob)          # Case 1: bracketed content
                    (?:                 # Non-capt. group for alternative:
                        $nb++
                                        # Non-brackets
                        |               # Or
                        (?:             # Balanced brackets
                            $ob         # Opening bracket
                                $nb*+
                                        # No bracket
                            $cb         # Closing bracket
                        )
                    )*+                 # Capture as much as possible
                    |                # Or
                    (?<!$ob)         # Case 2: non-bracketed LaTeX macro
                    %m
                    |                # Or
                    (?<!$ob)         # Case 3: non-bracketed character
                    (?![\ \t\n])$nb
                )               # End capturing group
            )                   #
            (?P=$B1)            # Consume text matched by lookahead
        (?(${B1}_ob)$cb)        # Closing bracket (case 1 only)
    )                           # End non-capt group
    """))


class MetaBrackets:
    """Function object providing bracket pair matching for Pattern instances.

    Sub-classes must specify which rule list class to use internally.

    The class provides a function object that replaces %c, %r and %s in regular
    expressions with patterns that match pairs of curly, round and square
    brackets, respectively. The function object also replaces %C with a pattern
    that matches a pair of curly braces or a LaTeX command or a single
    character. The matching is described in more detail in the LaTeXMixin
    documentation. The function object maintains an index of %c/%C, %r and %s
    patterns in order to name the capturing group for the bracketed content,
    for use in a recursive pattern. (The recursive pattern is what enables the
    use of balanced brackets in bracketed content with the regex module.) The
    name of a capturing group can be specified manually by appending an empty
    named group to the %c, %C, %s or %s placeholder, such as in
    '%C(?P<custom_name>)'; the index is not incremented for such placeholders.

    Normally, capturing groups in an alternation---such as in (a)|(b)---have
    the same group number. However, because the capturing groups in the %c/%C,
    %r and %s are named, they always have different group numbers.

    Class methods:
        __init_subclass__ -- subclass initializer, which includes defining
            internal rules

    Child class attributes:
        _template_crs -- template for %c, %r and %s search patterns
        _template_C -- template for %C search pattern
        _align -- rule to align comments in Brackets rule
        _curly -- format values for curly brackets
        _round -- format values for round brackets
        _square -- format values for square brackets

    Methods:
        __init__ -- initializer
        __call__ -- function call

    Attributes:
        _indices -- index counters for bracket pairs in search pattern
    """

    # ob = opening bracket; cb = closing bracket; nb = neither bracket
    # not_esc = not escaped (only need to check for one backslash because \\
    # is converted to newline early in setup rule function)
    not_esc = r'(?<!\\)'
    _curly = {'name': 'CURLY',
              'ob': f'{not_esc}{{',
              'cb': f'{not_esc}}}'}
    _round = {'name': 'ROUND',
              'ob': fr'{not_esc}\(',
              'cb': fr'{not_esc}\)'}
    _square = {'name': 'SQUARE',
               'ob': fr'{not_esc}\[',
               'cb': fr'{not_esc}\]'}
    for bracket in (_curly, _round, _square):
        bracket['nb'] = f'(?>(?!{bracket["ob"]})(?!{bracket["cb"]})(?s:.))'

    def __init_subclass__(cls, RuleList, **kwargs):
        """Specify class-level attributes.

        Argument:
            RuleList -- class to use for rule lists in this class
        """
        super().__init_subclass__(**kwargs)
        Rule = RuleList.Rule
        # Pattern for re uses lookahead to ensure atomicity, because it does
        # not support atomic groups and possessive quantifiers.
        if Rule.Pattern.re_module.__name__ == 'regex':
            cls._template_crs = _TEMPLATE_CRS_REGEX
            cls._template_C = _TEMPLATE_C_REGEX
            # Parameters for _align rules below
            shift = 46
            n_space = 38
        else:
            cls._template_crs = _TEMPLATE_CRS_RE
            cls._template_C = _TEMPLATE_C_RE
            # Parameters for _align rules below
            shift = 41
            n_space = 32
        # Rules to align comments in Bracket patterns, to improve formatting in
        # syntax error messages. The second rule leaves room for the expanded
        # meaning of '%n', which is interpreted literally here because plain
        # rules do not expand it.
        Rule = RuleList.Rule
        cls._align = RuleList([
            Rule(r'^([^%#\n]+)(\#.*)',
                 lambda m: m[1][:shift] + ' ' * (shift - len(m[1])) + m[2],
                 scope=cls.__name__),
            Rule(r'^(\ +%n)\ +(\#.*)',
                 lambda m: m[1] + ' ' * (shift - len(m[1]) - n_space) + m[2],
                 scope=cls.__name__)
        ])

    def __init__(self, **kwargs):
        """Initialize function object."""
        super().__init__(**kwargs)
        self._indices = {'c': 0, 'r': 0, 's': 0}

    def __call__(self, match):
        """Call function object.

        Argument:
            match -- match object provided by re_module.sub or re_module.subn
        """
        cls = type(self)
        brackets = match[1]
        name = match[2]
        template = cls._template_C if brackets == 'C' else cls._template_crs
        brackets = brackets.lower()
        values = {'c': cls._curly,
                  'r': cls._round,
                  's': cls._square}[brackets]
        if not name:
            self._indices[brackets] += 1
            name = brackets + str(self._indices[brackets])
        pattern = template.substitute(values, B1=name)
        return cls._align.sub(pattern)


class LaTeXMixin:
    r"""Regular expression pattern extended for matching LaTeX code.

    This is a mixin class. Sub-classes must specify the class to use for
    internal rule lists.

    Six changes are made to the pattern:

    1. Three negative lookbehinds are added before the pattern if it starts
    with a command name. The first one ensures that the matched text is not
    just a word or character following a newline (\\); it contains an inner
    negative lookbehind to allow matching commands that immediately follow
    newlines, such as \\\emph{abc}. The second lookbehind prevents matching
    command names in definitions using \newcommand, \renewcommand and
    \providecommand. Asterisks are stripped when files are read, and
    \renewcommand and \providecommand are converted to \newcommand. Therefore,
    the lookbehind pattern only needs to make sure that the command is not the
    first argument to \newcommand. The third lookbehind is similar to the
    second one, but for commands defined using \def, \edef, \gdef and \xdef.

    2. A negative lookahead is added after alphabetic commands that take no
    arguments to ensure that they don't match the beginning of longer commands,
    for instance \abc vs \abcd. The rule also swallows any white space
    following the command (including one newline, if the next line is not
    empty).

    3. The %c, %r and %s strings are replaced with patterns that match pairs of
    curly, round and square brackets with arbitrary content in between. The
    only restriction on the content is that it must not contain unbalanced
    brackets of the type being matched. A %c, %r or %s may be made optional by
    following it with a question mark (?) in the search pattern. Each %c,
    %r and %s counts as a capturing group, and the bracketed content can be
    inserted into replacement strings using named groups
    labelled according to the type of bracket (\g<c1> = content of first pair
    of curly brackets in pattern, \g<s1> = content of first pair of square
    brackets, etc.) Referring to capturing groups by indices (\1, \2, etc.) is
    not supported because (a) the pattern for the %C placeholder uses two
    capturing groups and (b) future bug fixes may require the introduction
    of additional capturing groups for any of the %c, %s, %r and %C
    placeholders. The name of a capturing group can be specified manually by
    appending an empty named group to the %c, %C, %s or %s placeholder (before
    the quantifier if applicable), such as in '%C(?P<myname>)'; the index is
    not incremented for such placeholders. White space before the opening
    bracket is dropped, as well as the one at the beginning and end of the
    bracketed content. With the standard re module, the patterns only match
    pairs of braces that contain no more than one additional level of brackets
    of the type being matched.

    4. The %C string is replaced by a pattern that matches a pair of curly
    braces with arbitrary content, a non-bracketed LaTeX command or a
    non-bracketed character. It is otherwise similar to %c, and its group names
    also start with a lowercase C (such as in \g<c1>). The pattern for the %C
    placeholder currently uses two capturing groups: the first one captures the
    opening bracket, if present, and the second one captures the command
    argument. However, this could be changed in future point releases to
    address bugs, and it should not be relied on. It is better to refer to
    capturing groups by name when using the %c, %s, %r and %C placeholders.

    5. The %m string is replaced by a pattern that matches LaTeX command (or
    "macro") name.

    6. The %h, %n and %w strings are replaced with patterns that match optional
    white space: %h matches an arbitrary amount of horizontal white space
    (space or tab), including none; %n is similar to %h, but may also include
    at most one non-commented newline character (and an arbitrary number of
    lines composed solely of LaTeX comments); and %w is similar to %n, but may
    include an arbitrary number of newline characters instead of zero or one.
    Contrary to the % strings from point 3, %h, %n and %w are not capturing
    groups.

    7. Opening curly brackets that immediately precede letters d, e, i and s
    are escaped in order to deactivate fuzzy matching in the regex module.

    Class methods:
        __init_subclass__ -- subclass initializer, which includes defining
            internal rules

    Child class attribute:
        _latex -- rules implementing LaTeX extensions to regular expressions

    Methods:
        __init__ -- initializer
    """

    def __init_subclass__(cls, InnerRuleList, Brackets, **kwargs):
        """Specify class-level attributes.

        Argument:
            InnerRuleList -- class to use for rule lists in this class
            Brackets -- class to use for bracket-matching pattern
        """
        super().__init_subclass__(InnerRuleList=InnerRuleList, **kwargs)
        Rule = InnerRuleList.Rule

        # Define rule that escapes backslash characters not followed by a
        # digit, to simplify specification of LaTeX rules below.
        escape = Rule(r'\\(?![0-9])', r'\\\\', scope=cls.__name__)

        # Replacement text for lookbehind rule.
        rep_lookbehind = escape.sub(textwrap.dedent(r"""
                                # NEGATIVE LOOK-BEHIND PATTERNS
             (?<!               # FIRST:
                 (?<!\\)        # Can follow pair of backslashes,
                 \\             # but not a unique one.
             )                  #
             (?<!               # SECOND:
                 \\newcommand{  # Must not be first argument
             )                  # of command definition (\newcommand).
             (?<!               # THIRD:
                 \\def{         # Must not be first argument
             )                  # of command definition (\def).
             \\"""))

        # Matching patterns and replacement text for lookahead rules. Lookahead
        # is used in pat_macro_name to ensure atomicity, because re module
        # prior to 3.11.5 did not properly support atomic groups and possessive
        # quantifiers. (The same pattern is used for all cases.)
        #
        # Pattern for alphabetic command name definitions in rules.
        pat_macro_name = textwrap.dedent(r"""
                                         # MACRO NAME DEFINITION
            (?P<name>                    # Capturing group
                \\\\                     # Initial backslash
                (?:                      # Non-capt group for name elements
                    (?=                  # Lookahead to ensure atomicity
                        (?P<element>     # Capturing group for name element
                            (?:                # Non-capt group for alternation
                                [a-zA-Z]++           # Sequence of letters
                                |                    # Or
                                \[[a-zA-Z]++\]       # Letter set
                                |                    # Or
                                \([a-zA-Z\|]++\)     # Capturing alternation
                                |                    # Or
                                \(\?:[a-zA-Z\|]++\)  # Non-capt alternation
                            )
                            (?:                      # Optional
                                \?                   # Greedy or
                                \+?+                 # possessive quantifier.
                            )?+
                        )
                    )
                    (?P=element)      # Consume text matched by lookahead
                )++
            )
            """)
        # Pattern for optional asterisk
        pat_asterisk = textwrap.dedent(r"""
                                     # OPTIONAL ASTERISK
            (?P<asterisk>            # Capturing group
                \\\*\?               # asterisk with greedy or
                \+?+                 # possessive quantifier.
            )?+
            """)
        # Pattern for optional arguments that precede a curly-bracket argument.
        pat_args = textwrap.dedent(r"""
                             # ONLY OPTIONAL ARGUMENTS
            (?P<args>        # Capturing group
                (?:          # Non-capturing group for repetition
                    %[rs]\?  # Optional square- or round-bracket argument
                )*+          # As many as possible
                (?=%C)       # Immediately before a %C argument
            )
            """)
        # Replacement text for argument-less commands with alphabetic names
        # prevents matching partial command names and captures trailing space.
        rep_lookahead_no_arg = textwrap.dedent(r"""
            \g<name>\g<asterisk>
                              # NEGATIVE LOOK-AHEAD PATTERNS (NO ARGUMENT)
            (?![a-zA-Z])      # Command must not be followed by letter.
            (?:%n(?!\\n)|%h)  # Subsequent white space removed.
            """)
        # Replacement text for commands with mandatory arguments and alphabetic
        # names prevents matching partial command names. This is required
        # because %C can match single arbitrary characters.
        rep_lookahead_arg = textwrap.dedent(r"""
            \g<name>\g<asterisk>\g<args>
                             # NEGATIVE LOOK-AHEAD PATTERN (WITH ARGUMENT)
            (?![a-zA-Z])     # Command must not be followed by letter.
            """)

        # Pattern matching LaTeX commands that start with backslash (no dedent
        # so it lines up better in curly bracket pattern).
        rep_macro_name = escape.sub(r"""
                                  # COMMAND NAME
                \\                # Initial backslash
                (?:               # Non-capturing group for alternative
                    [a-zA-Z]++    # Letters
                    |             # Or
                    \s            # Single space
                    |             # Or
                    .             # Any other character
                )                 # End non-capt group
                """)

        # Define rule list
        cls._latex = InnerRuleList([
            Rule(r'\A\\\\(?=.)',
                 rep_lookbehind, compact=cls._uncomment.sub(rep_lookbehind),
                 scope=cls.__name__),
            Rule(pat_macro_name + pat_asterisk + r'\Z',
                 rep_lookahead_no_arg,
                 compact=cls._uncomment.sub(rep_lookahead_no_arg),
                 scope=cls.__name__),
            Rule(pat_macro_name + pat_asterisk + pat_args,
                 rep_lookahead_arg,
                 compact=cls._uncomment.sub(rep_lookahead_arg),
                 scope=cls.__name__),
            Rule('%([Ccrs])'               # Bracket specifier
                 r'(?:\(\?P<(\w++)>\))?',  # Optional group name
                 Brackets, scope=cls.__name__),
            Rule('%m',
                 rep_macro_name,
                 compact=cls._uncomment.sub(rep_macro_name),
                 scope=cls.__name__),
            Rule('%n', escape.sub(r'%h\n?+%h(?:%.*+\n%h)*+'),
                 scope=cls.__name__),
            Rule('%h', escape.sub(r'[\ \t]*+'), scope=cls.__name__),
            Rule('%w', escape.sub(r'[\ \t\n]*+'), scope=cls.__name__),
            Rule(r'({[deis])', escape.sub(r'\\1'), scope=cls.__name__)
        ])

    def __init__(self, pattern, *, stack_index=1, **kwargs):
        """Initialize LaTeX-extended regular expression.

        Arguments:
            pattern -- high-level LaTeX pattern to be translated using _latex

        Keyword-only arguments:
            stack_index -- index of frame entry in stack for pattern or rule
                instantiator; sub-classes that define __init__ must increment
                stack_index by 1 and pass it on to the next __init__; __init__
                methods of rule classes should set it to 2
            file, line, scope -- custom values for file, line number and scope
        """
        cls = type(self)
        compact = cls._uncomment.sub(pattern)
        pattern = cls._latex.sub(pattern)
        super().__init__(pattern, compact=compact,
                         stack_index=stack_index + 1, **kwargs)


class KeyValueMixin:
    r"""Provide class method returning rule to extract key-value parameters

    This is a mixin class for Rule classes.

    Class method:
        key_value -- return rule to extract specific key-value parameter from
            LaTeX input string.
    """

    @classmethod
    def key_value(cls, key):
        """Return rule to extract key-value.

        Arguments:
            key -- key for which a value is sought

        Returns:
            rule
        """
        def value(raw):
            # Return content of balanced braces. Workaround for re module when
            # string contains more than two levels of braces.
            levels = 0
            for index, character in enumerate(raw):
                if character == '{':
                    levels += 1
                elif character == '}':
                    levels -= 1
                if levels == 0:
                    return raw[1:index]
            return ''

        template = string.Template(r"""
            (?s)                        # Period matches \n too.
            \A                          # From start of string,
            (?:(?!                      # skip everything
                (?<![a-zA-Z])           # before
                (?:$key)%n=).           # key.
            )*+
            (?:                         # If present, match
                (?:$key)%n=%n           # key and capture value:
                (?:
                    %c                      # content of curly braces,
                    |
                    (?P<unbracketed>
                        (?!{)
                        (?:                 # everything
                            (?!             # until next comma or end of string
                                [\ \t\n]*+  # (while ignoring spaces),
                                (?:,|\Z)
                            ).
                        )*+
                    )
                    |                        # or
                    (?P<bracketed>(?={).*+)  # 3+ levels of braces with re
                )                            # module.
            )?
            .*+                         # Skip everything else.
            """)
        return cls(template.substitute(key=key),
                   lambda m: (m['c1'] or m['unbracketed']
                              or value(m['bracketed'] or '')))


def create_classes(re_module, timeout, interruption=None):
    """Create pattern and rule classes.

    The Pattern, Rule and RuleList classes returned by this function provide
    latex-specific pattern elements (such as %c and %n). See documentation of
    errers.rules sub-package for more information.

    Arguments:
        re_module -- regular expression module
        timeout -- timeout for pattern matching with third-party regex module
        interruption -- threading event originating from main thread that, when
            set, causes the extraction thread to terminate (only applicable to
            multithreaded setups)

    Returns:
        3-tuple: Pattern, Rule and RuleList classes
    """
    PlainPattern, _, PlainRuleList \
        = plain.create_classes(re_module, timeout, interruption)

    class Brackets(MetaBrackets, RuleList=PlainRuleList):
        """Function object for bracket pair matching."""

    class Pattern(LaTeXMixin, plain.CompactMixin, plain.NonAtomicMixin,
                  base.MetaPattern,
                  InnerRuleList=PlainRuleList, Brackets=Brackets,
                  re_module=re_module, timeout=timeout,
                  interruption=interruption,
                  instances=PlainPattern.instances):
        """Pattern class for LaTeX matching patterns."""

    class Rule(KeyValueMixin, base.MetaRule, Pattern=Pattern):
        """Rule class for LaTeX matching patterns."""

    class RuleList(base.MetaRuleList, Rule=Rule):
        """Rule list class for LaTeX matching patterns."""

    return Pattern, Rule, RuleList
