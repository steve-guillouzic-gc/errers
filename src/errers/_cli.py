# coding=utf-8
#
# SPDX-FileCopyrightText: 2023 His Majesty in Right of Canada
#
# SPDX-License-Identifier: LicenseRef-MIT-DND
#
# This file is part of the ERRERS package.

"""ERRERS: command-line interface

All elements of this module are implementation details that may change in
non-backward-compatible ways between minor or micro version releases.

Functions:
    run -- run tool in CLI mode

The following elements are internal elements of the module.

Constants: logging
    _misc_logger -- miscellaneous log messages

Classes (internal):
    _ArgumentParser -- argument parser that sends output to GUI if not
        connected to terminal

Functions (internal):
    _help_formatter -- format CLI help message
    _create_parser -- create parser for processing command-line arguments
"""

__all__ = ['run']

import argparse
import logging
from pathlib import Path
import sys

import errers
from errers import _app
from errers import _engine
from errers import _gui


# Logging
_misc_logger = logging.getLogger('errers.log')


def run():
    """Run tool in Command-Line Interface (CLI) mode.

    Run GUI if requested or if no input file is specified.
    """
    # Parse arguments.
    parser = _create_parser()
    args = parser.parse_args()
    # Execute according to specified arguments.
    # pylint: disable=broad-except
    # Reason: exception logged
    _app.set_log_stream(sys.stderr)
    if args.help:
        parser.exit(0, parser.format_help())
    elif args.version:
        parser.exit(0, '%s %s\n' % (errers.SHORTNAME,
                                    errers.__version__))
    elif (args.infile is not None
            and not _app.valid_input_file(args.infile) and not args.gui):
        parser.error('invalid input file')
    elif args.gui or args.shortcuts:
        try:
            if _gui.tk.TkVersion < 8.6:
                _misc_logger.error(
                    'Current python installation provides version %s of Tk '
                    'library, but %s requires 8.6 or more recent. It can '
                    'still be run in command-line mode, but an alternate '
                    'version of Python with a more recent version of Tk must '
                    'be installed to used it in GUI mode. Any of the '
                    'contemporary versions at https://www.python.org/ '
                    'would fulfill that requirement.',
                    _gui.tk.TkVersion, errers.SHORTNAME)
                sys.exit(1)
        except AttributeError:
            _misc_logger.error(
                'Tk library is missing, which prevents %s from running in '
                'GUI mode. It can still be run in command-line mode, but '
                'the Tk package must be installed using your operating '
                "system's package manager to use it in GUI mode.",
                errers.SHORTNAME)
            sys.exit(1)
        if args.shortcuts:
            _gui.update_shortcuts()
        else:
            _gui.run(init_inpath=args.infile,
                     init_outpattern=args.outfile,
                     init_patterns=args.patterns,
                     init_steps=args.steps,
                     init_times=args.times,
                     init_trace=args.trace,
                     init_verbose=args.verbose,
                     init_auto=args.auto,
                     init_default=args.default,
                     init_local=args.local,
                     init_re=args.re,
                     init_timeout=args.timeout)
    else:
        try:
            _app.extract_and_save(
                    inpath=args.infile,
                    outpattern=args.outfile,
                    patterns=args.patterns,
                    steps=args.steps,
                    times=args.times,
                    trace=args.trace,
                    verbose=args.verbose,
                    auto=args.auto,
                    default=args.default,
                    local=args.local,
                    std_re=args.re,
                    timeout=args.timeout)
        except (_engine.extractor.EncodingError,
                _engine.base.CatastrophicBacktracking,
                _app.InvalidFilenamePattern) as err:
            _misc_logger.error(err)
        except _engine.base.RegularExpressionError:
            _misc_logger.error(
                'Extraction interrupted by regular expression error.')
        except PermissionError as err:
            path = Path(err.filename).resolve()
            _misc_logger.error('Cannot write to %s in %s. It may be open in '
                               'another application. If so, please close it '
                               'and try again.',
                               path.name, path.parent)
        except KeyboardInterrupt:
            _misc_logger.error('Extraction interrupted by user.')
        except Exception:
            _misc_logger.exception(
                'Unexpected error: please report to developer.')
            sys.exit(1)


class _ArgumentParser(argparse.ArgumentParser):
    """Argument parser that sends output to GUI if not connected to terminal.

    Methods:
        exit -- terminate program with specified status and message
        error -- print usage message following error
    """

    def exit(self, status=0, message=None):
        """Terminate program.

        Argument:
            status -- program exit status
            message -- message to be printed on exit
        """
        if sys.stderr is None or getattr(sys, 'frozen', False):
            _gui.run(init_log=message)
            sys.exit()
        else:
            super().exit(status, message)

    def error(self, message):
        """Print usage message with description of error.

        Arguments:
            message -- description of error
        """
        if sys.stderr is None or getattr(sys, 'frozen', False):
            self.exit(2, '%s%s: error: %s' % (self.format_usage(), self.prog,
                                              message))
        else:
            super().error(message)

    def parse_args(self):
        """Parse arguments and activate GUI automatically if needed.

        The GUI is activated automatically if no input file is specified,
        standard error is not connected, or the application is frozen.

        Returns:
            Namespace object with argument values
        """
        args = super().parse_args()
        if (args.infile is None or sys.stderr is None
                or getattr(sys, 'frozen', False)):
            args.gui = True
        return args


def _help_formatter(prog):
    """Return formatting object for help text.

    The returned object leaves more room for argument names in help text.

    Argument:
        prog -- program name

    Returns:
        argparse.HelpFormatter object
    """
    return argparse.HelpFormatter(prog, max_help_position=16, width=79)


def _create_parser():
    """Create parser for processing command-line arguments.

    Returns:
        argparse.ArgumentParser object
    """
    parser = _ArgumentParser(
                formatter_class=_help_formatter, add_help=False,
                description="""Extract text from LaTeX file so as to reduce
                number of false positives when checking grammar and spelling
                with Microsoft Word or other software. The extraction is
                performed through application of substitution rules based on
                regular expressions.""",
                epilog=f"""Current substitution rules cover most common
                LaTeX commands, and rules are created automatically for
                commands defined in document. If needed, custom rules can be
                defined directly in LaTeX document or, when
                {errers.SHORTNAME} is installed as Python package rather
                than standalone application, in a local.py file placed in the
                rules sub-directory of its installation folder. More
                information in user manual:
                https://cradpdf.drdc-rddc.gc.ca/PDFS/unc459/p813656_A1b.pdf.
                Questions, comments and suggestions:
                github.com/steve-guillouzic-gc/errers/issues.
                For those without a GitHub account:
                steve.guillouzic@forces.gc.ca.""")

    pos_arg = parser.add_argument_group('Positional argument')
    pos_arg.add_argument('infile', nargs='?', default='',
                         type=lambda path: None if path == '' else Path(path),
                         metavar='INFILE.tex', help='input file')
    general = parser.add_argument_group('General options')
    general.add_argument('--gui', action='store_true',
                         help='launch in GUI mode')
    general.add_argument('--help', '-h', action='store_true',
                         help='show this help message and exit')
    general.add_argument('--outfile', '-o',
                         default=_app.OUTPATTERN, metavar='OUTFILE',
                         help='pattern for name stem of output file (name '
                              'without extension), with %%i standing for name '
                              'stem of input file; .txt extension added '
                              'automatically; default: %(default)s; also '
                              'determines names of log, pattern, step, time, '
                              'and trace files: OUTFILE-log.txt, '
                              'OUTFILE-patterns.txt, OUTFILE-steps.txt, '
                              'OUTFILE-times.txt, and OUTFILE-trace.txt')
    general.add_argument('--shortcuts', action='store_true',
                         help='launch shortcut-update GUI')
    general.add_argument('--version', action='store_true',
                         help='print out version number and exit')
    log = parser.add_argument_group('Debugging options (logging)')
    log.add_argument('--patterns', action='store_true',
                     help='print expanded patterns to OUTFILE-patterns.txt '
                          'as they are compiled, to verify that expansions '
                          'work as expected')
    log.add_argument('--steps', action='store_true',
                     help='print text to OUTFILE-steps.txt after each '
                          'matching rule, to help debug interactions between '
                          'them')
    log.add_argument('--times', action='store_true',
                     help='save compilation and run times of regular '
                          'expressions to OUTFILE-times.csv')
    log.add_argument('--trace', action='store_true',
                     help='list patterns and rules to OUTFILE-trace.txt as '
                          'they are run, to help identify source of '
                          'catastrophic backtracking')
    log.add_argument('--verbose', action='store_true',
                     help='print informational messages to standard error in '
                          'addition to warnings and errors; also stream the '
                          'trace if --trace is specified and the standard re '
                          'module is used (because automatic detection of '
                          'catastrophic backtracking is not available with '
                          'that module)')
    rules = parser.add_argument_group('Debugging options (rule selection)')
    rules.add_argument('--no-auto', action='store_false', dest='auto',
                       help='omit automatic substitution rules for LaTeX '
                            'commands defined in document')
    rules.add_argument('--no-default', action='store_false', dest='default',
                       help='omit default substitution rules, to help debug '
                            'command-specific rules')
    rules.add_argument('--no-local', action='store_false', dest='local',
                       help='omit local substitution rules')
    module = parser.add_argument_group('Debugging options (regular expression '
                                       'module)')
    module.add_argument('--re', action='store_true',
                        help='use standard re module even if third-party '
                             'regex module is available')
    module.add_argument('--timeout', default=_engine.extractor.TIMEOUT,
                        type=float, metavar='SECONDS',
                        help='timeout in seconds for individual search '
                             'patterns and substitution rules used as '
                             'indication of likely catastrophic backtracking '
                             'when using the regex module; default: '
                             '%(default)s seconds')
    return parser
