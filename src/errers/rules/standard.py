# coding=utf-8
#
# SPDX-FileCopyrightText: 2023 His Majesty in Right of Canada
#
# SPDX-License-Identifier: LicenseRef-MIT-DND
#
# This file is part of the ERRERS package.

r"""ERRERS: standard extraction rules

Utility functions (used by rule functions):
    add_diacritic -- add diacritic to matched character

Rule functions:
    core_insertion -- rule list run once at start of extraction to insert
        secondary files
    core_removal -- rule list run once at start of extraction to remove
        commands and environments that could be corrupted by later rules (such
        as equations and \verb commands)
    core_setup -- rule list run once at start of extraction to remove elements
        that don't need multiple passes even with the re module;
    core_main -- rule list for standard LaTeX document with no package
    core_cleanup_braces -- rule list to clean-up braces
    core_cleanup -- rule list to clean-up remaining commands and white space
    class_NAME_PHASE -- rule list for document class NAME and specified
        extraction PHASE
    package_NAME_PHASE -- rule list for package NAME and specified extraction
        PHASE
    style_NAME_PHASE -- rule list for bibliography style NAME (BibTeX) and
        specified extraction PHASE
"""

__all__ = [
    'add_diacritic',
    'core_insertion', 'core_removal', 'core_setup', 'core_main',
    'core_cleanup_braces', 'core_cleanup',
    'class_drdc_main', 'class_drdc_brief_main', 'class_drdc_report_main',
    'class_interact_main', 'package_acro_main', 'package_acronym_main',
    'package_amsmath_main', 'package_amsmath_removal', 'package_amsthm_main',
    'package_apacite_main', 'package_array_main', 'package_babel_main',
    'package_booktabs_main', 'package_caption_main', 'package_cleveref_main',
    'package_dtk_logos_main', 'package_endfloat_main', 'package_enumitem_main',
    'package_etoolbox_location', 'package_etoolbox_main',
    'package_fancyvrb_removal',
    'package_fixme_main', 'package_floatrow_main', 'package_glossaries_main',
    'package_graphics_main', 'package_graphicx_main', 'package_harpoon_main',
    'package_hyperref_main', 'package_ifthen_main', 'package_listings_main',
    'package_listings_removal', 'package_makeidx_main',
    'package_mathtools_main', 'package_mdframed_main', 'package_mfpic_main',
    'package_multirow_main', 'package_natbib_main', 'package_pdfpages_main',
    'package_pgfplots_main', 'package_scalerel_main', 'package_siunitx_main',
    'package_soul_main', 'package_subcaption_main', 'package_subfig_main',
    'package_tikz_setup', 'package_tikz_main', 'package_ulem_main',
    'package_url_main', 'package_url_removal', 'package_xcolor_main',
    'style_drdc_main', 'style_drdc_plain_main']

import textwrap
import unicodedata


# Utility functions

def add_diacritic(characters, diacritic):
    """Add diacritic to first character of matched string.

    Arguments:
        characters -- characters to which diacritic must be added
        diacritic -- diacritic being added to characters

    Returns:
        character with diacritic, in composed form
    """
    return unicodedata.normalize('NFKC', characters + diacritic)


# Rule functions

def core_location(Rule, RuleList, **_):
    r"""Return rules that note location of LaTeX command definitions.

    Location is written as (line){file name} after the command name for use in
    Rule definition. To simplify negative look-behind pattern that prevents
    rules from matching command names in command definitions, definitions
    done using \newcommand, \renewcommand and \providecommand are all
    replaced by a non-starred \newcommand. Newline character before command
    name is retained to keep line count accurate in later definitions, but
    it is moved after the line number because the re modules requires
    negative look-behind pattern to be fixed width. Similar processing is done
    for \newenvironment and \renewenvironment using \newenvironment as
    placeholder name; and \def, \edef, \gdef and \xdef using \def as
    placeholder name.
    """
    return RuleList([
        Rule(
            textwrap.dedent(r"""
                \\(?:new|renew|provide)command\*?
                (?P<space>%n)  # White space (move after line number)
                %C"""),
            lambda m, file_name: r'\newcommand{%s}(%s)%s(%s)'
                                 % (m['c1'],
                                    m.string.count('\n', 0, m.start(0)) + 1,
                                    m['space'],
                                    file_name)),
        Rule(
            textwrap.dedent(r"""
                \\(?:new|renew)environment\*?
                (?P<space>%n)  # White space (move after line number)
                %c"""),
            lambda m, file_name: r'\newenvironment{%s}(%s)%s(%s)'
                                 % (m['c1'],
                                    m.string.count('\n', 0, m.start(0)) + 1,
                                    m['space'],
                                    file_name)),
        Rule(
            textwrap.dedent(r"""
                \\[egx]?def       # Apply to \def variants also
                (?P<space1>%n)    # White space (move after line number)
                (?P<name>%m)      # Command name
                (?P<space2>%n)    # White space (one \n max)
                (?P<para>[^{]*+)  # Parameter text
                """),
            lambda m, file_name: r'\def{%s}(%s)%s(%s)%s{%s}'
                                 % (m['name'],
                                    m.string.count('\n', 0, m.start(0)) + 1,
                                    m['space1'],
                                    file_name,
                                    m['space2'],
                                    m['para'])),
        Rule(
            textwrap.dedent(r"""
                \\newcounter
                (?P<space>%n)  # White space (move after line number)
                %C"""),
            lambda m, file_name: r'\newcounter{%s}(%s)%s(%s)'
                                 % (m['c1'],
                                    m.string.count('\n', 0, m.start(0)) + 1,
                                    m['space'],
                                    file_name))
    ])


def core_insertion(*, Rule, RuleList, document, not_commented, read_file, **_):
    """Return file-insertion rules run at start of extraction."""
    return RuleList([
        # Merge files
        Rule(not_commented + r'\\input%C',
             lambda m: '\n' + read_file(m['c1'], '.tex'),
             iterative=True),
        Rule(not_commented + r'\\include%C',
             lambda m: '\n' + read_file(m['c1'], '.tex')),
        Rule(not_commented + r'\\bibliography%C',
             lambda m: '\n' + read_file(document.path.stem, '.bbl')),
    ])


def core_removal(*, Rule, RuleList, not_escaped, **_):
    """Return text removal rules run at start of extraction."""
    return RuleList([
        # Remove \verb commands and verbatim environments. The first rule saves
        # the environment name in an optional argument for use in the second
        # rule. Rules for similar environments, such as the lstlisting
        # environment of the listings package, can do the same to be processed
        # jointly with the verbatim environment.
        Rule(r'\\begin{verbatim}', r'\\begin[verbatim]{verbatim}'),
        Rule(not_escaped + r"""
             (?:
                 (?P<comment>  # Also keep comment,
                 %             # from character
                 .*+           # to end of line.
                 )
                 |
                 (?P<verb>                   # Replace verb command by ||:
                      \\verb(?![a-zA-Z])     # command name,
                      %h                     # optional horizontal space,
                      (?P<delim>.)           # initial delimiter,
                      (?:(?!(?P=delim)).)*+  # and everything up to
                      (?P=delim)             # closing delimiter.
                 )
                 |
                 (?P<verbatim>                       # Replace verbatim by ||:
                     \\begin%s{verbatim}             # start of environment
                     (?s:                            # and, including newlines,
                         (?:(?!\\end{(?P=s1)}).)*+   # everything up to
                     )
                     \\end{(?P=s1)}                  # end of environment.
                 )
             )""",
             lambda m: ((m['comment'] or '')
                        + ('||' if m['verb'] else ''))),
        # Remove comments: comment-only lines are removed; empty lines
        # following end-of-line comments are kept; non-empty lines following
        # end-of-line comments are wrapped up.
        Rule(fr'^%h{not_escaped}%.*\n', ''),
        Rule(fr'{not_escaped}%.*\n%h\n', r'\n\n'),
        Rule(fr'{not_escaped}%.*%n', ''),
        # Remove lines dealing with internal commands
        Rule(r'(?s)\\makeatletter.*?\\makeatother', ''),
        # Replace math expressions by $$. It is done here to prevent other
        # rules from adding dollar signs to the math expressions, which would
        # confuse the rules below. The first rule converts dollar sign pairs
        # (TeX command for math display mode) into single dollar signs. The
        # second rule converts \( \) pairs into $ $ pairs. The third rule does
        # the same for \begin{math} and \end{math} pairs. The fourth and fifth
        # rules convert \[ \] pairs into \begin{equation} \end{equation} pairs.
        # The sixth and seventh rules do the same for eqnarray environment. The
        # eighth rule matches non-empty inline equations. The ninth rule
        # matches displayed equations while capturing the final punctuation
        # mark (if present and not encapsulated into another command or
        # environment) and putting it after the $$. The tenth rule matches
        # standalone \ensuremath commands. The eleventh rule replaces
        # dollar-sign pairs ($$) by a number when immediately followed by
        # letters or an alphabetic command.
        Rule(r'\$\$', '$'),
        Rule(r'\\[()]', '$'),
        Rule(r'\\(?:begin|end){math}', '$'),
        Rule(r'\\\[', r'\\begin{equation}'),
        Rule(r'\\]', r'\\end{equation}'),
        Rule(r'\\begin{eqnarray}', r'\\begin{equation}'),
        Rule(r'\\end{eqnarray}', r'\\end{equation}'),
        Rule(fr"""(?s)               # Period matches \n too.
             {not_escaped}(?<!\$)\$  # Start of equation.
             (?:\\\$|[^\$])++        # Anything but an unescaped $.
             {not_escaped}\$         # End of equation.
             """, '$$'),
        Rule(r"""(?s)                 # Period matches \n too.
             \\begin{(equation\*?)}   # Start of equation.
                 (?:
                     (?!\\end{\1})    # Scanning until the end
                     (?:              # and skipping over
                         }            # closing brackets,
                         |
                         \\end%C      # end of environments,
                         |
                         \\label%C    # labels,
                         |
                         \\[,.:;!?]   # escaped punctuation,
                         |
                         %w           # and white space,
                         |
                         (?P<last>.)  # take note of last character.
                     )
                 )*
             \\end{\1}                # End of equation.
             """,
             lambda m: '$$' if m['last'] not in ',.:;!?'
                       else '$$' + m['last']),
        Rule(r'\\ensuremath%C', '$$'),
        Rule(r'\$\$(?=\\?[^\W\d])', '124')
    ])


def core_setup(*, Rule, RuleList, **_):
    """Return miscellaneous setup rules run at start of extraction."""
    # tabbing: rules for tabbing environment
    tabbing = RuleList([
        Rule(r"""(?s)               # Period matches \n too.
             (?:\A|(?<!\\\\))       # Start of line
                 (?:(?!\\kill).)*+  # Anything but \kill
             \\kill                 # \kill
             """, ''),
        Rule(r'\\\\', r'\n\n'),
        Rule(r'\\=', ''),
        Rule(r'\\>', r'\n\n'),
        Rule(r'\\<', ''),
        Rule(r'\\\+', ''),
        Rule(r'\\-', ''),
        Rule(r"\\'", r'\n\n'),
        Rule(r'\\`', r'\n\n'),
        Rule(r'\\(?:push|pop)tabs', '')
    ])
    return RuleList([
        # Tabbing environment
        Rule(r"""(?s)                         # Period matches \n too.
             \\begin{tabbing}                 # Start of environment.
                 ((?:(?!\\end{tabbing}).)*+)  # Scan until end of environment.
             \\end{tabbing}                   # End of environment.
             """,
             lambda m: '\n' + tabbing.sub(m[1]) + '\n'),
        # Accents
        # Refs:
        #    https://en.wikibooks.org/wiki/LaTeX/Special_Characters
        #    https://en.wikipedia.org/wiki/Combining_character
        # Note: tilde and circumflex accent are processed with reserved
        # characters.
        # Now that tabbing environment has been processed, convert \a command
        # to regular accent commands.
        Rule(r'\\a%C%C', r'\\\g<c1>{\g<c2>}'),
        # The following commands are special characters. The regular i, rather
        # than the dot-less i, must be used to compose properly with accents.
        Rule(r'\\o', 'ø'),
        Rule(r'\\i', 'i'),
        Rule(r'\\l', 'ł'),
        # The following commands add the accent to the first letter of their
        # argument and drop the following ones.
        Rule(r'\\`%C', lambda m: add_diacritic(m['c1'][0], '\u0300')),
        Rule(r"\\'%C", lambda m: add_diacritic(m['c1'][0], '\u0301')),
        Rule(r'\\"%C', lambda m: add_diacritic(m['c1'][0], '\u0308')),
        Rule(r'\\H%C', lambda m: add_diacritic(m['c1'][0], '\u030B')),
        Rule(r'\\c%C', lambda m: add_diacritic(m['c1'][0], '\u0327')),
        Rule(r'\\k%C', lambda m: add_diacritic(m['c1'][0], '\u0328')),
        Rule(r'\\v%C', lambda m: add_diacritic(m['c1'][0], '\u030C')),
        Rule(r'\\r%C', lambda m: add_diacritic(m['c1'][0], '\u030A')),
        # There's a special command for ring over a.
        Rule(r'\\aa', lambda m: add_diacritic('a', '\u030A')),
        # The following commands add the accent to the first letter of their
        # argument and keep the following ones as is.
        Rule(r'\\=%C',
             lambda m: add_diacritic(m['c1'][0], '\u0304') + m['c1'][1:]),
        Rule(r'\\\.%C',
             lambda m: add_diacritic(m['c1'][0], '\u0307') + m['c1'][1:]),
        Rule(r'\\u%C',
             lambda m: add_diacritic(m['c1'][0], '\u0306') + m['c1'][1:]),
        # The following command centres the dot below the argument in LaTeX.
        # The rule only places it on the first letter, as it's the closest I
        # was able to achieve.
        Rule(r'\\d%C',
             lambda m: add_diacritic(m['c1'][0], '\u0323') + m['c1'][1:]),
        # Rules are not provided for \b and \t, as I was not able to create
        # sensible ones. They are handled by the default rule for one-argument
        # commands.
        # Replace \\ by a newline (it will lead to a new paragraph if at the
        # end of the line, but not otherwise). \tabularnewline is equivalent
        # to \\ in a tabular environment.
        Rule(r'\\\\', r'\n'),
        Rule(r'\\tabularnewline', r'\n'),
        # Replace tab characters and \newblock commands with regular spaces.
        Rule(r'\t', ' '),
        Rule(r'\\newblock', ' '),
        # Symbols and punctuation
        # Replace LaTeX quotes with straight quotes. Replace --- and -- with
        # actual em and en dashes. Remove discretionary hyphens.
        Rule(r'\\LaTeX', 'LaTeX'),
        Rule(r'\\ldots', '…'),
        Rule(r'``', '"'),
        Rule(r"''", '"'),
        Rule(r'`', "'"),
        Rule('---', '—'),
        Rule('--', '–'),
        Rule(r'\\textemdash', '—'),
        Rule(r'\\textendash', '–'),
        Rule(r'\\textcopyright', '©'),
        Rule(r'\\textregistered', '®'),
        Rule(r'\\texttrademark', '™'),
        Rule(r'\\-', ''),
        # Replace explicit space commands by '\ ', except for negative spaces
        # which are simply removed.
        Rule(r'\\[,>:;]', r'\\ '),
        Rule(r'\\(?:thin|med|thick)space', r'\\ '),
        Rule(r'\\q?quad', r'\\ '),
        Rule(r'\\!', ''),
        Rule(r'\\neg(?:thin|med|thick)space', r''),
        # Font and alignment
        Rule(r'\\(?:Huge|huge|LARGE|Large|large|normalsize)', ''),
        Rule(r'\\(?:small|footnotesize|scriptsize|tiny)', ''),
        Rule(r'\\centering', ''),
        Rule(r'\\ragged(?:left|right)', ''),
        Rule(r'\\(?:no)?indent', ''),
        # Counters
        Rule(r'\\the(?:part|chapter|section|subsection|subsubsection)', 'X'),
        Rule(r'\\the(?:paragraph|subparagraph|figure|table)', 'X'),
        Rule(r'\\the(?:footnote|mpfootnote|enumi|enumii|enumiii|enumiv)', 'X'),
        Rule(r'\\the(?:page|equation)', 'X'),
        # Ligatures: not LaTeX specific.
        Rule('ﬀ', 'ff'),
        Rule('ﬁ', 'fi'),
        Rule('ﬂ', 'fl'),
        Rule('ﬃ', 'ffi'),
        Rule('ﬄ', 'ffl')
    ])


def core_main(*, Rule, RuleList, auto, single_pass, **_):
    """Return rule list for core LaTeX with no package."""
    # colon: used by \item rule
    # backslash: used by translate_rep rule
    # translate_rep and unwrap: used by new_command and def_command functions
    # translate_para: used by def_command function
    colon = Rule(r'([.,:;!?]):$', r'\1')
    backslash = Rule(r'\\', r'\\\\')
    default = Rule(r'\#1', lambda m, default: default)
    translate_rep_new_no_opt = RuleList([
        backslash,
        Rule(r'\#([1-9])', r'\\g<c\1>')
    ])
    translate_rep_new_opt = RuleList([
        backslash,
        Rule(r'\#1', r'\\g<s1>'),
        Rule(r'\#([2-9])', lambda m: fr'\g<c{int(m[1]) - 1}>')
    ])
    translate_rep_def = RuleList([
        backslash,
        Rule(r'\#([1-9])', r'\\g<a\1>')
    ])
    unwrap = Rule(r'\s+', ' ')
    translate_para = RuleList([
        Rule(r'([\\\^\-\[\].$*+?(){|])',     # Escape special characters
             r'\\\1'),                       # (except #).
        Rule(r'[\ \t]{2,}', ' '),            # Compress spaces and tabs.
        Rule(r'\ \n', r'\n'),                # Remove spaces before newlines.
        Rule(r'\n\ ', r'\n'),                # Remove spaces after newlines.
        Rule(r'(?<!\n)\n(?!\n)', ' '),       # Replace single \n by space.
        Rule(r'\#([0-9])([^\#]++)(?=\#)',    # Non-final delimited parameters
             r'(?P<a\1>(?:(?!\2)%C)*+)\2'),  # match all text up to delimiter.
        Rule(r'\#([0-9])([^\#]++)(?<![\ \n])\Z',  # Same for final parameter if
             r'(?P<a\1>(?:(?!\2)%C)*+)\2'),       # delimiter does not end with
                                                  # a space or newline.
        Rule(r'\#([0-9])([^\#]*)\ \Z',       # Final parameter with space
             r'(?)<a\1>(?:(?!\2 )%C)*+)'     # ending delimiter captures
             r'\2(?:%n(?!\\n))?+'),          # newline only if not followed
                                             # by another newline.
        Rule(r'\#([0-9])([^\#]*)\n\n\Z',       # Final parameter with paragraph
             r'(?P<a\1>(?:(?!\2\\n\\n)%C)*+)'  # ending delimiter captures
             r'\2(?:%n%n(?!\\n))?+'),          # newlines only if not followed
                                               # by another newline.
        Rule(r'\#([0-9])',                   # Parameters without delimiter
             r'%C(?P<a\1>)'),                # match curly-bracket arguments.
        Rule(r'\n\n', r'%h\\n%h\\n%h'),      # Insert pattern for new para.
        Rule(r'(?<!\\)\ ',                   # Insert pattern for space char.
             r'(?=[\\ \\t\\n])%n'),
    ])
    # Dynamic list of rules for commands defined in document and function to
    # append rules to it
    commands = RuleList(iterative=single_pass)

    def new_command(*, name, n_mandatory, optional, definition, file, line):
        if auto:
            if optional is None:
                translate_rep = translate_rep_new_no_opt
                mandatory = '%C'
                opt_def = [('', definition)]
            else:
                translate_rep = translate_rep_new_opt
                # To avoid matching [ with re module when multi-level brackets
                # are involved, mandatory arguments must be in curly brackets
                # when an optional argument may be present.
                mandatory = '%c'
                if optional:
                    # Use two rules if optional parameter has non-empty default
                    # value.
                    opt_def = [('%s', definition),
                               ('', default.sub(definition, default=optional))]
                else:
                    opt_def = [('%s?', definition)]
            for opt_placeholder, intermediate_def in opt_def:
                replacement = translate_rep.sub(intermediate_def)
                compact = unwrap.sub(replacement)
                rule = Rule(r'\%s%s%s' % (name, opt_placeholder,
                                          mandatory * n_mandatory),
                            replacement, compact=compact,
                            file=file, line=int(line), scope='')
                commands.append(rule)
                rule.pattern.print_trace('Created')
        return ''

    def new_environment(*, name, n_mandatory, optional, begin_def, end_def,
                        file, line):
        if auto:
            new_command(name=r'\begin{%s}' % name,
                        n_mandatory=n_mandatory,
                        optional=optional,
                        definition=begin_def,
                        file=file,
                        line=line)
            new_command(name=r'\end{%s}' % name,
                        n_mandatory=0,
                        optional=None,
                        definition=end_def,
                        file=file,
                        line=line)
        return ''

    def def_command(*, name, parameters, definition, file, line):
        if auto:
            replacement = translate_rep_def.sub(definition)
            compact = unwrap.sub(replacement)
            rule = Rule(r'\%s%%n%s' % (name, translate_para.sub(parameters)),
                        replacement, compact=compact,
                        file=file, line=int(line), scope='')
            commands.append(rule)
            rule.pattern.print_trace('Created')
        return ''

    return RuleList([
        # Automatic rules
        #
        # When files are loaded, \newcommand\* \renewcommand\*? and
        # \providecommand\*? are replaced by a non-starred \newcommand, and the
        # line number and file name are inserted after the command name.
        Rule(r'\\newcommand%C%r%r%s%s%c',
             lambda m: new_command(name=m['c1'],
                                   n_mandatory=int(m['s1']) - 1,
                                   optional=m['s2'],
                                   definition=m['c2'],
                                   file=m['r2'],
                                   line=m['r1'])),
        Rule(r'\\newcommand%C%r%r%s?%c',
             lambda m: new_command(name=m['c1'],
                                   n_mandatory=int(m['s1'] or '0'),
                                   optional=None,
                                   definition=m['c2'],
                                   file=m['r2'],
                                   line=m['r1'])),
        # When files are loaded, \renewenvironment is replaced by
        # \newenvironment, and the line number and file name are inserted after
        # the environment name.
        Rule(r'\\newenvironment%c%r%r%s%s%c%c',
             lambda m: new_environment(name=m['c1'],
                                       n_mandatory=int(m['s1']) - 1,
                                       optional=m['s2'],
                                       begin_def=m['c2'],
                                       end_def=m['c3'],
                                       file=m['r2'],
                                       line=m['r1'])),
        Rule(r'\\newenvironment%c%r%r%s?%c%c',
             lambda m: new_environment(name=m['c1'],
                                       n_mandatory=int(m['s1'] or '0'),
                                       optional=None,
                                       begin_def=m['c2'],
                                       end_def=m['c3'],
                                       file=m['r2'],
                                       line=m['r1'])),
        # When files are loaded, \edef, \gdef and \xdef are replaced by \def,
        # and the line number and file name are inserted after the command
        # name.
        Rule(r"""\\def
             %c  # Command name
             %r  # Line number
             %r  # File name
             %c  # Parameter text
             %c  # Definition
             """,
             lambda m: def_command(name=m['c1'],
                                   parameters=m['c2'],
                                   definition=m['c3'],
                                   file=m['r2'],
                                   line=m['r1'])),
        # When files are loaded, the line number and file name are inserted
        # after the counter name.
        Rule(r'\\newcounter%c%r%r%s?',
             lambda m: new_command(name=r'\the%s' % m['c1'],
                                   n_mandatory=0,
                                   optional=None,
                                   definition='X',
                                   file=m['r2'],
                                   line=m['r1'])),
        commands,
        #
        # End of automatic rules
        #
        # Preamble
        Rule(r'\\documentclass%s?%c', ''),
        Rule(r'\\usepackage%s?%c%s?', ''),
        Rule(r'\\RequirePackage%s?%c%s?', ''),
        Rule(r'\\PassOptionsToPackage%C%C', ''),
        Rule(r'\\title%C', r'\n\g<c1>\n'),
        Rule(r'\\author%C', r'\n\g<c1>\n'),
        Rule(r'\\hyphenation%C', ''),
        # Sections
        Rule(r"""\\(?:part|chapter|section|subsection|subsubsection
                          |paragraph|subparagraph)\*?%s?%c""",
             r'\n\g<s1>\n\n\g<c1>\n'),
        Rule(r'\\addtocontents%C%C', r'\n\g<c2>\n'),
        # Floats
        # Move floats to their own paragraphs, processing them one at a time
        # starting from end of paragraph.
        Rule(r"""(?s)                            # Period matches \n too.
             \\begin{(figure|table)}%s?          # -capture float from start
                (?P<float>(?:(?!\\end{\1}).)*+)  #  to end,
             \\end{\1}%h\n?                      #  incl. white space; and
             (?P<para>(?:                        # -capture para until
                 (?!(?<=\n)%h\n)                 #  a blank line
                 (?!\\begin{(?:figure|table)})   #  or another float.
                 .
             )*+)
             (?<=\n)%h\n                         # Match only if end of para.
             """,
             r'\g<para>\n'
             r'\g<float>\n\n',
             iterative=True),
        # Captions
        Rule(r'\\caption%s?%c', r'\n\g<s1>\n\n\g<c1>\n'),
        # Footnotes, marginpars and thanks are put in parentheses at the end of
        # the paragraph (next blank line). Marginpars with optional arguments
        # are split into two before being moved to end of paragraph.
        Rule(r'(?s)\\marginpar%s%C',
             r'\\marginpar{\g<s1>}\\marginpar{\g<c1>}'),
        Rule(r'(?s)\\marginpar%C', r'\\footnote{\g<c1>}'),
        Rule(r'(?s)\\thanks%C', r'\\footnote{\g<c1>}'),
        Rule(r'(?s)\\footnote(?:text)?%s?%c(?P<rest_of_para>.*?)\n%h\n',
             lambda m: '%s (%s)\n\n' % (m['rest_of_para'], m['c1'].strip()),
             iterative=True),
        Rule(r'\\footnotemark%s?', ''),
        # Lists. The second \item rule adds a colon if the optional argument
        # does not end with a punctuation character. The first \item rule omits
        # the colon if the argument is empty. The third \item rule takes care
        # of the case where the argument is omitted.
        Rule(r'\\item\[\]%w', '-'),
        Rule(r'\\item%s', lambda m: colon.sub('-' + m['s1'] + ':') + ' '),
        Rule(r'\\item%w ', '-'),
        # Tabular
        Rule(r'\\multicolumn%C%C%C', r'\g<c3>'),
        # References
        Rule(r'\\bibliographystyle%C', ''),
        Rule(r'\\bibitem%s?%c', r'\n[X]: '),
        Rule(r'\\cite%s%C', r'[X, \g<s1>]'),
        Rule(r'\\cite%C', '[X]'),
        Rule(r'\\label%C', ''),
        Rule(r'\\ref%C', 'X'),
        Rule(r'\\pageref%C', 'X'),
        # Boxes
        Rule(r'\\newsavebox%C', ''),
        Rule(r'\\usebox%C', ''),
        Rule(r'\\rule%s?%c%c', ''),
        Rule(r'\\mbox%C', r'\g<c1>'),
        Rule(r'\\makebox%s?%s?%c', r'\g<c1>'),
        Rule(r'\\parbox%s?%s?%s?%c%c', r'\g<c2>'),
        Rule(r'\\raisebox%C%s?%s?%c', r'\g<c2>'),
        # Lengths and spaces
        Rule(r'\\setlength%C%C', ''),
        Rule(r'\\addtolength%C%C', ''),
        Rule(r'\\settoheight%C%C', ''),
        Rule(r'\\settodepth%C%C', ''),
        Rule(r'\\settowidth%C%C', ''),
        Rule(r'\\hspace\*?%C', ''),
        Rule(r'\\vspace\*?%C', ''),
        # Counters
        Rule(r'\\refstepcounter%C', ''),
        Rule(r'\\stepcounter%C', ''),
        Rule(r'\\value%C', 'X'),
        Rule(r'\\setcounter%C%C', ''),
        Rule(r'\\addtocounter%C%C', ''),
        Rule(r'\\alph%C', 'x'),
        Rule(r'\\arabic%C', 'X'),
        Rule(r'\\roman%C', 'X'),
        Rule(r'\\fnsymbol%C', 'X'),
        Rule(r'\\numberwithin%C%C', ''),
        Rule(r'\\newtheorem%C%s?%c(?(s1)|%s?)', r'\n\g<c2>\n'),
        # Page break
        Rule(r'\\(?:clearpage|cleardoublepage|newpage)', r'\n\n'),
        Rule(r'\\enlargethispage\*?%C', ''),
        Rule(r'\\(?:pagebreak|nopagebreak)%s?', ''),
        # Font and alignment
        Rule(r'\\(?:textnormal|emph|lowercase|uppercase|underline)%C',
             r'\g<c1>'),
        Rule(r'\\(?:MakeLowercase|MakeUppercase)%C', r'\g<c1>'),
        Rule(r'\\text(?:up|it|sl|sc)%C', r'\g<c1>'),
        Rule(r'\\text(?:rm|sf|tt)%C', r'\g<c1>'),
        Rule(r'\\text(?:bf|md)%C', r'\g<c1>'),
        Rule(r'\\shortstack%s?%c', r'\g<c1>'),
        # Headers and footers
        Rule(r'\\pagestyle%C', ''),
        Rule(r'\\thispagestyle%C', ''),
        # Plain TeX
        Rule(r'\\noalign%C', '')
    ])


def core_cleanup_braces(*, Rule, RuleList, default, single_pass, **_):
    """Return rule list to clean-up braces.

    When the re module is used, this prepares the text for another iteration of
    the main rules.
    """
    rlist = RuleList()
    if default:
        # Replace curly-brackets one-argument commands with the said argument,
        # except for \begin and \end.
        rlist.append(
            Rule(r'\\(?!begin|end)[a-zA-Z]++\*?+%c(?!%n[{\[\(])',
                 r'\g<c1>', iterative=single_pass)
        )
    # Remove curly brackets not part of commands, keeping preceding white space
    # if any.
    rlist.append(
        Rule(r"""(?s)                                # Period matches \n too.
             (?P<command>
                 \\(?:[a-zA-Z]++\*?+|\S)
                 (?:%c|%r|%s)*+                      # Capture commands
             )
             |                                       # and
             (?P<space>[\ \t\n]++)                   # white space as is,
             |                                       # while capturing
             %c                                      # content of braces.
             |                                       # Everything else
             (?P<other>.[^\\{]*+)                    # is captured as is.
             """, r'\g<command>\g<space>\g<c2>\g<other>',
             iterative=single_pass,
             sub_matches=['c2'])
    )
    return rlist


def core_cleanup(*, Rule, RuleList, default, **_):
    """Return rule list to clean-up remaining commands and white space."""
    rlist = RuleList()
    if default:
        rlist.extend(RuleList([
            # Remove commands with no arguments, including the space that
            # follows them (up to, but not including, the newline). An
            # additional lookahead is required in order to avoid matching
            # partial command names, because the re module doesn't have
            # possessive quantifiers.
            Rule(r'\\[a-zA-Z]++(?![a-zA-Z])\*?+%h(?![{\[\(])%h', ''),
            # Remove \begin and \end commands, including the following white
            # space and the newline if applicable.
            Rule(r'\\begin%C(?:%c|%r|%s)*+%n', ''),
            Rule(r'\\end%C%n', '')
        ]))
    rlist.extend(RuleList([
        # Replace explicit space characters with regular ones. Must be done
        # after processing of argument-less commands. Tilde rule matches only
        # if not following a backslash.
        Rule(r'(?<!\\)~', ' '),
        Rule(r'\\[\ \n]', ' '),
        # Reserved characters.
        Rule(r'\\\#', '#'),
        Rule(r'\\\$', '$'),
        Rule(r'\\%', '%'),
        Rule(r'\\&', '&'),
        Rule(r'\\{', '{'),
        Rule(r'\\}', '}'),
        Rule(r'\\_', '_'),
        Rule(r'\\~%C', lambda m: add_diacritic(m['c1'][0], '\u0303')),
        Rule(r'\\\^%C', lambda m: add_diacritic(m['c1'][0], '\u0302')),
        # Replace consecutive space characters with a single space.
        Rule(r'[\ ]{2,}', ' '),
        # Remove white space at beginning and end of lines.
        # Space must be escaped because of VERBOSE option.
        Rule(r'^\ ', ''),
        Rule(r'\ $', ''),
        # Remove blank lines at beginning and end of document.
        Rule(r'\A\n++', ''),
        Rule(r'\n\n++\Z', r'\n'),
        # Replace consecutive blank lines with single blank lines.
        Rule(r'\n{3,}', r'\n\n'),
        # Wrap lines by replacing newlines between non-blank lines with spaces.
        Rule(r'(?<=.)\n(?=.)', ' ')
    ]))
    return rlist


def class_drdc_main(*, Rule, RuleList, **_):
    """Return rule list for DRDC classes."""
    # authors: sub-rules for \author and \authors command
    # future: sub-rule for \futuredistribution
    authors = RuleList([
        Rule(r'\\rank%C', r'\g<c1>'),
        Rule(r'\\equalauthormark', r''),
        Rule(r'%w\\and', ', '),
        Rule('%s', r' (\g<s1>) '),
        Rule(r'\ ,', ',')
    ])
    future = Rule('^(?:u|goc|goc&c|dnd|dnd&c|drdc)$', '')
    return RuleList([
        Rule(r'\\authors?%C', lambda m: '\n' + authors.sub(m['c1']) + '\n'),
        Rule(r'\\establishment%C', r'\n\g<c1>\n'),
        Rule(r'\\projectnumber%C', r'\n\g<c1>\n'),
        Rule(r'\\(?:|sub|subsub|par)annex\*?%s?%c', r'\n\g<s1>\n\n\g<c1>\n'),
        Rule(r'\\setdate%C%C%C', ''),
        Rule(r'\\addkeyword%C',
             lambda m: m['c1'][0].upper() + m['c1'][1:] + '\n'),
        Rule(r'\\make(?:expanded|initialized)authors%C%C', ''),
        Rule(r'\\makeexpandedkeywords%C%C', ''),
        Rule(r'\\ControlledGoods%C', ''),
        Rule(r'\\docnumber%C', ''),
        Rule(r'\\futuredistribution%C%C',
             lambda m: '\n' + future.sub(m['c1']) + '\n\n' + m['c2'] + '\n'),
        Rule(r'\\preparedfor%C%C', r'\n\g<c1>\n\n\g<c2>\n')
    ])


class_drdc_brief_main = class_drdc_main
class_drdc_report_main = class_drdc_main


def class_interact_main(*, Rule, RuleList, **_):
    """Return rule list for Taylor & Francis Interact class."""
    return RuleList([
        Rule(r'\\name%C', r'\n\g<c1>\n'),
        Rule(r'\\affil%C', r'\n\g<c1>\n'),
        Rule(r'\\tbl%C%C', r'\\caption{\g<c1>}\n\g<c2>')
    ])


def package_acro_main(*, Rule, RuleList, **_):
    """Return rule list for acro package."""
    # rule_X: subrules for \DeclareAcronym rule (X = short, long, short_plural,
    #     short_plural_form, long_plural or long_plural_form)
    # declare_acronym: function implementing the \DeclareAcronym rule; required
    #     because of the rule's complexity
    rule_short = Rule.key_value('short')
    rule_long = Rule.key_value('long')
    rule_short_plural = Rule.key_value('short-plural')
    rule_short_plural_form = Rule.key_value('short-plural-form')
    rule_long_plural = Rule.key_value('long-plural')
    rule_long_plural_form = Rule.key_value('long-plural-form')

    def declare_acronym(acro_id, keys):
        r"""Process \DeclareAcronym arguments.

        The singular form is always returned, but the plural form is returned
        only if at least one plural key is present.
        """
        short = rule_short.sub(keys) or acro_id
        long = rule_long.sub(keys)
        short_plural = rule_short_plural.sub(keys)
        short_plural_form = rule_short_plural_form.sub(keys)
        long_plural = rule_long_plural.sub(keys)
        long_plural_form = rule_long_plural_form.sub(keys)
        text = '\n%(short)s: %(long)s\n' % {'short': short, 'long': long}
        if (short_plural or short_plural_form
                or long_plural or long_plural_form):
            text += ('\n%(short)s: %(long)s\n'
                     % {'short':
                        short_plural_form or short + (short_plural or 's'),
                        'long':
                        long_plural_form or long + (long_plural or 's')})
        return text

    return RuleList([
        Rule(r'\\acroif(?:|boolean|all|any|tag|starred|used)TF%C%C%C', ''),
        Rule(r'\\acroif(?:|boolean|all|any|tag|starred|used)[TF]%C%C', ''),
        Rule(r'\\acroif(?:first|single|chapter|pages)TF%C%C%C', ''),
        Rule(r'\\acroif(?:first|single|chapter|pages)[TF]%C%C', ''),
        Rule(r'\\acronymsmap%C', ''),
        Rule(r'\\acronymsmapTF%C%C%C', ''),
        Rule(r'\\acronymsmap[TF]%C%C', ''),
        Rule(r'\\(?:New|Renew|Setup|SetupNext)AcroTemplate%s?%c%c', ''),
        Rule(r'\\DeclareAcronym%C%C',
             lambda m: declare_acronym(m['c1'], m['c2'])),
        Rule(r'\\(?:ac|acs|aca|acl|acf|acsingle)\*?%C', r'\g<c1>'),
        Rule(r'\\(?:Ac|Acl|Acf|Acsingle)\*?%C', r'\g<c1>'),
        Rule(r'\\(?:acp|acsp|acap|aclp|acfp)\*?%C', r'\g<c1>s'),
        Rule(r'\\(?:Acp|Aclp|Acfp)\*?%C', r'\g<c1>s'),
        Rule(r'\\(?:iac|iacs|iacl)\*?%C', r'a \g<c1>'),
        Rule(r'\\Iac\*?%C', r'A \g<c1>'),
        Rule(r'\\acflike\*?%C%C', r'\g<c2> (\g<c1>)'),
        Rule(r'\\acfplike\*?%C%C', r'\g<c2> (\g<c1>s)'),
        Rule(r'\\acreset%C', r''),
        Rule(r'\\acuse%C', r''),
        Rule(r'\\printacronyms%s?', r'')
    ])


def package_acronym_main(*, Rule, RuleList, **_):
    """Return rule list for acronym package."""
    return RuleList([
        Rule(r'\\(?:ac|acs|acl|acf|acfi|acsu|aclu)\*?%C', r'\g<c1>'),
        Rule(r'\\(?:acp|acsp|aclp|acfp)\*?%C', r'\g<c1>s'),
        Rule(r'\\iac\*?%C', r'a \g<c1>'),
        Rule(r'\\Iac\*?%C', r'A \g<c1>'),
        Rule(r'\\acused%C', ''),
        Rule(r'\\(?:acro|newacro|acrodef)%C%s%C', r'\g<s1>: \g<c2>\n'),
        Rule(r'\\(?:acro|newacro|acrodef)%C%C', r'\g<c1>: \g<c2>\n'),
        Rule(r'\\acroplural%C%s%C', r'\g<s1>: \g<c2>\n'),
        Rule(r'\\acroplural%C%C', r'\g<c1>s: \g<c2>\n')
    ])


def package_amsmath_removal(*, Rule, RuleList, **_):
    """Return rule list for amsmath package (removal phase).

    Applied at removal phase, because that is when equations are removed.
    """
    return RuleList([
        Rule(r'\\(begin|end){(?:align|alignat|flalign|gather|multline)\*?}',
             r'\\\1{equation}')
    ])


def package_amsmath_main(*, Rule, RuleList, **_):
    """Return rule list for amsmath package (main phase)."""
    return RuleList([
        Rule(r'\\eqref%C', r'(\\ref{\g<c1>})'),
        Rule(r'\\DeclareMathOperator\*?%C%C', ''),
        Rule(r'\\allowdisplaybreaks%s?', '')
    ])


def package_amsthm_main(*, Rule, RuleList, **_):
    """Return rule list for amsthm package (main phase)."""
    return RuleList([
        Rule(r'\\theoremstyle%C', ''),
        Rule(r'\\newtheoremstyle%C%C%C%C%C%C%C%C%C', '')
    ])


def package_apacite_main(*, Rule, RuleList, **_):
    """Return rule list for apacite package."""
    return RuleList([
        Rule(r'\\begin{APACrefauthors}', ''),
        Rule(r'\\APACaddress(?:Publisher|Institution)%C%C',
             lambda m: (m['c1'] + (': ' if m['c1'] and m['c2'] else '')
                        + m['c2'])),
        Rule(r'\\APACbVolEdTR%C%C',
             lambda m: ('(' + m['c1']
                            + ('; ' if m['c1'] and m['c2'] else '')
                            + m['c2']
                            + ')')),
        Rule(r'\\APACinsertmetastar%C', ''),
        Rule(r'\\APACjournalVolNumPages%C%C%C%C',
             r'\g<c1>, \g<c2>(\g<c3>), \g<c4>'),
        Rule(r'\\APACmonth%C',
             lambda m: ['', 'January', 'February', 'March', 'April', 'May',
                        'June', 'July', 'August', 'September', 'October',
                        'November', 'December', 'Winter', 'Spring', 'Summer',
                        'Fall'][int(m['c1'])]),
        Rule(r'\\APACrefatitle%C%C', r'\g<c2>'),
        Rule(r'\\APACrefbtitle%C%C', r'\g<c2>'),
        Rule(r'\\APACrefYear%C', r'(\g<c1>)'),
        Rule(r'\\APACrefYearMonthDay%C%C%C',
             lambda m: '(' + m['c1']
                           + (', ' if m['c2'] or m['c3'] else '')
                           + m['c2']
                           + (' ' if m['c3'] else '')
                           + m['c3']
                           + ')'),
        Rule(r'\\BBA%C', '&'),
        Rule(r'\\BBCQ', ''),
        Rule(r'\\BBOQ', ''),
        Rule(r'\\Bby', 'by'),
        Rule(r'\\BCBL%C', ','),
        Rule(r'\\BEd', 'ed.'),
        Rule(r'\\BED', 'Ed.'),
        Rule(r'\\BEDS', 'Eds.'),
        Rule(r'\\BIn', 'In'),
        Rule(r'\\BNUM', 'No.'),
        Rule(r'\\BNUMS', 'Nos.'),
        Rule(r'\\BOthers', 'et al'),
        Rule(r'\\BOthersPeriod', 'et al.'),
        Rule(r'\\BPBI', '. '),
        Rule(r'\\BPG', 'p.'),
        Rule(r'\\BPGS', 'pp.'),
        Rule(r'\\BTR', 'Tech. Rep.'),
        Rule(r'\\BVOL', 'Vol.'),
        Rule(r'\\BVOLS', 'Vols.'),
        Rule(r'\\PrintOrdinal%C',
             lambda m: '1st' if m['c1'] == 1 else
                       '2nd' if m['c1'] == 2 else
                       '3rd' if m['c1'] == 3 else
                       m['c1'] + 'th')
    ])


def package_array_main(*, Rule, RuleList, **_):
    """Return rule list for array package."""
    return RuleList([
        Rule(r'\\newcolumntype%C%s?%c', '')
    ])


def package_babel_main(*, Rule, RuleList, **_):
    """Return rule list for babel package."""
    return RuleList([
        Rule(r'\\shorthandon%C', ''),
        Rule(r'\\shorthandoff%C', ''),
        Rule(r'\\up%C', r'\g<c1>')
    ])


def package_booktabs_main(*, Rule, RuleList, **_):
    """Return rule list for booktabs package."""
    return RuleList([
        Rule(r'\\cmidrule%s?%r?%C', ''),
        Rule(r'\\(?:top|mid|bottom)rule%s?', '')
    ])


def package_caption_main(*, Rule, RuleList, **_):
    """Return rule list for caption package."""
    return RuleList([
        Rule(r'\\captionof', r'\\caption'),
        Rule(r'\\caption\*', r'\\caption'),
        Rule(r'\\captionlistentry%s?%c', ''),
        Rule(r'\\captionsetup%s?%c', ''),
        Rule(r'\\clearcaptionsetup%s?%c', ''),
        Rule(r'\\showcaptionsetup%C', '')
    ])


def package_cleveref_main(*, Rule, RuleList, **_):
    """Return rule list for cleveref package."""
    ref = 'reference'
    Ref = 'Reference'
    refs = 'references'
    Refs = 'References'
    return RuleList([
        Rule(r'\\cref\*?%C',
             lambda m: fr'{refs} \ref{{{m["c1"]}}} and \ref{{{m["c1"]}}}'
                       if ',' in m['c1'] else fr'{ref} \ref{{{m["c1"]}}}'),
        Rule(r'\\Cref\*?%C',
             lambda m: fr'{Refs} \ref{{{m["c1"]}}} and \ref{{{m["c1"]}}}'
                       if ',' in m['c1'] else fr'{Ref} \ref{{{m["c1"]}}}'),
        Rule(r'\\crefrange\*?%C%C',
             fr'{refs} \\ref{{\g<c1>}} to \\ref{{\g<c2>}}'),
        Rule(r'\\Crefrange\*?%C%C',
             fr'{Refs} \\ref{{\g<c1>}} to \\ref{{\g<c2>}}'),
        Rule(r'\\cpageref\*?%C',
             lambda m:
             fr'pages \pageref{{{m["c1"]}}} and \pageref{{{m["c1"]}}}'
             if ',' in m['c1'] else fr'page \pageref{{{m["c1"]}}}'),
        Rule(r'\\Cpageref\*?%C',
             lambda m:
             fr'Pages \pageref{{{m["c1"]}}} and \pageref{{{m["c1"]}}}'
             if ',' in m['c1'] else fr'Page \pageref{{{m["c1"]}}}'),
        Rule(r'\\cpagerefrange\*?%C%C',
             r'pages \\pageref{{{m["c1"]}}} to \\pageref{{{m["c2"]}}}'),
        Rule(r'\\Cpagerefrange\*?%C%C',
             r'Pages \\pageref{{{m["c1"]}}} to \\pageref{{{m["c2"]}}}'),
        Rule(r'\\(?:lc)?namecref%C', f'{ref}'),
        Rule(r'\\nameCref%C', f'{Ref}'),
        Rule(r'\\(?:lc)?namecrefs%C', f'{refs}'),
        Rule(r'\\nameCrefs%C', f'{Refs}'),
        Rule(r'\\labelc(page|)ref\*?%C',
             lambda m:
             fr'\{m[1]}ref{{{m["c1"]}}} and \{m[1]}ref{{{m["c1"]}}}'
             if ',' in m['c1'] else fr'\{m[1]}ref{{{m["c1"]}}}'),
        Rule(r'\\crefalias%C%C', ''),
        Rule(r'\\crefname%C%C%C', ''),
        Rule(r'\\label%s%c', r'\\label{{\g<c1>}}')
    ])


def package_dtk_logos_main(*, Rule, RuleList, **_):
    """Return rule list for dtk-logos package."""
    return RuleList([
        Rule(r'\\BibTeX', 'BibTeX'),
        Rule(r'\\TikZ', 'TikZ')
    ])


def package_endfloat_main(*, Rule, RuleList, **_):
    """Return rule list for endfloat package."""
    return RuleList([
        Rule(r'\\AtBegin(?:Figures|Tables|DelayedFloats)%C', '')
    ])


def package_enumitem_main(*, Rule, RuleList, **_):
    """Return rule list for enumitem package."""
    return RuleList([
        Rule(r'\\setlist%s?%c', '')
    ])


def package_etoolbox_location(*, Rule, RuleList, **_):
    """Return rule list for fancyvrb package (location phase)."""
    return RuleList([
        Rule(r'\\(new|renew|provide)robustcmd', r'\\\1command')
    ])


def package_etoolbox_main(*, Rule, RuleList, **_):
    """Return rule list for fancyvrb package (location phase)."""
    return RuleList([
        Rule(r'\\robustify%C', ''),
        Rule(r'\\protecting%C', ''),
        Rule(r'\\defcounter%C%C', ''),
        Rule(r'\\deflength%C%C', ''),
        Rule(r'\\(?:After|AtEnd|AfterEnd)Preamble%C', ''),
        Rule(r'\\AfterEndDocument%C', ''),
        Rule(r'\\(?:AtBegin|AtEnd|BeforeBegin|AfterEnd)Environment%C%C', ''),
    ])


def package_fancyvrb_removal(*, Rule, RuleList, auto, **_):
    """Return rule list for fancyvrb package (removal phase)."""
    # List of rules for identifying verbatim environments
    verbatim = RuleList()

    def new_environment(name):
        if auto:
            rule = Rule(r'\\begin{(%s\*?)}' % name, r'\\begin[\1]{verbatim}')
            verbatim.append(rule)
            rule.pattern.print_trace('Created')
        return ''

    def new_command(name):
        if auto:
            rule = Rule(fr'\{name}%s?%c', '')
            verbatim.append(rule)
            rule.pattern.print_trace('Created')
        return ''

    return RuleList([
        Rule(r'\\DefineVerbatimEnvironment%C%C%C',
             lambda m: new_environment(m['c1'])),
        Rule(r'\\CustomVerbatimCommand%C%C%C',
             lambda m: new_command(m['c1'])),
        Rule(r'\\RecustomVerbatim(?:Environment|Command)%C%C%C', ''),
        Rule(r'\\begin{([BL]?Verbatim\*?)}', r'\\begin[\1]{verbatim}'),
        Rule(r'\\begin{(SaveVerbatim\*?)}', r'\\begin[\1]{verbatim}'),
        Rule(r'\\SaveVerb%s?%c', r'\\verb'),
        Rule(r'\\UseVerb%C', '||'),
        Rule(r'\\fvset%C', ''),
        Rule(r'\\[BL]?UseVerbatim%s?%c', '||'),
        Rule(r'\\[BL]?VerbatimInput%s?%c', ''),
        verbatim
    ])


def package_fixme_main(*, Rule, RuleList, **_):
    """Return rule list for fixme package."""
    return RuleList([
        Rule(r'\\fx(?:note|warning|error|fatal)\*%s?%c%c',
             r'\g<c2>\\fixme{\g<c1>}'),
        Rule(r'\\fx(?:note|warning|error|fatal)%s?%c', r'\\fixme{\g<c1>}'),
        Rule(r'\\fixme%s?%c', r'\\footnote{Fix me: \g<c1>}'),
        Rule(r'\\fxsetup%C', ''),
        Rule(r'\\FXRegisterAuthor%C%C%C', ''),
        Rule(r'\\fxloadtargetlayouts%C', ''),
        Rule(r'\\fxusetargetlayout%C', '')
    ])


def package_floatrow_main(*, Rule, RuleList, **_):
    """Return rule list for floatrow package."""
    return RuleList([
        Rule(r'\\floatsetup%s?%c', ''),
        Rule(r'\\(?:re)?newfloatcommand%C%C%s?%s?', ''),
        Rule(r'\\floatbox%s?%c%s?%s?%s?%c%c', r'\g<c2>\n\g<c3>'),
        Rule(r'\\(?:ffigbox|fcapside|ttabbox)%s?%s?%s?%c%c',
             r'\g<c1>\n\g<c2>')
    ])


def package_glossaries_main(*, Rule, RuleList, logger, **_):
    """Return rule list for glossaries package."""
    # rule_X: subrules for \DeclareAcronym rule (X = short, long, short_plural,
    #     short_plural_form, long_plural or long_plural_form)
    # declare_acronym: function implementing the \DeclareAcronym rule; required
    #     because of the rule's complexity
    rule_name = Rule.key_value('name')
    rule_parent = Rule.key_value('parent')
    rule_description = Rule.key_value('description')
    rule_descriptionplural = Rule.key_value('descriptionplural')
    rule_text = Rule.key_value('text')
    rule_first = Rule.key_value('first')
    rule_plural = Rule.key_value('plural')
    rule_firstplural = Rule.key_value('firstplural')
    rule_symbol = Rule.key_value('symbol')
    rule_user1 = Rule.key_value('user1')
    rule_user2 = Rule.key_value('user2')
    rule_user3 = Rule.key_value('user3')
    rule_user4 = Rule.key_value('user4')
    rule_user5 = Rule.key_value('user5')
    rule_user6 = Rule.key_value('user6')

    # Dictionaries where entry values are stored.
    name = {}
    parent = {}
    description = {}
    descriptionplural = {}
    text = {}
    first = {}
    plural = {}
    firstplural = {}
    symbol = {}
    user1 = {}
    user2 = {}
    user3 = {}
    user4 = {}
    user5 = {}
    user6 = {}
    fields = {'name': name, 'parent': parent, 'desc': description,
              'descplural': descriptionplural, 'text': text, 'first': first,
              'plural': plural, 'firstplural': firstplural, 'symbol': symbol,
              'useri': user1, 'userii': user2, 'useriii': user3,
              'useriv': user4, 'userv': user5, 'uservi': user6}
    # Dictionary where first use of entry is recorded.
    used = {}
    # Number of glossary entries that have been printed
    printed = 0

    def glossary_entry(label, keys, desc=None):
        r"""Process \newglossaryentry and similar commands.

        Arguments:
            label -- entry label
            keys -- string of key-value pairs
            desc -- long description (optional)

        Returns:
            Empty string
        """
        if label not in name:
            parent[label] = rule_parent.sub(keys)
            try:
                name[label] = rule_name.sub(keys) or name[parent[label]]
            except KeyError:
                logger.error('Missing name/parent for glossary entry "%s".',
                             label)
                return ''
            if desc is None:
                description[label] = rule_description.sub(keys)
            else:
                description[label] = desc
            descriptionplural[label] = (rule_descriptionplural.sub(keys)
                                        or description[label])
            text[label] = rule_text.sub(keys) or name[label]
            first[label] = rule_first.sub(keys)
            plural[label] = rule_plural.sub(keys) or text[label] + 's'
            firstplural[label] = rule_firstplural.sub(keys)
            if not firstplural[label]:
                if not first[label]:
                    firstplural[label] = plural[label]
                else:
                    firstplural[label] = first[label] + 's'
            if not first[label]:
                first[label] = text[label]
            symbol[label] = rule_symbol.sub(keys)
            user1[label] = rule_user1.sub(keys)
            user2[label] = rule_user2.sub(keys)
            user3[label] = rule_user3.sub(keys)
            user4[label] = rule_user4.sub(keys)
            user5[label] = rule_user5.sub(keys)
            user6[label] = rule_user6.sub(keys)
            used[label] = False
        return ''

    def gls(*, match, label, field=None, field_first=None,
            suffix=None, start=None, post=None):
        """Return field value for specified label (glossaries package).

        If field and field_first are both None and the label is listed in the
        glossary, set used flag and return empty string.

        Arguments:
            match -- matched text, which is returned if glossary has no entry
                for specified label
            label -- label identifying the glossary entry
            field -- field to be returned
            field_first -- alternate field to be returned the first time that
                field_first is specified (field argument must also be
                specified)
            suffix -- text appended to field value
            start -- first three letters of command; if equal to "gls",
                replacement text (field + suffix) is left as is; if equal to
                "Gls", the first letter is capitalized; if equal to "GLS", all
                letters are capitalized
            post -- one-argument function applied to replacement after the
                start-based processing

        Returns:
            replacement string
        """
        start_functions = {'gls': str, 'Gls': str.capitalize,
                           'GLS': str.upper}
        if label in name:
            if field is None and field_first is None:
                # Called only to set used flag
                used[label] = True
                replacement = ''
            elif used[label] or field_first is None:
                replacement = field[label]
            else:
                used[label] = True
                replacement = field_first[label]
            if suffix is not None:
                replacement += suffix
            if start is not None:
                replacement = start_functions[start](replacement)
            if post is not None:
                replacement = post(replacement)
        else:
            replacement = match
        return replacement

    def print_glossary():
        """Return list of glossary entries."""
        nonlocal printed
        entries = []
        for label in sorted(list(name)[printed:], key=str.casefold):
            entries.append('%s: %s' % (name[label].capitalize(),
                                       description[label]))
        printed = len(name)
        if entries:
            glossary = '\n%s\n' % '\n\n'.join(entries)
            replacement = glossary + '\n\\printglossary\n'
        else:
            replacement = r'\printglossary'
        return replacement

    return RuleList([
        Rule(r'\\setacronymstyle%s?%c', ''),
        Rule(r'\\loadglsentries%s?%c', ''),
        Rule(r'\\(?:new|provide)glossaryentry%c%c',
             lambda m: glossary_entry(label=m['c1'], keys=m['c2'])),
        Rule(r'\\long(?:new|provide)glossaryentry%c%c%c',
             lambda m: glossary_entry(label=m['c1'], keys=m['c2'],
                                      desc=m['c3'])),
        Rule(r'\\glspar', r'\n\n'),
        Rule(r'\\glsentrytitlecase%c%c',
             lambda m: gls(match=m[0], label=m['c1'], field=fields[m['c2']],
                           post=str.title)),
        Rule(r'\\glshyperlink%s?%c',
             lambda m: (m['s1'] if m['s1'] != ''
                        else gls(match=m[0], label=m['c1'], field=text))),
        Rule(r"""\\(?P<start>gls|Gls)entry
                 (?P<field>name|text|plural|first|firstplural|desc|descplural
                  |symbol|useri|userii|useriii|useriv|userv|uservi)%c""",
             lambda m: gls(match=m[0], label=m['c1'], field=fields[m['field']],
                           start=m['start'])),
        Rule(r'\\(?P<start>gls|Gls|GLS)[+*]?%s?%c%s?',
             lambda m: gls(match=m[0], label=m['c1'], field=text,
                           field_first=first, suffix=m['s2'],
                           start=m['start'])),
        Rule(r'\\(?P<start>gls|Gls|GLS)pl[+*]?%s?%c%s?',
             lambda m: gls(match=m[0], label=m['c1'], field=plural,
                           field_first=firstplural, suffix=m['s2'],
                           start=m['start'])),
        Rule(r'\\(?P<start>gls|Gls)disp[*+]?%s?%c%c',
             lambda m: gls(match=m[0], label=m['c1'], suffix=m['c2'],
                           start=m['start'])),
        Rule(r'\\glslink[*+]?%s?%c%c', r'\g<c2>'),
        Rule(r'\\Glslink[*+]?%s?%c%c', lambda m: m['c2'].capitalize()),
        Rule(r"""\\(?P<start>gls|Gls|GLS)
                 (?P<field>name|text|plural|first|firstplural|desc
                  |symbol|useri|userii|useriii|useriv|userv|uservi)[*+]?
                 %s?%c%s?""",
             lambda m: gls(match=m[0], label=m['c1'], field=fields[m['field']],
                           suffix=m['s2'], start=m['start'])),
        Rule(r'\\print(?:noidx|unsrt)?glossary%s?',
             lambda m: print_glossary()),
        Rule(r'\\print(?:noidx|unsrt)?glossaries',
             lambda m: print_glossary())
    ])


def package_graphics_main(*, Rule, RuleList, **_):
    """Return rule list for graphics and graphicx packages."""
    return RuleList([
        Rule(r'\\DeclareGraphicsExtensions%C', ''),
        Rule(r'\\DeclareGraphicsRule%C%C%C%C', ''),
        Rule(r'\\graphicspath%C', ''),
        Rule(r'\\includegraphics%s?%s?%c', ''),
        Rule(r'\\rotatebox%s?%c%c', r'\g<c2>'),
        Rule(r'\\scalebox%c%s?%c', r'\g<c2>'),
        Rule(r'\\resizebox\*?%c%c%c', r'\g<c3>')
    ])


package_graphicx_main = package_graphics_main


def package_harpoon_main(*, Rule, RuleList, **_):
    """Return rule list for harpoon packages."""
    return RuleList([
        Rule(r'\\(?:over|under)(?:left|right)harp(?:down)?%C', r'\g<c1>')
    ])


def package_hyperref_main(*, Rule, RuleList, **_):
    """Return rule list for hyperref package."""
    # Key-value rules used by \hypersetup rule.
    value_rules = [Rule.key_value('pdftitle'),
                   Rule.key_value('pdfauthor'),
                   Rule.key_value('pdfsubject'),
                   Rule.key_value('pdfkeywords'),
                   Rule.key_value('pdfproducer'),
                   Rule.key_value('pdfcopyright'),
                   Rule.key_value('pdflicenseurl')]

    def hypersetup(content):
        values = [rule.sub(content) for rule in value_rules]
        return '\n%s\n' % '\n\n'.join([value for value in values if value])

    return RuleList([
        Rule(r'\\pdfbookmark%s?%c%c', r'\g<c1>'),
        Rule(r'\\hypersetup%C', lambda m: hypersetup(m['c1'])),
        Rule(r'\\texorpdfstring%C%C', r'\n\g<c1>\n\n\g<c2>\n'),
        Rule(r'\\ref\*%C', r'\\ref{\g<c1>}'),
        Rule(r'\\pageref\*%C', r'\\pageref{\g<c1>}'),
        Rule(r'\\href%s?%c%c', r'\g<c2>'),
        Rule(r'\\autoref\*?%C', 'X'),
        Rule(r'\\autopageref\*?%C', 'X')
    ])


def package_ifthen_main(*, Rule, RuleList, **_):
    """Return rule list for ifthen package."""
    return RuleList([
        Rule(r'\\newboolean%C', r''),
        Rule(r'\\setboolean%C%C', r''),
        Rule(r'\\equal%C%C', r''),
        Rule(r'\\ifthenelse%C%C%C', r'\g<c2> \g<c3>')
    ])


def package_listings_removal(*, Rule, RuleList, **_):
    """Return rule list for listings package (removal phase)."""
    return RuleList([
        Rule(r'\\lstinline%s?{', r'\\verb}'),
        Rule(r'\\lstinline%s?(?P<delim>.)', r'\\verb\g<delim>'),
        Rule(r'\\begin{lstlisting}', r'\\begin[lstlisting]{verbatim}')
    ])


def package_listings_main(*, Rule, RuleList, **_):
    """Return rule list for listings package (main phase)."""
    return RuleList([
        Rule(r'\\lstloadlanguages%C', ''),
        Rule(r'\\lstset%C', ''),
        Rule(r'\\lstdefinestyle%C%C', ''),
        Rule(r'\\lstinputlisting%s?%c', '')
    ])


def package_makeidx_setup(*, Rule, RuleList, **__):
    """Return rule list for makeidx package (setup phase)."""
    return RuleList([
        Rule(r'\\printindex', '\n\nIndex\n\n' + r'\\printindex')
    ])


def package_makeidx_main(*, Rule, RuleList, **__):
    """Return rule list for makeidx package (main phase)."""
    # Rules for individual index entries.
    noq = r'(?<!(?<!\\)")'  # No non-escaped quote
    text = f'(?:(?!{noq}[!@|]).)*+'
    entry_rules = RuleList([
        # Drop text that determines alphabetical position.
        Rule(fr"""(\A|{noq}!)       # Sub-entry delimiter
                  {text}            # Position string
                  {noq}@            # Format delimiter
                  ({text})          # Formatted text
                  (?=\Z|{noq}[!|])  # Sub-entry delimiter
                  """, r'\1\2'),
        # Keep "see" statements.
        Rule(fr'{noq}\|see%c', r'; see \g<c1>'),
        # Drop page number formatting.
        Rule(fr'{noq}\|.*', ''),
        # Separate sub-entries using commas.
        Rule(fr'{noq}!', ', ')])

    # List where index entries are stored.
    entries = []
    # Number of index entries that have been printed
    printed = 0

    def index_entry(raw_text):
        r"""Process \index command.

        Arguments:
            raw_text -- raw text of index entry

        Returns:
            Empty string
        """
        entries.append(entry_rules.sub(raw_text))
        return ''

    def print_index():
        """Return list of index entries."""
        nonlocal printed
        new_entries = set(entries[printed:]) - set(entries[:printed])
        printed = len(entries)
        content = '\n\n'.join(sorted(new_entries,
                              key=lambda entry: (entry.casefold(),
                                                 entry.swapcase())))
        if content:
            replacement = content + '\n\\printindex\n'
        else:
            replacement = r'\printindex'
        return replacement

    return RuleList([
        Rule(r'\\index%C', lambda m: index_entry(m['c1'])),
        Rule(r'\\printindex', lambda m: print_index())
    ])


def package_mathtools_main(*, Rule, RuleList, **_):
    """Return rule list for mathtools package."""
    return RuleList([
        Rule(r'\\DeclarePairedDelimiter%C%C%C', ''),
        Rule(r'\\DeclarePairedDelimiterX%C%s%C%C%C', ''),
        Rule(r'\\DeclarePairedDelimiterXPP%C%s%C%C%C%C%C', '')
    ])


def package_mdframed_main(*, Rule, RuleList, **_):
    """Return rule list for mdframed package."""
    return RuleList([
        Rule(r'\\mdfdefinestyle%C%C', ''),
        Rule(r'\\newmdenv%s%C', '')
    ])


def package_mfpic_main(*, Rule, RuleList, **_):
    r"""Return rule list for mfpic package."""
    return RuleList([
        Rule(r'\\opengraphsfile%C', ''),
        Rule(r'\\fdef%C%C%C', ''),
        RuleList([
            # Move labels before mpfic environment one at a time.
            Rule(r"""(?s)                              # Period matches \n too.
                 (?P<env>                              # Capture
                     \\begin{mfpic}                    # environment
                     (?:                               # until
                         (?!\\end{mfpic})              # the end
                         (?!\\tlabel[^a-zA-Z])         # or any
                         (?!\\tlabels[^a-zA-Z])        # of the
                         (?!\\axislabels[^a-zA-Z])     # various
                         (?!\\plottext[^a-zA-Z])       # label
                         (?!\\tcaption[^a-zA-Z])       # commands
                         .                             # whichever comes first.
                     )*+
                 )
                 (?:                                            # Capture label
                     \\tlabel(?P<tlabel>%s?(?:%r|%c)%C)         # from \tlabel,
                     |
                     (?P<tlabels>\\tlabels%n{)(?!})             # \tlabels'
                     %s?(?:%r|%C)%C                             # first label,
                     |
                     (?P<axislabels>\\axislabels%C%s?%n{)(?!})  # \axislabels'
                     %C[^{}]+                                   # first label,
                     |
                     \\plottext%s?%c%c                          # \plottext
                     |                                          # or
                     \\tcaption%s?%c                            # \tcaption.
                 )
                 """,
                 r'\g<c2>\g<c4>\g<c6>\g<c7>\g<c9>\n\n'
                 r'\g<env>\g<tlabels>\g<axislabels>',
                 iterative=True),
            # Remove empty \tlabels and \axislabels commands.
            Rule(r"""(?s)                          # Period matches \n too.
                (?P<env>                           # Capture
                    \\begin{mfpic}                 # environment
                    (?:                            # until
                        (?!\\end{mfpic})           # the end
                        (?!\\tlabel[^a-zA-Z])      # or any
                        (?!\\tlabels[^a-zA-Z])     # of the
                        (?!\\axislabels[^a-zA-Z])  # various
                        (?!\\plottext[^a-zA-Z])    # label
                        (?!\\tcaption[^a-zA-Z])    # commands
                        .                          # whichever comes first.
                    )*+
                )
                (?:                                # Remove empty
                    \\tlabels%n{%n}                # \tlabels
                    |                              # and
                    \\axislabels%C%s?%n{}          # \axislabels.
                )
                """, r'\g<env>'),
            # Remove empty mfpic environments.
            Rule(r"""(?s)                      # Period matches \n too.
                \\begin{mfpic}                 # Start of environment.
                (?:                            # Match until
                    (?!\\end{mfpic})           # the end
                    (?!\\tlabel[^a-zA-Z])      # or any
                    (?!\\tlabels[^a-zA-Z])     # of the
                    (?!\\axislabels[^a-zA-Z])  # various
                    (?!\\plottext[^a-zA-Z])    # label
                    (?!\\tcaption[^a-zA-Z])    # commands
                    .                          # whichever comes first.
                )*+
                \\end{mfpic}                   # End of environment.
                """, '')
        ], iterative=True)
    ])


def package_multirow_main(*, Rule, RuleList, **_):
    """Return rule list for multirow package."""
    return RuleList([
        Rule(r'\\multirow%s?%c%s?%c%s?%c', r'\g<c3>')
    ])


def package_natbib_main(*, Rule, RuleList, **_):
    """Return rule list for natbib package."""
    refx = 'Paper X'
    return RuleList([
        # \citet and \Citet
        Rule(r'\\[Cc]itet\*?%s%C', r'%s (\g<s1>)' % refx),
        Rule(r'\\[Cc]itet\*?%C', refx),
        # \citep and \Citep
        Rule(r'\\[Cc]itep\*?%s\[\]%C', r'(\g<s1> %s)' % refx),
        Rule(r'\\[Cc]itep\*?%s%s%C', r'(\g<s1> %s, \g<s2>)' % refx),
        Rule(r'\\[Cc]itep\*?%s%C', r'(%s, \g<s1>)' % refx),
        Rule(r'\\[Cc]itep\*?%C', '(%s)' % refx),
        # \citealt, \citealp, \Citealt and \Citealp
        Rule(r'\\[Cc]iteal[tp]\*?%s\[\]%C', r'\g<s1> %s' % refx),
        Rule(r'\\[Cc]iteal[tp]\*?%s%s%C', r'\g<s1> %s, \g<s2>' % refx),
        Rule(r'\\[Cc]iteal[tp]\*?%s%C', r'%s, \g<s1>' % refx),
        Rule(r'\\[Cc]iteal[tp]\*?%C', refx),
        # Alias
        Rule(r'\\defcitealias%C%C', ''),
        Rule(r'\\citetalias%C', refx),
        Rule(r'\\citepalias%C', '(%s)' % refx),
        # Others
        Rule(r'\\citenum%C', 'X'),
        Rule(r'\\citetext%C', r'(\g<c1>)'),
        Rule(r'\\[Cc]iteauthor\*?%C', 'Authors'),
        Rule(r'\\[Cc]itefullauthor%C', 'Authors'),
        Rule(r'\\citeyearpar%C', r'(\\citeyear\g<c1>)'),
        Rule(r'\\citeyear%C', '2020')
    ])


def package_pdfpages_main(*, Rule, RuleList, **_):
    """Return rule list for pdfpages package."""
    return RuleList([
        Rule(r'\\includepdf%s?%c', ''),
        Rule(r'\\includepdfmerge%s?%c', ''),
        Rule(r'\\includepdfset%C', '')
    ])


def package_pgfplots_main(*, Rule, RuleList, **_):
    """Return rule list for pgfplots package."""
    return RuleList([
        Rule(r'\\usepgfplotslibrary%C', ''),
        Rule(r'\\pgfplotsset%C', '')
    ])


def package_scalerel_main(*, Rule, RuleList, **_):
    """Return rule list for scalerel package."""
    return RuleList([
        Rule(r'\\(?:scale|stretch)rel\*%s?%c%c', r'\g<c1>'),
        Rule(r'\\(?:scale|stretch)rel%s?%c%c', r'\g<c1>\g<c2>'),
        Rule(r'\\(?:scale|stretch)to%s?%c%c', r'\g<c1>')
    ])


def package_siunitx_main(*, Rule, RuleList, **_):
    r"""Return rule list for siunitx package."""
    def format_list(raw_list):
        # Join elements using commas and "and".
        values = raw_list.split(';')
        return ' and '.join([', '.join(values[:-1]), values[-1]])

    def angle(raw_list):
        result = ''
        if ';' in raw_list:
            # Angle in degree-minute-second notation
            degrees, minutes, seconds = raw_list.replace(' ', '').split(';')
            if degrees:
                result += degrees + '°'
            if minutes:
                result += minutes + "'"
            if seconds:
                result += seconds + '"'
        else:
            # Angle in decimal notation
            result = raw_list + '°'
        return result

    return RuleList([
        Rule(r'\\sisetup%C', ''),
        Rule(r'\\ang%s?%c', lambda m: angle(m['c1'])),
        Rule(r'\\(?:complex)?num%s?%c', r'\g<c1>'),
        Rule(r'\\numlist%s?%c', lambda m: format_list(m['c1'])),
        Rule(r'\\numproduct%s?%c', r'\g<c1>'),
        Rule(r'\\numrange%s?%c%c', r'\g<c1> to \g<c2>'),
        Rule(r'\\(?:unit|si)%s?%c', ''),
        Rule(r'\\(?:qty|complexqty|SI)%s?%c%c', r'\g<c1>'),
        Rule(r'\\(?:qty|SI)list%s?%c%c', lambda m: format_list(m['c1'])),
        Rule(r'\\(?:qty|SI)product%s?%c%c', r'\g<c1>'),
        Rule(r'\\(?:qty|SI)range%s?%c%c%c', r'\g<c1> to \g<c2>'),
        Rule(r'\\DeclareSIUnit%s?%C%c', ''),
        Rule(r'\\DeclareSI(?:Prefix|Power)%C%c%c', ''),
        Rule(r'\\DeclareSIQualifier%C%c', ''),
        Rule(r'\\tablenum%s?%c', r'\g<c1>'),
    ])


def package_soul_main(*, Rule, RuleList, **_):
    r"""Return rule list for soul package."""
    return RuleList([
        Rule(r'\\soulregister%C%C', ''),
        Rule(r'\\soulfont%C%C', ''),
        Rule(r'\\soulaccent%C', '')
    ])


def package_subcaption_main(*, Rule, RuleList, **_):
    """Return rule list for subcaption package."""
    return RuleList([
        Rule(r'\\subcaption%s?%c', r'\\caption[\g<s1>]{\g<c1>}')
    ])


def package_subfig_main(*, Rule, RuleList, **_):
    """Return rule list for subfig package."""
    return RuleList([
        Rule(r'\\subfloat%s?%s?%c', r'\\caption[\g<s1>]{\g<s2>}\n\g<c1>\n'),
        Rule(r'\\subref\*?%C', r'\\ref{\g<c1>}'),
    ])


def package_tikz_setup(*, Rule, RuleList, **_):
    """Return rule list for Tikz package (setup phase).

    Pre-process node commands so brace cleanup rule does not remove braces of
    %c argument: put backslash before every node command, and remove "at"
    keyword. Also remove two %r arguments, although not strictly needed.
    """
    # label and options: used by node rule
    # node: used by rule for tikzpicture environment
    label = Rule(r'[^:]*+:', '')
    options = Rule.key_value('label|pin')
    node = RuleList([
        Rule(r"""(?s)                 # Period matches \n too.
             (?P<head>\A[^\[]*+)      # Move content of first argument in []
             %s                       # before \begin{tikzpicture}.
             """,
             lambda m: (label.sub(options.sub(m['s1']))
                        + '\n\n' + m['head'] + ' '),
             iterative=True),
        Rule(r'[\ \\]node(?![a-zA-Z])', r'\\node'),
        RuleList([
            Rule(r'\\node\+{0,2}%r', r'\\node'),
            Rule(r'\\node%n at %n\+{0,2}%r', r'\\node'),
            Rule(r'\\node%n foreach[^{]*+%c', r'\\node{')
        ], iterative=True)
    ])
    return RuleList([
        Rule(r"""(?s)                     # Period matches \n too.
             (?P<env>                     # Entire environment.
                 \\begin{tikzpicture}%s?  # Start delimiter.
                     .*?
                 \\end{tikzpicture}       # End delimiter.
             )
             """,
             lambda m: node.sub(m['env']))
    ])


def package_tikz_main(*, Rule, RuleList, **_):
    r"""Return rule list for TikZ package (main phase).

    The node command can appear standalone as \node or as part of a \path
    command without the leading backslash. The text is moved to the end of the
    paragraph (next blank line).
    """
    return RuleList([
        Rule(r'\\usetikzlibrary%C', ''),
        Rule(r'\\tikzstyle.+?=%s', ''),
        Rule(r'\\tikzset%C', ''),
        Rule(r"""(?s)                        # Period matches \n too.
             (?P<env>                        # Capture
                 \\begin{tikzpicture}%s?     # environment
                 (?:                         # until
                     (?!\\end{tikzpicture})  # the end or a node label.
                     (?!\\node%c)
                     .
                 )*+
             )
             \\node%c                        # Capture node label.
             """, r'\g<c2>\n\n\g<env>', iterative=True),
        Rule(r"""(?s)                     # Period matches \n too.
             \\begin{tikzpicture}         # Start of environment.
             (?:                          # Skip environment until
                 (?!\\end{tikzpicture})   # the end
                 (?![\ \\]node[^a-zA-Z])  # or an unprocessed node label.
                 .
             )*+
             \\end{tikzpicture}           # Match the end.
             """, '')
    ])


def package_ulem_main(*, Rule, RuleList, **_):
    """Return rule list for ulem package."""
    return RuleList([
        # \markoverwith is replaced by a space so following text is not merged
        # with \bgroup command that normally precedes it.
        Rule(r'\\markoverwith%C', ' '),
        Rule(r'\\uline%C', r'\g<c1>'),
        Rule(r'\\uuline%C', r'\g<c1>'),
        Rule(r'\\uwave%C', r'\g<c1>'),
        Rule(r'\\sout%C', r'\g<c1>'),
        Rule(r'\\xout%C', r'\g<c1>'),
        Rule(r'\\dashuline%C', r'\g<c1>'),
        Rule(r'\\dotuline%C', r'\g<c1>'),
    ])


def package_url_removal(*, Rule, RuleList, not_escaped, **_):
    """Return rule list for url package.

    Applied at removal phase because URLs may contain % characters.
    """
    escape = Rule(f'{not_escaped}%', r'\%')
    return RuleList([
        Rule(r'\\url%c', lambda m: escape.sub(m['c1'])),
        Rule(r"""
             \\url(?![a-zA-Z])  # Command name (not followed by letter)
             \s*+               # Optional space
             (?P<delim>.)       # Opening delimiter
             (?P<url>(?s:.)*?)  # URL
             (?P=delim)         # Closing delimiter
             """,
             lambda m: escape.sub(m['url'])),
    ])


def package_url_main(*, Rule, RuleList, **_):
    """Return rule list for url package."""
    return RuleList([
        Rule(r'\\urlstyle%C', '')
    ])


def package_xcolor_main(*, Rule, RuleList, **_):
    """Return rule list for xcolor package."""
    return RuleList([
        Rule(r'\\(?:define|provide)color%s?%c%c%c', ''),
        Rule(r'\\(?:define|provide)colors%c', ''),
        Rule(r'\\(?:define|provide)colorset%s?%c%c%c%c', ''),
        Rule(r'\\colorlet%s?%c%s?%c', ''),
        Rule(r'\\(?:page)?color%s?%c', ''),
        Rule(r'\\(?:text|math)color%s?%c%c', r'\g<c2>'),
        Rule(r'\\colorbox%s?%c%c', r'\g<c2>'),
        Rule(r'\\fcolorbox%s?%c%s?%c%c', r'\g<c3>'),
        Rule(r'\\boxframe%c%c%c', '')
    ])


def style_drdc_main(*, Rule, RuleList, **_):
    r"""Return rule list for DRDC bibliography styles.

    Includes a duplicate of the \url rule, because the bibliography style
    provides it if not already defined.
    """
    return RuleList([
        Rule(r'\\in', 'in'),
        Rule(r'\\In', 'In'),
        Rule(r'\\of', 'of'),
        Rule(r'\\and', 'and'),
        Rule(r'\\online', 'online'),
        Rule(r'\\accessdate', 'Access Date'),
        Rule(r'\\masters', "Master's thesis"),
        Rule(r'\\phd', 'Ph.D. thesis'),
        Rule(r'\\U', ''),
        Rule(r'\\numtomonth%C',
             lambda m: ['January', 'February', 'March', 'April', 'May',
                        'June', 'July', 'August', 'September', 'October',
                        'November', 'December'][int(m['c1']) - 1])
    ])


style_drdc_plain_main = style_drdc_main
