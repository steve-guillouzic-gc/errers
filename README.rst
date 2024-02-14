..
   SPDX-FileCopyrightText: 2023 His Majesty in Right of Canada

   SPDX-License-Identifier: LicenseRef-MIT-DND

   This file is part of the ERRERS package.

=========================
ERRERS: Quick Start Guide
=========================

Purpose
=======
ERRERS stands for "Enhanced Review of Reports via Extraction using Rule-based
Substitutions". It extracts text from LaTeX files so as to reduce the number of
false positives when checking grammar and spelling with Microsoft Word or other
software. It is performed through the application of substitution rules based
on regular expressions.

Requirements
============

ERRERS runs on Python 3, more specifically version 3.6 or more recent. Version
3.2 was tested on Microsoft Windows 10 and 11, Apple macOS 14, and Debian
GNU/Linux 12. It uses the third-party regex module if available
(https://pypi.org/project/regex), as it allows for faster execution, but
defaults back to the standard re module if not.

The Python distribution provided by Apple on macOS includes an older version of
the Tkinter GUI library with which ERRERS is not compatible, but it can still
be used in command-line mode. To use ERRERS in GUI mode on that platform, an
alternate version of Python must be installed, such as those available from the
Python website (https://www.python.org/). On macOS 14, it is preferable to use
Python 3.11.7 or more recent, as buttons may become unresponsive with the
version of Tkinter included in earlier versions. There are two workarounds for
the unresponsiveness bug if upgrading Python is not an option: the first is to
use keyboard shortcuts, and the second one is to move the window (which
reactivates the buttons).

ERRERS depends on two third-party Python packages:

regex (all platforms)
   Provides faster and more robust processing of regular expressions; and

pywin32 (Windows only)
   Enables creation of shortcuts and inclusion of a "Check" button to initiate
   grammar and spell check in Microsoft Word.

Installation
============

Option 1
--------

ERRERS is distributed as a platform-independent Python package, which requires
a local Python installation. To install it:

1. Open a command prompt or shell from which Python can be run. For instance,
   with the Anaconda Python distribution, you would choose Programs >>
   Anaconda3 >> Anaconda Prompt in the Windows Start menu.
2. Type ``python3 -m pip install errers`` and press enter. On some systems, you
   may need to use ``py`` or ``python`` rather than ``python3``. You may also
   need to use ``pipx`` rather than ``pip``.
3. Type ``errers --shortcuts`` at the command prompt and press enter.
4. In the shortcut-update window that appears, choose the locations where you
   would like application shortcuts to be created and click "Create". The
   available locations vary from one operating system to another:

   a) On Windows: Desktop, "Send To" menu, and Start menu;
   b) On macOS: user Applications folder, Launchpad, and "Open with" menu; and
   c) On Linux: Desktop (or Home directory), Application menu, and "Open With"
      menu.

5. Copy shortcuts to other locations if desired. For instance, on Windows, one
   of them could be pinned to the taskbar; on macOS, it could be added to the
   Dock.

Option 2
--------

If pip cannot download ERRERS at step 2 above, you may be able to download it
manually from https://pypi.org/project/errers/#files. If so:

1. Obtain the installation file: errers-VERSION-py3-none-any.whl, where VERSION
   represents the version number of ERRERS that you wish to install.
2. Open a command prompt or shell from which Python can be run.
3. At the command prompt, change directory to the location of the installation
   file from step 1.
4. Type ``python3 -m pip install WHEEL`` and press enter, where ``WHEEL`` is
   the name of the installation file from step 1. On some systems, you may need
   to use ``py`` or ``python`` rather than ``python3``. You may also need to
   use ``pipx`` rather than ``pip``.
5. Continue with step 3 to 5 of option 1.

Notes
-----

The installation procedures above fail if regex is not available. On Windows,
they also fail if pywin32 is not available. If for some reason these two
packages cannot be installed, the installation can be forced by using option
``--no-deps`` when calling pip, which omits package dependencies:
``python3 -m pip install --no-deps errers`` or 
``python3 -m pip install --no-deps WHEEL``. Without regex, text extraction will
be slower. Without pywin32 on Windows, shortcut creation will not be available,
and the "Check" button will be missing.

Installation files can also be downloaded from
https://github.com/steve-guillouzic-gc/errers/releases, where pre-release
versions will also be made available.

Local network administrators may offer other methods of installing ERRERS. For
instance, the ERRERS source code is distributed with a script that bundles it
into a standalone Windows application that does not require Python. This is not
covered here, as it is outside the scope of this manual.

Removal
=======

To remove ERRERS:

1. Open a command prompt or shell from which Python can be run. For instance,
   with the Anaconda Python distribution, you would choose Programs >>
   Anaconda3 >> Anaconda Prompt in the Windows Start menu.
2. Type ``errers --shortcuts`` at the command prompt and press enter.
3. In the shortcut-update window that appears, click "Delete" to delete
   application shortcuts. If shortcuts had been copied to other locations, they
   must be deleted manually.
4. Type ``python3 -m pip uninstall errers`` and press enter. On some systems,
   you may need to use ``py`` or ``python`` rather than ``python3``. You may
   also need to use ``pipx`` rather than ``pip``.

Usage
=====

GUI
---

1. Drag the LaTeX file and drop it on one of the shortcuts created during 
   installation, or right-click on the LaTeX file and choose ERRERS under the
   "Send To" menu (on Windows) or "Open with" menu (on macOS and Linux). This
   launches the application GUI with the input file path already filled out.
   Alternately, one can launch the application from one of the shortcuts and
   click on the input field to choose the file.
2. Click on the "Extract" button. This creates a text file named INPUT-dy.txt
   in the same directory as the LaTeX file, where INPUT is the stem of the
   input file name. Errors and warnings are shown in the "Extraction log" box
   at the bottom left of the main window, including a list of remaining LaTeX
   commands (if any). A more detailed log is saved to INPUT-dy-log.txt.
3. Click on the "Copy" button to copy the text file to the clipboard, and paste
   it into a grammar and spell checking application. (Text must be pasted
   before closing ERRERS.) Alternately, on Windows, one can click on the
   "Check" button to load the text file into MS Word and start the grammar and
   spelling check automatically.
4. Errors can be reported to the developer using the email address provided in
   the top left of the window or the command-line help text.

Command-line
------------

ERRERS can also be used from the command-line. Type ``errers -h`` at the
command prompt and press enter for more information.

Customization
=============

The extraction is performed through the application of substitution rules based
on regular expressions. The current set of rules covers the most common LaTeX
commands, and additional rules will be added over time. Rules are created
automatically for LaTeX commands defined in the document using \\newcommand,
\\rewnewcommand, \\providecommand, \\def, \\edef, \\gdef, and \\xdef. In many
cases, there is no need for users to define additional substitution rules.

However, if needed, rules can be defined directly in LaTeX documents; such
rules are applied first and can be used to override those provided with ERRERS
or determined automatically from command definitions. When installed as Python
package rather than standalone application, users can also place custom rules
in a local.py file saved to the rules sub-directory of the ERRERS installation
folder so they can be applied to all their documents.

The substitution rules being based on regular expressions, the first step in 
learning how to create new rules is to look at the re module page: 
https://docs.python.org/3/library/re.html.

The ERRERS package provides LaTeX-specific sequences for use in regular 
expressions:

1. The %c, %r, and %s strings are replaced with patterns that respectively
   match pairs of curly, round, and square brackets with arbitrary content in
   between. The content of these bracket pairs is accessed in substitution
   strings as sequentially numbered named groups: \\g<c1>, \\g<c2>, ... for %c
   placeholders; \\g<r1>, \\g<r2>, ... for %r; and \\g<s1>, \\g<s2>, ... for
   %s.
2. The %C string is replaced with a pattern that, in addition to matching curly
   brackets with arbitrary content, can also match an unbracketed LaTeX command
   or single character. This matches how curly brackets are handled in LaTeX.
   The captured text is accessed using the same sequence of named groups as %c:
   \\g<c1>, \\g<c2>, ...
3. The %h, %n, and %w strings are replaced with patterns that match optional
   white space: %h matches an arbitrary amount of horizontal white space (space
   or tab), including none; %n is similar to %h, but may also include at most
   one newline character; and %w is similar to %n, but may include an arbitrary
   number of newline characters.
4. The %m string is replaced by a pattern that matches the name of LaTeX
   commands (or "macros"). This is used internally by ERRERS but is unlikely to
   be needed in regular substitution rules.

For instance, Rule(r'\\\\foo%C%C', r'\\g<c1>') substitutes each occurrence of a
two-argument \\foo command with the content of its first argument. If the rule
should be applied only when the arguments are in curly brackets, %C should be
replaced with %c. To use it in a given document, add the following line
anywhere in the LaTeX file:

% Rule(r'\\\\foo%C%C', r'\\g<c1>')

Additional information
======================

More information can be found in the user manual:
https://cradpdf.drdc-rddc.gc.ca/PDFS/unc459/p813656_A1b.pdf.

A list of changes from one version to the next is provided in the change log:
https://github.com/steve-guillouzic-gc/errers/blob/main/CHANGELOG.rst.

If you wish to contribute to the development of ERRERS, please see the
CONTRIBUTING file:
https://github.com/steve-guillouzic-gc/errers/blob/main/CONTRIBUTING.rst.

The source code is hosted on GitHub:
https://github.com/steve-guillouzic-gc/errers.

Acknowledgements
================

The following people contributed to the project:

- Patrick Dooley, Pierre-Luc Drouin, Fred Ma, Matthew MacLeod, Paul Melchin,
  and Stephen Okazawa helped brainstorm the name for the tool.
- Janice Lang suggested the original idea for the icon, and Adison Rossiter
  designed it using the Google Poppins font
  (https://fonts.google.com/specimen/Poppins).
- Pierre-Luc Drouin, Joshua Goldman, Fred Ma, and Paul Melchin helped with beta
  testing.
 
License
=======

The ERRERS source code is distributed under the MIT license
(https://spdx.org/licenses/MIT). The LICENSES directory in the source code,
wheel, and source distribution files contains the text of the license.
