# coding=utf-8
#
# SPDX-FileCopyrightText: 2023 His Majesty in Right of Canada
#
# SPDX-License-Identifier: LicenseRef-MIT-DND
#
# This file is part of the ERRERS package.

r"""Enhanced Review of Reports via Extraction using Rule-based Substitutions

ERRERS extracts text from LaTeX files. The extraction aims to reduce the number
of false positives when checking grammar and spelling with Microsoft Word or
other software. It is performed through the application of substitution rules
based on regular expressions. For instance, Rule(r'\\foo%C%C', r'\g<c1>') would
substitute each occurrence of a two-argument \foo command with the content of
its first argument. (More information about rule syntax can be found in the
documentation of the Pattern and Rule classes.) While there are core rules
applicable to all documents, additional rules are loaded as needed based on the
document class, as well as the packages and bibliography style used.

The ERRERS executable is called errers.exe on Microsoft Windows and errers on
other operating systems. It provides a Graphical User Interface (GUI), but it
can also be run from the command-line. Usage help for the Command-Line
Interface (CLI) can be obtained by typing "errers -h". The GUI is launched if
no input file is included on the command-line or if the --gui option is
specified.

Users can also call the extraction engine from their own applications using the
extract function, and they can experiment with creating their own patterns and
rules using the classes returned by the create_classes function. If desired,
they can obtain the rule lists for individual document classes, packages and
bibliography styles from the rule functions in the rules.standard module.

Additional rules can be defined locally by creating a rules/local.py file in
the directory where the errers package is installed. This file must contain
one or more functions returning RuleList objects, each such function being
called insertion, removal, setup, core, cleanup_braces, cleanup,
class_NAME_PHASE, package_NAME_PHASE or style_NAME_PHASE (with NAME a document
class, a package name or a bibliography style, respectively, and PHASE being
the extraction phase at which the rules are applied: insertion, removal, setup,
main or cleanup). When a rule function with the same name is present in both
rules.local and rules.standard, the rules from the local script are run first.

Rules are created automatically for LaTeX commands defined in the document
using \newcommand, \rewnewcommand, \providecommand, \def, \edef, \gdef and
\xdef, and they are applied with the rules from the rules.standard.core rule
function. If needed, rules can also be defined on a per-document basis by
including them in comments directly in the LaTeX document, and these rules are
run before those from rules.local and rules.standard.

Limitations:
    1. Rules for commands provided by a package are only loaded if the
       document includes a \usepackage command for that package or if the LaTeX
       log file is available in the same directory as the LaTeX document.
    2. Default rules are used to process environments and one-argument commands
       for which no explicit rule is specified to reduce the number of rules
       required. These default rules get confused when curly, round or square
       brackets follow a command, as the bracketed content is mistakenly
       interpreted as an additional argument. After \begin, it is removed with
       the rest of the \begin command. After one-argument commands, it prevents
       the application of the default rule. These problems can be mitigated by:
           a) Creating an explicit rule for the affected command or
              environment;
           b) Using an explicit space (backslash-space: "\ ") between the last
              argument of the command and the following bracketed content; or
           c) Wrapping the command in curly brackets.
    3. When running the re module, using \footnote, \footnotetext or
       \marginpar in a \newcommand, \renewcommand or \providecommand leads to
       stray parentheses being left in the document when there are more than
       two levels of curly braces involved. This issue does not arise with the
       regex module, because rules for command definitions are always applied
       before footnote and marginpar rules irrespective of the number of brace
       levels. The problem with the re module can be mitigated by placing the
       command definition between \makeatletter and \makeatother, although this
       prevents the automatic creation of an extraction rule for that command.

Sub-package:
    rules -- substitution rules used by extraction engine

Constants:
    SHORTNAME -- short name of application
    LONGNAME -- long name of application
    TIMEOUT -- default timeout for individual search patterns and
        substitution rules used as indication of catastrophic backtracking

Classes:
    Timer -- context manager to time and count execution of arbitrary code
    CatastrophicBacktracking -- exception raised when there is a suspected
        catastrophic backtracking in a regular expression
    Interruption -- exception raised when extraction is interrupted by user
    RegularExpressionError -- exception raised when there is a regular
        expression error

Functions:
    extract -- extract text from LaTeX file
    create_classes -- create classes for patterns, rules and rule lists

The following elements are implementation details that may change in
non-backward-compatible ways between minor or micro version releases.

Sub-package (internal):
    _engine -- extraction engine

Modules (internal):
    _app -- application that leverages extraction engine and is behind the CLI
        and GUI
    _cli -- command-line interface to application
    _gui -- graphical user interface to application
"""

__all__ = ['SHORTNAME', 'LONGNAME', 'Timer', 'CatastrophicBacktracking',
           'Interruption', 'RegularExpressionError', 'TIMEOUT', 'extract',
           'create_classes', 'rules']

# _cli is imported to help PyInstaller with dependency analysis
from errers._version import __version__
from errers._name import SHORTNAME, LONGNAME
import errers._cli
from errers._engine.base import (Timer, CatastrophicBacktracking,
                                 Interruption, RegularExpressionError)
from errers._engine.extractor import TIMEOUT, extract
from errers._engine.latex import create_classes
from errers import rules
