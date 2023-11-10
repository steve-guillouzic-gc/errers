# coding=utf-8
#
# SPDX-FileCopyrightText: 2023 His Majesty in Right of Canada
#
# SPDX-License-Identifier: LicenseRef-MIT-DND
#
# This file is part of the ERRERS package.

r"""ERRERS: extraction engine

All elements of this sub-package are implementation details that may change in
non-backward-compatible ways between minor or micro version releases.

This sub-package provides the extraction engine. The engine is based on a
four-level hierarchy of classes, each of which is provided by a different
module. Each of the bottom-three layers (base, plain and latex) provides a set
of classes used to implement substitution rules: a pattern class, a rule class,
and a rule list class. In each module, these classes are returned by a function
called create_classes. The fourth module (extractor) uses the classes from the
latex module and the rules from the errers.rule sub-package to perform the
extraction.

Modules:
    base -- custom interface to the regular expression engine
    plain -- provides a more compact representation of verbose regular
        expressions and a compatibility layer for older versions of re module
        (prior to 3.11.5)
    latex -- provides latex-specific pattern elements
    extractor -- extraction engine itself
"""

__all__ = ['base', 'extractor', 'latex', 'plain']

from errers._engine import base, extractor, latex, plain
