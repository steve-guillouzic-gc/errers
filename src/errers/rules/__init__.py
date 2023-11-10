# coding=utf-8
#
# SPDX-FileCopyrightText: 2023 His Majesty in Right of Canada
#
# SPDX-License-Identifier: LicenseRef-MIT-DND
#
# This file is part of the ERRERS package.

r"""ERRERS: substitution rules

Most rules are returned by rule functions defined in standard and (optionally)
local modules of this sub-package. Some are defined in the LaTeX document
itself. The name of a rule function indicates when its rules are applied. Rules
are applied in the following order (X stands for LaTeX class name, LaTeX
package name or BibTeX style name):
    1. Location rules (applied once at start of extraction; also applied
       individually to each file inserted into document using read_file
       function):
        a) Rules defined in LaTeX document for location phase;
        b) Functions class_X_location, package_X_location and style_X_location;
           and
        c) Function core_location;
    2. Insertion rules (applied once at start of extraction):
        a) Rules defined in LaTeX document for insertion phase;
        b) Functions class_X_insertion, package_X_insertion and
           style_X_insertion; and
        c) Function core_insertion;
    3. Removal rules (applied once at start of extraction):
        a) Rules defined in LaTeX document for removal phase;
        a) Functions class_X_removal, package_X_removal and style_X_removal;
           and
        b) Function core_removal;
    4. Miscellaneous setup rules (applied once at start of extraction):
        a) Rules defined in LaTeX document for setup phase;
        a) Functions class_X_setup, package_X_setup and style_X_setup; and
        b) Function core_setup;
    5. Main rules:
        a) Rules defined in LaTeX document for main phase;
        b) Functions class_X_main, package_X_main and style_X_main; and
        c) Function core (rules for most core LaTeX commands);
    6. Function core_cleanup_braces (rules for cleaning up braces and applying
       default rules for single-argument commands); and
    7. Remaining cleanup rules (final cleanup):
        a) Rules defined in LaTeX document for cleanup phase;
        a) Functions class_X_cleanup, package_X_cleanup and style_X_cleanup;
           and
        b) Function core_cleanup.
When regex module is used, rules are applied once in the order above, except
that step 1 is also applied to each file inserted into main document. When re
module is used, step 5 is applied iteratively until none of its rules match; if
any rule from step 6 matches, the process goes back to step 5.

In each of the seven phases above, local rules (if present) are applied before
standard rules, so they can override them or leverage them for part of the
processing. Similarly and for the same reasons, class, package and style rules
are applied before the core ones, and rules defined in the LaTeX document are
applied before those defined in the local and standard modules. Most rules are
applied at the main phase.

The purpose of each phase is as follows:
    1. Location: note down location (file and line number) of LaTeX command
       definitions for reporting when generating auto rules.
    2. Insertion: insert sub-documents, using for instance \include and
       \bibliography.
    3. Removal: remove parts of the document that do not generally need grammar
       and spell checking, but that could confuse the rest of the rules (such
       as equations and \verb commands).
    4. Setup: rules that only need to be run once even with re module or need
       to be done before the main rules.
    5. Main: most of the rules.
    6. Cleanup braces: remove pairs of curly braces that are not command
       arguments, and apply default rules for single-argument commands.
    7. Cleanup: process textual reserved characters, and remove extra spaces
       and newline characters.

A rule function takes a subset of ten keyword arguments (listed below) and
returns a RuleList object. Most rule functions in the standard rules module use
only the following two arguments:
    1. Rule -- class used to create extraction rules; and
    2. RuleList -- class used to group extraction rules.

Some rule functions also use the following argument:
    3. logger -- logging object for informational messages, warnings and
       errors.

Other arguments are more specialized and are unlikely to be needed for most
rule functions:
    4. auto -- whether to create rules dynamically for commands defined in
       LaTeX document using \newcommand, \renewcommand, \providecommand or
       similar commands (used mainly by core_main rule function);
    5. default -- whether to create default rules for LaTeX commands that take
       one or no argument, and for unknown LaTeX environments (used only by
       core_cleanup_braces and core_cleanup rule functions);
    6. document -- object providing read-only interface to main LaTeX file
       (used only by core_insertion rule function);
    7. read_file -- function that inserts a file into the document (used only
       by core_insertion rule function; not available for location rules);
    8. not_commented -- pattern prefix ensuring that LaTeX command is not in
       a comment (useful only up to removal phase, where comments are removed);
    9. not_escaped -- pattern prefix ensuring that following character is not
       escaped while recognizing newline commands (useful only up to setup
       phase, where newline commands are removed; a simpler pattern can be used
       in later phases); and
    10. single_pass --  Boolean indicating that the engine is going through the
       rules only once, which is indicative of using the regex module rather
       than the builtin re module (used only by core_main and
       core_cleanup_braces rule functions).

Rather than declare all arguments, rule functions typically declare only those
that they use and append **_ as catch-all argument for the other ones.

When applying location rules, their sub and subn methods require an extra
argument: file_name, which is the name of the file on which they are being
applied.

Modules:
    standard -- standard extraction rules provided with ERRERS
    local -- local extraction rules to supplement or replace standard rules
        (not provided; can be created manually if if desired)
"""

__all__ = ['local', 'standard']

try:
    from errers.rules import local
except ImportError:
    # Python throws ImportError rather than ModuleNotFoundError when local.py
    # is missing, because errers.rules is not fully initialized yet.
    pass
from errers.rules import standard
