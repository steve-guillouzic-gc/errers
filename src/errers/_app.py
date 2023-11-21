# coding=utf-8
#
# SPDX-FileCopyrightText: 2023 His Majesty in Right of Canada
#
# SPDX-License-Identifier: LicenseRef-MIT-DND
#
# This file is part of the ERRERS package.

"""ERRERS: application behind CLI and GUI

This module manages the output and log files. It leverages the engine
sub-package for the actual extraction.

All elements of this module are implementation details that may change in
non-backward-compatible ways between minor or micro version releases.

Constants: text
    _FILE_BUSY

Constants: other
    OUTPATTERN -- default pattern for output file name (%i = root: name of
        input file without extension)

Classes:
    InvalidFilenamePattern -- Invalid pattern for name of output file

Functions:
    extract_and_save -- extract text, and save output and log to file
    set_log_stream -- initialize log stream handler
    valid_input_file -- return whether input file exists and is valid
    output_file_root -- return path of output file (without extension) used by
        the extract_and_save function

The following elements are internal elements of the module.

Constants: logging
    _main_logger -- parent logger to all ERRERS loggers
    _misc_logger -- miscellaneous log messages
    _pattern_logger -- output of patterns option
    _step_logger -- output of steps option
    _trace_logger -- output of trace option

Functions (internal):
    _set_log_files -- initialize log file handlers
    _set_log_levels -- set log levels based on options specified by user
"""

__all__ = ['extract_and_save', 'set_log_stream', 'valid_input_file',
           'output_file_root']

import logging
from pathlib import Path
import re
import sys

try:
    import regex
except ModuleNotFoundError:
    pass

from errers import _engine

# Logging
_main_logger = logging.getLogger('errers')
_misc_logger = logging.getLogger('errers.log')
_pattern_logger = logging.getLogger('errers.patterns')
_step_logger = logging.getLogger('errers.steps')
_trace_logger = logging.getLogger('errers.trace')

# Other constants
OUTPATTERN = '%i-err'


class InvalidFilenamePattern(Exception):
    """Invalid pattern for name of output file.

    Methods:
        __init__: initializer
    """

    def __init__(self, reason):
        """Initialize exception.

        Arguments:
            reason -- reason why pattern is invalid
        """
        message = 'Invalid pattern for name of output file: %s.' % reason
        super().__init__(message)


def extract_and_save(inpath, *, outpattern, patterns, steps, times, trace,
                     verbose, auto, default, local,
                     std_re, timeout, interruption=None):
    r"""Extract text, and save output and log to file.

    Arguments:
        inpath -- path of input file (LaTeX)
        outpattern -- pattern for name of output file (text)
        patterns -- whether to print expanded patterns to patterns file
        steps -- whether to print text to steps file after each rule
        times -- whether to save compilation and run times of regular
            expressions to a CSV file (OUTNAME-times.csv)
        trace -- whether to list patterns and rules to trace file as they
            are run
        verbose -- whether to propagate informational message to the main log
            (if False, only warning and error messages are relayed)
        auto -- whether to define rules automatically for LaTeX commands
            defined in document using \newcommand, \renewcommand,
            \providecommand, \def, \edef, \gdef and \xdef
        default -- whether to apply default rules
        local -- whether to apply local rules
        std_re -- whether to use standard re module even when regex module
            is available
        timeout -- timeout for individual search patterns and substitution
            rules to detect likely catastrophic backtracking
        interruption -- event originating from the main thread indicating that
            the extraction thread must terminate

    Returns:
        name of output file as Path object

    Logging:
        Each of the loggers used by the extractor module is written to a
        different log file:
            errers.trace is saved to OUTNAME-trace.txt if trace activated
            errers.steps is saved to OUTNAME-steps.txt if steps activated
            errers.log is always saved to OUTNAME-log.txt
        The first two files are created only if the level for the corresponding
        logger is set to logging.DEBUG.
    """
    # Select regular expression module
    if 'regex' in sys.modules and not std_re:
        re_module = regex
    else:
        re_module = re
    # Define file names
    outroot = str(output_file_root(inpath, outpattern))
    out_path = Path(outroot + '.txt')
    misc_path = Path(outroot + '-log.txt')
    patterns_path = Path(outroot + '-patterns.txt') if patterns else None
    steps_path = Path(outroot + '-steps.txt') if steps else None
    trace_path = Path(outroot + '-trace.txt') if trace else None
    times_path = Path(outroot + '-times.csv')
    # Create output folder if needed
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Setup logging
    _set_log_files(misc_path, patterns_path, steps_path, trace_path)
    _set_log_levels(patterns, steps, trace, verbose, re_module.__name__)
    _misc_logger.info('Input folder: %s', inpath.parent.resolve())
    _misc_logger.info('Output folder: %s', out_path.parent)
    _misc_logger.info('Output file: %s', out_path.name)
    if patterns:
        _misc_logger.info('Patterns file: %s', patterns_path.name)
    if steps:
        _misc_logger.info('Steps file: %s', steps_path.name)
    if times:
        _misc_logger.info('Times file: %s', times_path.name)
    if trace:
        _misc_logger.info('Trace file: %s', trace_path.name)
    # Perform extraction and save results
    (text, times_csv) = _engine.extractor.extract(latex_doc=inpath,
                                                  re_module=re_module,
                                                  auto=auto, default=default,
                                                  local=local, timeout=timeout,
                                                  interruption=interruption)
    with open(out_path, 'w', encoding='utf-8') as out_file:
        out_file.write(text)
    if times:
        with open(times_path, 'w', encoding='utf-8', newline='') as times_file:
            times_file.write(times_csv)
    return Path(out_path)


def set_log_stream(stream):
    """Initialize logging stream handler for overarching errers logger.

    Delete existing handlers if any, including of sub-loggers. The logging
    level is initially set to WARNING, but it may be increased later by the
    _set_log_levels function.

    Arguments:
        stream -- logging stream
    """
    _main_logger.handlers.clear()
    _misc_logger.handlers.clear()
    _pattern_logger.handlers.clear()
    _step_logger.handlers.clear()
    _trace_logger.handlers.clear()
    main_handler = logging.StreamHandler(stream)
    main_handler.setLevel(logging.WARNING)
    main_formatter = logging.Formatter('%(levelname)-8s - %(message)s')
    main_handler.setFormatter(main_formatter)
    _main_logger.addHandler(main_handler)


def _set_log_files(misc_path=None, patterns_path=None,
                   steps_path=None, trace_path=None):
    """Initialize logging handlers for log files.

    Log files are setup for the following loggers:
        errers.trace -- output from trace option;
        errers.steps -- output from steps option;
        errers.patterns -- output from patterns option; and
        errers.misc -- everything else.

    Arguments:
        misc_path -- path of miscellaneous logging file
        patterns_path -- path of pattern logging file
        steps_path -- path of steps logging file
        trace_path -- path of trace logging file
    """
    # Miscellaneous log
    if misc_path is not None:
        misc_handler = logging.FileHandler(misc_path, mode='w',
                                           encoding='utf-8')
        misc_handler.setLevel(logging.DEBUG)
        misc_formatter = logging.Formatter('%(levelname)-8s - %(message)s')
        misc_handler.setFormatter(misc_formatter)
        _misc_logger.addHandler(misc_handler)
    # Pattern, Steps and trace logs
    logs = [(patterns_path, _pattern_logger),
            (steps_path, _step_logger),
            (trace_path, _trace_logger)]
    for path, logger in logs:
        if path is not None:
            handler = logging.FileHandler(path, mode='w', encoding='utf-8')
            handler.setLevel(logging.DEBUG)
            logger.addHandler(handler)


def _set_log_levels(patterns, steps, trace, verbose, re_name):
    """Set log levels based on options specified by user.

    Arguments:
        patterns -- whether to print expanded patterns to patterns file
        steps -- whether to print text to steps file after each rule
        trace -- whether to list patterns and rules to trace file as they
            are run
        verbose -- whether to propagate informational message to the main log
            (if False, only warning and error messages are relayed)
        re_name -- name of regular expression module used (re or regex)
    """
    # Set logging levels. Steps and trace are logged only if their levels are
    # set to DEBUG.
    if trace and re_name == 're':
        main_level = logging.DEBUG
    elif verbose:
        main_level = logging.INFO
    else:
        main_level = logging.WARNING
    _main_logger.handlers[0].setLevel(main_level)
    _misc_logger.setLevel(logging.DEBUG)
    _pattern_logger.setLevel(logging.DEBUG if patterns else logging.INFO)
    _step_logger.setLevel(logging.DEBUG if steps else logging.INFO)
    _trace_logger.setLevel(logging.DEBUG if trace else logging.INFO)
    # Never propagate log messages from patterns and steps logger, as their
    # multi-line nature does not blend well with those from other loggers.
    _pattern_logger.propagate = False
    _step_logger.propagate = False
    # Do not propagate trace if using third-party regex module, because
    # automatic detection of catastrophic backtracking is offered when using
    # it.
    _trace_logger.propagate = re_name == 're'


def valid_input_file(inpath):
    """Return whether input file exists and is valid.

    Argument:
        inpath -- path of input file

    Returns:
        Boolean
    """
    return inpath.is_file() and inpath.suffix == '.tex'


def output_file_root(inpath, outpattern):
    """Return path of output file without extension.

    Arguments:
        inpath -- path of input file
        outpattern -- pattern for name of output file (%i = input root)

    Returns:
        Root of output file as Path object
    """
    outstem = outpattern.replace('%i', inpath.stem)
    outroot = inpath.parent.joinpath(outstem).resolve()
    # Check for empty name. (Explicit '.' required if directory name is to be
    # used as root.)
    if not outpattern:
        raise InvalidFilenamePattern('empty name')
    # Check for invalid characters, such as : or ? on Windows.
    invalid = ''
    for char in sorted(set(outstem)):
        try:
            Path(char).stat()
        except FileNotFoundError:
            pass
        except OSError:
            invalid += char
    if invalid:
        raise InvalidFilenamePattern('invalid characters (%s)' % invalid)
    # Check for other empty names, such as '/'.
    try:
        outroot.with_name('name')
    except ValueError:
        raise InvalidFilenamePattern('empty name')
    return outroot
