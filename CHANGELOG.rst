..
   SPDX-FileCopyrightText: 2023 His Majesty in Right of Canada

   SPDX-License-Identifier: LicenseRef-MIT-DND

   This file is part of the ERRERS package.

==================
ERRERS: Change Log
==================

3.2, 2024-02-14
===============

Added
-----
- Add "Delete" button to shortcut window.
- On Windows, when clicking the "Check" button, provide option to change
  language variants -- for instance English (Canada) vs. English (U.S.).
- Document removal procedure in README file.

Changed
-------
- Display name of input file in title bar when specified.
- On Windows, replace "Send To" shortcut by entry in "Open With" menu. Creating
  the latter does not require the pywin32 package.
- On Windows, when clicking the "Check" button, open the modern Editor tool if
  available, defaulting back to the old grammar and spell checker if not.
- On Windows and macOS, open help, options and language windows centered on
  main window. (This was already the case on Linux.)
- Enable navigation to input path and option list using tab key.
- Improve look-and-feel consistency of input fields in main window (especially
  apparent on macOS).
- Turn-off auto-selection of output path pattern when entering field.

Fixed
-----
- Document in help window the use of tab key and spacebar.
- Make key bindings case insensitive.
- On Windows, check if a modal dialog box is open in Word before trying to
  import text file.
- On Windows, reset Word status bar after importing text file.
- On Windows and Linux, display ERRERS icon in title bar of secondary windows
  and dialog boxes too.
- On Linux, fix bug in determination of initial size of main window.
- On macOS, eliminate duplicate icon displayed in Dock when launching from
  application shortcut.
- On macOS, allow launching multiple instances from application shortcut.
- Consolidate all Tkinter code to main thread.
- Avoid garbage collection of Tkinter objects in non-main threads.

3.1.1, 2023-12-22
=================

Fixed
-----
- Eliminate font pixelation in GUI on Windows.
- Make disabling of buttons more apparent on macOS.
- Warn user of button bug on macOS 14 with Python prior to 3.11.7, and list
  workarounds.
- Improve validation of timeout value in GUI.
- Improve validation of pattern for name of output file.
- Lock input fields during extraction.
- Always pass absolute path to Microsoft Word.
- Always log absolute path of input directory.
- Report location of files that are not writable.
- Catch and report on file encoding mismatch.
- Shorten copyright notice.
- Fix bugs in determination of ERRERS version number from Git repository.
- Retain ZIP file as single source file. (Remove .tar.gz file.)
- Update link to user manual.
- Update README files.

3.1, 2023-11-01
===============

- Public release.

Added
-----
- Add license information (MIT license).
- Provide contribution guidelines in new CONTRIBUTING file.
- Add rules for commands:
    - | ulem:
      | \\dashuline, \\dotuline, \\sout, \\uline, \\uuline, \\uwave, \\xout,
      | \\markoverwith

Changed
-------
- Update bundling script to work with PyInstaller 6, which puts all files
  except the executable into an _internal subdirectory.
- Set version number automatically from Git tag when generating Python package.

Fixed
-----
- In main window, properly align field labels to the left of the window.

3.1rc2, 2023-09-25
==================

Added
-----
- Add keyboard shortcuts to GUI elements.
- Add "Quit" button.
- Add rules for commands:
    - | core:
      | \\addtocontents
    - | apacite:
      | \\APACmonth, \\Bby, \\BED, \\BEDS, \\BIn, \\BOthers, \\BothersPeriod
- Add rules for environment:
    - | apacite:
      | APACrefauthors

Changed
-------
- Move description to secondary window accessed via new "Help" button.
- Move options to secondary window and summarize them in a new "Options" field
  in main window.

Fixed
-----
- Fix bug that prevented deletion of log and debugging files on Windows until
  GUI was closed or reset button was pressed.
- Return to new line after printing version number when using --version option
  in CLI.
- On macOS, fix bug in implementation of right-clicking of URLs.
- Check if name pattern of output file is missing.

3.1rc1, 2023-09-01
==================

Added
-----
- Add rules for commands:
    - | core:
      | $$ (TeX command for display math mode),
      | \\textemdash, \\textendash, \\eqnarray,
      | \\centering, \\raggedleft, \\raggedright, \\shortstack,
      | \\noalign, \\indent, \\noindent,
      | \\thepart, \\thechapter, \\thesection, \\thesubsection,
      | \\thesubsubsection, \\theparagraph, \\thesubparagraph, \\thepage,
      | \\thefigure, \\thetable, \\thefootnote, \\thempfootnote, \\theequation,
      | \\theenumi, \\theenumii, \\theenumiii, \\theenumiv
    - | acro:
      | \\acroifT, \\acroifF, \\acroifbooleanT, \\acroifbooleanF,
      | \\acroifallT, \\acroifallF, \\acroifanyT, \\acroifanyF,
      | \\acroiftagT, \\acroiftagF, \\acroifstarredT, \\acroifstarredF,
      | \\acroifusedT, \\acroifusedF, \\acroiffirstT, \\acroiffirstF,
      | \\acroifsingleT, \\acroifsingleF, \\acroifchapterT, \\acroifchapterF,
      | \\acroifpagesT, \\acroifpagesF,
      | \\acronymsmap, \\acronymsmapT, \\acronymsmapF,
      | \\NewAcroTemplate, \\RenewAcroTemplate,
      | \\SetupAcroTemplate, \\SetupNextAcroTemplate
    - | amsmath:
      | \\allowdisplaybreaks
    - | apacite:
      | \\APACaddressInstitution, \\APACbVolEdTR, \\BNUM, \\BNUMS, \\BPG,
      | \\BPGS, \\BTR, \\BTVOL, \\BTVOLS
    - | caption:
      | \\caption*, \\captionof, \\captionlistentry, \\captionsetup,
      | \\clearcaptionsetup, \\showcaptionsetup
    - | cleveref:
      | \\cref, \\Cref, \\crefrange, \\Crefrange, \\cpageref, \\Cpageref,
      | \\cpagerefrange, \\Cpagerefrange, \\namecref, \\nameCref,
      | \\namecrefs, \\nameCrefs, \\lcnamecref, \\lcnamecrefs,
      | \\labecref, \\labecpageref, \\crefalias, \\crefname, \\label
    - | drdc class:
      | \\equalauthormark, \\makeinitializedauthors
    - | etoolbox:
      | \\newrobustcmd, \\renewrobustcmd, \\providerobustcmd,
      | \\robustify, \\protecting, \\defcounter, \\deflength,
      | \\AfterPreamble, \\AtEndPreamble, \\AfterEndPreamble,
      | \\AfterEndDocument, \\AtBeginEnviroment, \\AtEndEnvironment,
      | \\BeforeBeginEnvironment, \\AfterEndEnvironment
    - | fancyvrb:
      | \\DefineVerbatimEnvironment, \\RecustomVerbatimEnvironment,
      | \\CustomVerbatimCommand, \\RecustomVerbatimCommand,
      | \\SaveVerb, \\UseVerb, \\UseVerbatim, \\BUseVerbatim, \\LUseVerbatim,
      | \\VerbatimInput, \\BVerbatimInput, \\LVerbatimInput, \\fvset
    - | fixme:
      | \\fxsetup
    - | floatrow:
      | \\floatsetup, \\newfloatcommand, \\renewfloatcommand,
      | \\floatbox, \\fcapside, \\ffigbox, \\ttabbox
    - | graphics/graphicx:
      | \\resizebox, \\rotatebox
    - | siunitx:
      | \\num, \\numlist, \\numproduct, \\numrange, \\tablenum,
      | \\unit, \\qty, \\qtylist, \\qtyproduct, \\qtyrange,
      | \\ang, \\complexnum, \\complexqty,
      | \\si, \\SI, \\SIlist, \\SIproduct, \\SIrange,
      | \\DeclareSIUnit, \\DeclareSIPrefix,
      | \\DeclareSIPower, \\DeclareSIQualifier
    - | xcolor:
      | \\definecolors, \\definecolorset, \\colorlet,
      | \\providecolor, \\providecolors, \\providecolorset,
      | \\color, \\mathcolor, \\pagecolor, \\textcolor,
      | \\colorbox, \\fcolorbox, \\boxframe
- Add rules for environments:
    - | fancyvrb:
      | Verbatim, BVerbatim, LVerbatim, SaveVerbatim

Changed
------- 
- Change name of application from DeLaTeXify to ERRERS. Change suffix of output
  files from "dy" to "err". Update icon. Rename "conversion" as "extraction".
- Create automatic rules for environments created using \\newenvironment and
  \\renewenvironment commands.
- Create automatic rules for \\the... commands of new counters.
- Amend rules for tikzpicture so labels defined using label and pin options are
  also kept.
- When an exception is raised, log location in hierarchy of rules and patterns,
  if applicable.
- Add vertical space between input and output fields in GUI. Set background of
  input field to white, and write "Click here to select input file." into the
  field when a file has not yet been selected.
- In GUI, label "Extract" button as "Error" rather than "Done" when an error
  occurs.
- Add "location" phase to extraction, applied when files are read and
  responsible for taking note of location of LaTeX command definitions (file
  name and line number).
- When creating rules automatically for LaTeX commands, add a rule that uses
  default value of optional argument when appropriate.
- Omit Microsoft Visual Studio files from bundled application. This requires
  the installation of either Visual Studio or "Microsoft Visual C++ 2015
  Redistributable" package to run application.
- Keep atomic groups and possessive quantifiers in patterns and substitution
  rules when using re module with Python 3.11.5 or later. (They were previously
  kept only when using the regex module.)

Fixed
-----
- Process optional argument of \\definecolor.
- Fix bug that led to node labels with more than one level of internal curly
  brackets to being dropped when using re module.
- Fix bug that led to erroneous removal of bracketed content immediately
  following \\begin{figure} or \\begin{table}.
- Move rule for \\i before accents rules to allow proper composition.
- Catch and log error when attempting to insert secondary file into main LaTeX
  document read from memory.
- Replace %C placeholder by %c after optional %s to avoid matching opening
  square bracket when using re module and mandatory argument contains more than
  one level of internal curly brackets. Similarly replace %C by %c in rules for
  tikzpicture environment.
- In DRDC documents, omit pre-defined values for future distribution (such as
  goc, dnd, and drdc).
- In DRDC documents, add space after establishment name in list of authors.
- Wrap input path when longer than width of input field.
- Accept optional version argument of \\usepackage command, which comes after
  the package name.
- In rule for \\hypersetup command, allow spaces before equal sign in key-value
  pairs. Also recognize a larger number of keywords.
- Fix bug in automatic creation of rules for LaTeX commands with optional
  argument.
- Fix bug in \\newcounter rule (leftover Vim regular-expression specifier).
- While the %n placeholder matches at most one newline character, allow it to
  match an arbitrary number of lines composed solely of comments.
- Remove white space from around the argument of \\footnote, \\footnotetext,
  \\marginpar, and \\thanks commands, as well as the commenting commands of the
  fixme package, before placing it in parentheses.
- Fix bug in \\tbl rule for interact document class.
- In booktabs package, make trimming argument of \\cmidrule command optional.

3.1b5, 2023-02-15
=================

Added
-----
- Add rules for commands:
    - | core:
      | \\a, \\RequirePackage,
      | \\pagestyle, \\thispagestyle,
      | \\verb (replaced by ||)
    - | amsthm:
      | \\newtheoremstyle, \\theoremstyle
    - | glossaries:
      | \\setacronymstyle, \\loadglsentries
    - | listings:
      | \\lstinline (replaced by ||)
    - | tikz:
      | \\tikzset, \\tikzstyle
- Add rules for environments:
    - | core:
      | tabbing,
      | verbatim (omit content)
    - | listings:
      | lstlisting (omit content)
- Add rules for classes:
    - | drdc:
      | \\rank
- Add rules for following ligatures: ff, fi, fl, ffi, and ffl (not
  LaTeX-specific).
- Support creation of application shortcuts on macOS and Linux.
- Names of capturing groups for content of %c, %C, %s, and %r placeholders can
  be specified explicitly by placing empty named capturing group after
  placeholder; for instance: '%c(?P<custom_name>)'.

Changed
-------
- Improve reporting of runtime exceptions during shortcut creation.
- Referring to capturing groups by index in replacement patterns no longer
  supported when using %c, %C, %s, and %r placeholders.
- Make \\author command of drdc document class an alias of its \\authors
  command.
- Split setup rule function into three: core_insertion, core_removal and
  core_setup.
- Rename core, cleanup_braces, and cleanup rule functions as core_main,
  core_cleanup_braces, and core_cleanup, respectively.
- Add suffix to name of class, package, and style rule functions to indicate
  when they are to be applied: insertion, removal, setup, main, and cleanup.
- Add optional phase argument to document rules to specify when they are to be
  applied: insertion, removal, setup, main, and cleanup.
- Log names of rule functions as they are run.
- Rename not_in_comment argument of rule functions as not_commented. Add a
  similar not_escaped argument.
- Replace delatexify-shortcuts by --shortcuts option to help with command
  autocompletion at command line.

Fixed
-----
- Allow matching of non-bracketed content, with %C placeholder, before closing
  curly bracket.
- Add space after colon in rule for \\item[].
- Support starred versions of align, alignat, flalign, gather, and multline
  environments of amsmath package.
- Remove call to Path.with_stem method in processing of "Copy Log" button,
  because it was introduced in Python 3.9.
- Remove white padding on left and right sides of shortcut window.
- Process rules for math environments earlier (setup phase rather than main) to
  prevent automatic rules from inserting dollar signs into them before their
  removal.
- Fix output of number of matches to times file.
- Replace \\i with a regular i rather than a dot-less i, because the latter
  does not compose properly with accents.
- Move rules for \\url command to removal phase so URLs with % characters are
  processed correctly.
- Omit space before percent signs to avoid issues in URLs.
- Modify rules for printing glossaries and indexes so all entries are printed
  with re module even when more than two levels of curly braces are present.
- Fix bug in default rule for one-argument commands that made it match the
  first argument of multi-argument commands when using re module.
- Replace \\clearpage, \\cleardoublepage, and \\newpage by two newlines rather
  than just removing them.
- Detect language before checking grammar when opening converted text in
  Microsoft Word.
- Run launch of Microsoft Word and creation of shortcuts in other threads so
  busy cursor is displayed.

3.1b4, 2023-01-16
=================

Added
-----
- Add rules for commands:
    - | core:
      | \\( \\) \\[ \\] \\{ \\} \\>
      | \\MakeLowercase, \\MakeUppercase,
      | \\clearpage, \\cleardoublepage, \\newpage, \\enlargethispage,
      | \\Huge, \\huge, \\LARGE, \\Large, \\large, \\normalsize,
      | \\small, \\footnotesize, \\scriptsize, \\tiny,
      | \\numberwithin, \\newtheorem
    - | acronym:
      | \\acrodef
    - | graphics and graphicx:
      | \\DeclareGraphicsRule
    - | makeidx package:
      | \\index, \\printindex
- Add rules for environments:
    - | core:
      | math
- Log number of times each remaining command appears in converted text.

Changed
-------
- Sort entries generated by glossaries package.
- In convert function, allow LaTeX input to be specified as string or path.

Fixed
-----
- Process commands inserting reserved characters during cleanup rather than
  setup.
- Recognize command names composed of non-letters when identifying braces that
  do not encapsulate command arguments.
- Replace tilde by space only if not preceded by backslash.
- When matching percent signs (for comments), check if character matched by
  rule is preceded by one, two or three backslashes rather than checking only
  for a single backslash.
- Fix bug in calculation of minimum window height.

3.1b3, 2022-12-23
=================

Added
-----
- Add "Copy" button that copies converted text to clipboard.
- Create rules automatically for commands defined in LaTeX document using
  \\def, \\edef, \\gdef, and \\xdef.
- Add initial support for package: glossaries.
- Add rules for the following spacing commands in setup: 
      | \\, \\: \\; \\!,
      | \\thinspace, \\medspace, \\thickspace,
      | \\negthinspace, \\negmedspace, \\negthickspace
- Add rules for more accents.
- Add rule that replaces %m by pattern that matches the name of LaTeX commands
  ("m" stands for "macros").
- Add rule that replaces %C by pattern that matches non-bracketed LaTeX command
  or character in addition to matching arbitrary content in curly brackets.
- Replace %c by %C in most rules.
- Add option to create a %o-patterns.txt file that lists the expanded
  matching patterns (%o = stem of output file name).
- Report location of error in replacement string when available. (This was
  already done for matching patterns.)
- Provide function to create pattern and rule classes for users who would like
  to experiment with them outside of DeLaTeXify.
- Log document rules as they are read.

Changed
-------
- Replace "Shortcuts" button with separate application.
- Replace "Email log" button with "Copy log", which copies log to clipboard.
- Reduce size of conversion log and move it to the left of the GUI, while
  moving the controls to the right, to reduce window size -- which was an issue
  on macOS.
- Wrap conversion log dynamically up resize.
- Print unexpanded form of matching pattern in error messages and in steps,
  times, and trace files.
- Indent trace file to indicate hierarchy of replacement function calls.
- Use UTF-8 encoding explicitly in all output files.
- Replace DEFAULT flag of Rule objects by an argument to rule functions.
- Replace "flags" argument of Rule and RuleList object initializers with an
  "iterative" argument.
- Write patterns and replacements strings as raw strings in log files only if
  they contain backslashes.
- Allow escaped quotes in document rules.
- Increase resolution of title-bar icon in macOS and Linux.

Fixed
-----
- Ignore Unicode errors when reading LaTeX log file.
- Detect and log when Tk library is missing or too old rather than crash.
- Create output directory if it does not exist yet.
- Catch and log errors that were previously ignored silently.
- Prevent empty window from flashing on screen at startup.

3.1b2, 2022-10-21
=================

Fixed
-----
- Fix bug that led to pywintypes.error when win32api.pyd file did not contain
  version information.

3.1b1, 2022-10-18
=================

Added
-----
- Generate rules automatically for commands defined in LaTeX document using
  \\newcommand, \\renewcommand, and \\ensurecommand.
- Add rules for commands:
    - | core:
      | \\ensuremath
- Add automatic detection of catastrophic backtracking using a timeout for
  individual matching patterns and conversion rules (with third-party regex
  module only).
- Add status bar indicating elapsed time during conversion, which can be used
  to detect catastrophic backtracking when using re module.
- Add "Reset" button to GUI.
- Add description of software to GUI and CLI with link to user manual and
  contact information.
- Use logging module for log messages. Save log to file in addition to
  streaming to standard error. Save steps and trace to file (when used).
- Add verbose option, which increases the level of detail streamed to the
  conversion box or standard error.
- Add automatic clearing of Python COM cache (on Microsoft Windows) when facing
  COM errors.
- Add DeLaTeXify icon to title bar in GUI.
- Reorganize as package. 
- Provide a function as part of the Application Programming Interface (API)
  that performs the conversion without writing anything to the file system.
- Add configuration files for creation of sdist and wheel packages.

Changed
-------
- Change default location of input file dialog to current working directory,
  and change initial working directory of shortcuts on Microsoft Windows to
  Document folder.
- Change default pattern for output file (%i-dy.txt rather than %i.txt, where
  %i = stem of input file name).
- Change matching pattern for document rules so only white space is allowed
  between the comment character (%) at the beginning of line and the beginning
  of the word Rule. Document rules can now be commented out using "%%".
- Updated and added several log messages.
- Group debugging options into three groups: logging, conversion rules, and
  regular expression module.
- Rename "Debugging log" to "Conversion log" and move it to the right of the
  window.
- Increase initial size of conversion log box.
- Make dependency on pywin32 optional; without it, Microsoft-Windows-specific
  GUI elements are omitted.
- Change function signature of rule functions following reorganization as
  package. They now access all classes and objects that they need via keyword
  arguments.

Removed
-------
- Remove support for Python 2.7 and 3.2 to 3.5.
- Remove "Save log" button from GUI, since it is now saved automatically.
- Remove ability to create shortcut from CLI (was on Microsoft Windows only).
- Remove obsolete LaTeX._unpercent rule.

Fixed
-----
- Fix bug that prevented user from seeing error message when exception was
  thrown during GUI initialization.
- Make rule that removes non-command curly braces iterative with the regex
  module, so inner-most braces are not left behind when a pair of braces is
  located within another pair.
- Run conversion in another thread so busy cursor is also displayed on
  Microsoft Windows.

3.0b9, 2022-08-25
=================

Added
-----
- Add rules for commands:
    - | core:
      | \\- (discretionary hyphen)
    - | fixme package:
      | \\FXRegisterAuthor, \\fxloadtargetlayouts, \\fxusetargetlayout
- Add limited support for packages array (\\newcolumntype) and siunitx
  (\\sisetup).
- Add visual cues to GUI to indicate that conversion is in progress.

Changed
-------
- Change shebang line from python to python3 in accordance with PEP 394.

Fixed
-----
- Fix bug in detection of Microsoft Outlook.
- Fix bugs in \\input and \\bibliography rules.

3.0b8, 2022-08-23
=================

Added
-----
- Add error message when clicking on "Check" button if Microsoft Word not
  found (on Microsoft Windows).
- Add error message when clicking on "Email log" button if Microsoft Outlook
  not found (on Microsoft Windows).
- Add support for creation of shortcuts when application is frozen (on
  Microsoft Windows).
- Create PyInstaller configuration files for Microsoft Windows.

3.0b7, 2022-05-25
=================

Fixed
-----
- Fix bug in rule for acro package (\\iacs and \\iacl commands).

3.0b6, 2022-03-03
=================

Removed
-------
- Remove dependency on "six" package.

Fixed
-----
- Fix bug in rules for old DRDC document classes.
- Fix bug in determination of rule location in LaTeX document.

3.0b5, 2022-02-28
=================

Added
-----
- Add support for name of consolidated DRDC document class (drdc).

Fixed
-----
- Fix bug that made GUI exit on exceptions.
- Fix bug in exception handling of local rules.

3.0b4, 2020-05-12
=================

Added
-----
- Add initial support for Interact class (Taylor & Francis).
- Add initial support for packages: apacite, endfloat, fixme, natbib, subfig.
- Add rules for commands:
    - | core:
      | \\newblock, \\PassOptionsToPackage, \\thanks
    - | booktabs package:
      | \\toprule, \\midrule, \\bottomrule
- Add rules for environments:
    - | amsmath package:
      | align, alignat, flalign, gather, multline

Changed
-------
- Change identification of document class and packages: now obtained from
  LaTeX log file if available, with fallback to LaTeX file if not.
- Change file insertion function so it logs missing files rather than crash.
- Change rules so newline characters after comments and argument-less commands
  are removed when not followed by a blank line.

Fixed
-----
- Fix Unicode conversion bug in trace and error reports with Python 2.

3.0b3, 2020-04-07
=================

Added
-----
- Implement nolocal option (was already present, but inactive).
- Add initial support for packages: dtk-logos, scalerel.
- Add rules for commands:
    - | core:
      | \\LaTeX, \\hyphenation
    - | listings package:
      | \\lstloadlanguages

Changed
-------
- Change default rules so they can process starred commands.
- Modify reading of document rules to allow flags and multiline definitions.

3.0b2, 2019-11-21
=================

Added
-----
- Add "Email log" button to GUI to simplify error reporting.
- Add list of inserted files to log.
- Add initial support for packages: acro, graphics, harpoon, pdfpages, soul.
- Add rules for commands:
    - | core:
      | \\tabularnewline, \\textnormal, \\emph, \\lowercase, \\uppercase,
      | \\underline, \\textup, \\textit, \\textsl, \\textsc, \\textrm,
      | \\textsf, \\texttt, \\textbf, \\textmd
    - | acronym package:
      | \\acfi, \\acsp, \\acfp, \\iac, \\Iac,
      | starred version of \\ac... commands
    - | hyperref package:
      | \\autoref, \\autopageref

Fixed
-----
- Fix bug in interface between tool and MS Word.

3.0b1, 2019-09-13
=================

- Initial internal sharing of version 3 with select beta testers.

3 series (alpha), April to September 2019
=========================================

- Conversion of Vimscript code to Python.

2 series, 2006 to 2019
======================

- Set of substitution rules implemented in Vimscript using regular expressions
  and used solely by package author.

1 series, 2005 (approximately) to 2006
======================================

- Set of fixed-string substitution rules implemented in Visual Basics for
  Application in Microsoft Word and used solely by package author.
