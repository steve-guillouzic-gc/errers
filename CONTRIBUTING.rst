..
   SPDX-FileCopyrightText: 2023 His Majesty in Right of Canada

   SPDX-License-Identifier: LicenseRef-MIT-DND

   This file is part of the ERRERS package.

====================
ERRERS: Contributing
====================

Comments and contributions are welcome. Thank you for your help in further
developing ERRERS.

Comments and bug reports
========================

The main channel for comments, questions, and bug reports is on GitHub, where
the ERRERS source code is hosted:
https://github.com/steve-guillouzic-gc/errers/issues. People without GitHub
accounts can send them to steve.guillouzic@forces.gc.ca.

We particularly appreciate learning about situations where the processing of
LaTeX commands during text extraction leads to spurious grammatical and
spelling errors in Microsoft Word or other grammar and spell checkers. It is
also useful for us to know which LaTeX commands appear textually in your
extracted text, as it will help us prioritize the implementation of rules for
additional LaTeX commands. If you can design and submit substitution rules for
these commands, please do so as it will accelerate their implementation.

Code contributions
==================

We accept code contributions via forks and pull requests on GitHub. If you want
to contribute, please follow the following steps:

1. Fork the official errers repository at the following page:
   https://github.com/steve-guillouzic-gc/errers/fork.
2. Create a local copy of your personal online errers repository using "git
   clone".
3. Create a custom branch in your local repository for your proposed
   contribution.
4. Prepare your contribution by editing the source code as desired and
   committing your edits to your custom branch using "git commit". Edits may be
   committed incrementally as you develop and test your proposal.
5. Once your contribution is ready to be discussed with other developers, make
   sure your commits are pushed to your online errers repository using "git
   push" and submit a pull request at
   https://github.com/steve-guillouzic-gc/errers/pulls. You can continue to
   edit your branch based on the result of the discussion resulting from the
   pull request. There is no need to submit a new pull request.

Note: If you wish to discuss an idea before starting to code, please file an
issue at https://github.com/steve-guillouzic-gc/errers/issues. For more complex
contributions, you should consider filing an issue or submitting a pull request
early in your development process to allow coordination with other contributors
and avoid duplication of effort.

For more information on the fork-and-pull workflow, see for instance
https://www.tomasbeuzen.com/post/git-fork-branch-pull/.

Commit messages
===============

Please follow the seven rules of a great Git commit message described at
https://cbea.ms/git-commit. To quote that page::

   1. Separate subject from body with a blank line
   2. Limit the subject line to 50 characters
   3. Capitalize the subject line
   4. Do not end the subject line with a period
   5. Use the imperative mood in the subject line
   6. Wrap the body at 72 characters
   7. Use the body to explain what and why vs. how

The page above describes the rationale for these rules and links to other pages
that also discuss them.

Coding style
============

We aim to follow PEP 8 -- Style Guide for Python Code
(https://peps.python.org/pep-0008). Please check your code with flake8 before
submitting it. It is also useful to run pylint to help catch potential errors.
A pylintrc configuration file is provided in the src/errers directory.

Makefile
========

A Makefile is provided for macOS and Linux to automate the generation of the
Python wheel and source distribution files. It also creates a LICENSES.txt
file, which provides a compilation of licenses used in the project, and it sets
the ERRERS version number based on Git tags and commit history.

Available make targets:

archive
   generate archive of repository files in their local state
build (default)
   generate distribution packages after generating LICENSES.txt and setting
   version number
clean
   delete temporary files, except archive, distribution packages, and
   _version.py
help
   list Makefile targets
licenses
   generate LICENSES.txt file
purge
   delete all temporary files
version
   set version number from Git repository

If the Makefile is not used, reuse should be called manually to create the
LICENSES.txt file, and the templates/_version.py file should be copied to
src/errers and amended manually to set the version number.

Work environment
================

During development, it is useful to install errers in development mode, also
known as an "editable install". This allows running updated software without
having to reinstall it after every edit. For more information:
https://setuptools.pypa.io/en/latest/userguide/development_mode.html.

It is also useful to work in a virtual environment to isolate the development
environment from the rest of the system. This allows a finer control of the
dependencies used during development and helps ensure that dependencies are
captured properly. For more information:
https://docs.python.org/3/library/venv.html.

Content of root directory
=========================

The root directory of the git repository contains the following directories and
files:

Directories:
   LICENSES/
      Licenses used in project
   bundle/
      Script and configuration files to bundle ERRERS as an executable
   src/
      Source code
   templates/
      Template for _version.py file
   tests/
      Unit tests (early phase of development)

Files:
   .gitignore
      Git configuration files
   CHANGELOG.rst, CONTRIBUTING.rst, README.rst
      Documentation
   Makefile
      Packaging automation
   MANIFEST.in, pyproject.toml, setup.py
      Package configuration

License
=======

By submitting a pull request, you are agreeing to license your own contribution
under the MIT license. Please add your copyright notice to the files that
include your contribution. You are also certifying that you identified
third-party contributions clearly, including the applicable copyright and
licensing terms.

Roadmap
=======

The priority for further development of ERRERS is the creation of a proper
testing framework. The tests subdirectory contains an attempt at testing
substitution rules using pytest, but for only one LaTeX package. We need to
develop a series of tests for all current substitution rules and for the rest
of the ERRERS code base.

We also want to add substitution rules for more LaTeX commands, starting with
the most used LaTeX classes and packages. We also wish to develop a
localization framework so the interface can be translated to other languages.
