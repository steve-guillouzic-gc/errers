# coding=utf-8
#
# SPDX-FileCopyrightText: 2023 His Majesty in Right of Canada
#
# SPDX-License-Identifier: LicenseRef-MIT-DND
#
# This file is part of the ERRERS package.

# Needed:
#   - Generate LaTeX output for each test function to make sure input is
#     correct and to allow visual confirmation of desired output.
#   - Add \usepackage.

import logging
import re

import pytest
import regex

import errers
from errers.rules import standard
from errers._engine.extractor import NOT_ESCAPED

TIMEOUT = 5


package_fancyvrb_removal = [
        # Match
        (r'\DefineVerbatimEnvironment{MyVerbatim}{Verbatim}{frame=single}',
         ''),
        (r'\CustomVerbatimCommand{\MyVerbatim}{Verbatim}{frame=single}',
         ''),
        (r'\RecustomVerbatimCommand{\MyVerbatim}{Verbatim}{frame=single}',
         ''),
        (r'\RecustomVerbatimEnvironment{MyVerbatim}{Verbatim}{frame=single}',
         ''),
        (r'\begin{Verbatim} foo bar \end{Verbatim}', ''),
        (r'\begin{Verbatim*} foo bar \end{Verbatim*}', ''),
        (r'\begin{BVerbatim} foo bar \end{BVerbatim}', ''),
        (r'\begin{BVerbatim*} foo bar \end{BVerbatim*}', ''),
        (r'\begin{LVerbatim} foo bar \end{LVerbatim}', ''),
        (r'\begin{LVerbatim*} foo bar \end{LVerbatim*}', ''),
        (r'\begin{SaveVerbatim} foo bar \end{SaveVerbatim}', ''),
        (r'\begin{SaveVerbatim*} foo bar \end{SaveVerbatim*}', ''),
        (r'\DefineVerbatimEnvironment{MyVerbatim}{Verbatim}{frame=single}'
         r'\begin{MyVerbatim} foo bar \end{MyVerbatim}', ''),
        (r'\DefineVerbatimEnvironment{MyVerbatim}{Verbatim}{frame=single}'
         r'\begin{MyVerbatim*} foo bar \end{MyVerbatim*}', ''),
        (r'\CustomVerbatimCommand{\MyVerbatim}{Verbatim}{frame=single}'
         r'\MyVerbatim[foo]{bar}', ''),
        (r'\SaveVerb[foo]{Bar}+asdf+', '||'),
        (r'\UseVerb{Bar}', '||'),
        (r'\fvset{Bar}', ''),
        (r'\UseVerbatim[asdf]{Bar}', '||'),
        (r'\VerbatimInput[asdf]{Bar}', ''),
        # No match
        (r'\begin{MyVerbatim} foo bar \end{MyVerbatim}',
         r'\begin{MyVerbatim} foo bar \end{MyVerbatim}'),
        (r'\begin{MyVerbatim*} foo bar \end{MyVerbatim*}',
         r'\begin{MyVerbatim*} foo bar \end{MyVerbatim*}'),
        (r'\begin{AVerbatim} foo bar \end{AVerbatim}',
         r'\begin{AVerbatim} foo bar \end{AVerbatim}'),
        (r'\begin{AVerbatim*} foo bar \end{AVerbatim*}',
         r'\begin{AVerbatim*} foo bar \end{AVerbatim*}')
    ]


@pytest.mark.parametrize('re_module', [regex, re])
@pytest.mark.parametrize(('input_', 'expected'), package_fancyvrb_removal)
def test_package_fancyvrb_removal(caplog, re_module, input_, expected):
    caplog.set_level(logging.ERROR)
    Pattern, Rule, RuleList = errers.create_classes(re_module, TIMEOUT)
    rules = standard.package_fancyvrb_removal(Rule=Rule, RuleList=RuleList,
                                              auto=True)
    rules.extend(standard.core_removal(Rule=Rule, RuleList=RuleList,
                                       auto=True, not_escaped=NOT_ESCAPED))
    assert rules.sub(input_) == expected
