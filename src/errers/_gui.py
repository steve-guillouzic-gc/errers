# coding=utf-8
#
# SPDX-FileCopyrightText: 2023 His Majesty in Right of Canada
#
# SPDX-License-Identifier: LicenseRef-MIT-DND
#
# This file is part of the ERRERS package.

"""ERRERS: graphical user interface

All elements of this module are implementation details that may change in
non-backward-compatible ways between minor or micro version releases.

Functions:
    run -- start GUI

The following elements are internal elements of the module.

Constants: text
    _UNEXPECTED, _UNEXPECTED_MESSAGE, _UNEXPECTED_DETAIL, _WORD_NOT_FOUND,
    _CORRUPT_GEN_PY, _INVALID_INPUT_FILE, _INVALID_OUTPUT_FILE,
    _FILENAME_REQUIRED, _DESCRIPTION, _MANUAL, _FEEDBACK, _ALTERNATE, _CONTACT,
    _ISSUES, _ISSUES_URL, _CONTACT, _CONTACT_URL, _NOTE_COPY,
    _CLICK_INPUT_FILE, _DEBUGGING, _FILTERED, _MACOS14, _LANGUAGE_VARIANTS

Constants: logging
    _main_logger -- parent logger to all ERRERS loggers
    _misc_logger -- miscellaneous log messages

Classes (internal):
    _MainWindow -- main GUI window
    _HelpWindow -- window for help text
    _OptionsWindow -- window for specifying options
    _LanguageWindow -- window for specifying language variants in document
    _ShortcutWindow -- window for shortcut creation and deletion
    _SectionLabel -- section label in GUI
    _SubSectionLabel -- sub-section label in GUI
    _TextField -- single-line text field in GUI
    _PositiveField -- single-line text field with positive number in GUI
    _Description -- multi-line label
    _Hyperlink -- centred hyperlink
    _LogBox -- multi-line text box in GUI for logging purposes
    _CheckBox -- checkbox in GUI
    _OptionList -- drop-down list in GUI
    _Spacer -- spacer widget in GUI
    _ButtonRow -- row of buttons in GUI
    _Status -- status bar
    _Busy -- context manager displaying a busy cursor in GUI
    _BackgroundTask -- background task running in another thread
    _InterProcessError -- exception raised on inter-process communication error
    _WordNotFoundError -- exception raised when MS Word not found
    _ModalDialogError -- exception raised when a dialog box makes MS Word
        unresponsive
    _Language -- interface to language name from MS Word

Functions (internal):
    _dispatch -- return COM object with early-binding, clearing cache if needed
    _centre_window -- centre one window over another
    _show_error -- custom error dialog box
    _ask_yes_no -- custom yes-no dialog box
"""

__all__ = ['run']

from collections import defaultdict
from concurrent import futures
import ctypes
import functools as ft
import gc
import logging
import os
from pathlib import Path
import platform
import plistlib
import queue
import shutil
import stat
import subprocess as sp
import sys
import textwrap
import time
import threading
import urllib
import webbrowser

try:
    import tkinter as tk
    import tkinter.ttk as ttk
    import tkinter.font
    import tkinter.filedialog
    import tkinter.messagebox
except ModuleNotFoundError:
    pass
try:
    import winreg
except ModuleNotFoundError:
    pass
try:
    import pythoncom
    import win32com.client
    import win32gui
except ModuleNotFoundError:
    pass

import errers
from errers import _app
from errers import _engine


# Logging
_main_logger = logging.getLogger('errers')
_misc_logger = logging.getLogger('errers.log')

# Constants
if platform.system() == 'Darwin':
    MOD_KEY = 'Control'
    _NOTE_URL = ('Note: left-click to open links; right-click or '
                 'control-click to copy.')
else:
    MOD_KEY = 'Alt'
    _NOTE_URL = 'Note: left-click to open links; right-click to copy.'
_UNEXPECTED = 'Unexpected error: please report to developer.'
_UNEXPECTED_CONSOLE = ('Unexpected error: details written to console window. '
                       'Please report to developer.')
_WORD_NOT_FOUND = 'Microsoft Word not found'
_MODAL_DIALOG = ('A dialog box opened in Microsoft Word makes it '
                 'unresponsive. Please close the dialog box and try again.')
_CORRUPT_GEN_PY = ('Inter-process communication error: clearing cache to '
                   'resolve issue. Please restart application and try again.')
_INVALID_INPUT_FILE = 'Invalid input file'
_INVALID_OUTPUT_FILE = 'Pattern required for name of output file'
_FILENAME_REQUIRED = 'Input file name required'
_DESCRIPTION = [
    textwrap.dedent(f"""\
        The {errers.SHORTNAME} acronym stands for {errers.LONGNAME}. The tool
        extracts text from LaTeX files so as to reduce false positives when
        checking grammar and spelling with Microsoft Word or other software.
        Extraction is performed through application of substitution rules based
        on regular expressions."""),
    textwrap.dedent(f"""\
        Current rules cover common LaTeX commands, and additional rules are
        created automatically for those defined in a document. When needed,
        custom rules can be defined manually in the document itself or, when
        {errers.SHORTNAME} is installed as Python package rather than
        standalone application, in a local.py file placed in the rules
        sub-directory of its installation folder."""),
    textwrap.dedent(f"""\
        Keyboard shortcuts are available for buttons, checkboxes, and text
        fields. For most controls, the shortcut is the {MOD_KEY} key combined
        with the underlined letter in the control label. The only exception is
        the Times option, for which the shortcut is {MOD_KEY}+X. In dialog
        boxes, the enter and return keys can also be used for "Yes" and "Ok",
        while the escape key can be used for "No" and "Cancel". Finally, the
        tab key cycles through controls, and the space bar toggles checkboxes
        and activates buttons."""),
    "More information in user manual:"
]
_MANUAL = 'https://cradpdf.drdc-rddc.gc.ca/PDFS/unc459/p813656_A1b.pdf'
_FEEDBACK = 'Questions, comments, and suggestions:'
_ALTERNATE = 'For those without a GitHub account:'
_ISSUES = 'github.com/steve-guillouzic-gc/errers/issues'
_ISSUES_URL = 'https://github.com/steve-guillouzic-gc/errers/issues'
_CONTACT = 'steve.guillouzic@forces.gc.ca'
_CONTACT_URL = ('mailto:steve.guillouzic@forces.gc.ca?Subject=%s'
                % urllib.parse.quote(errers.SHORTNAME + ' '
                                     + errers.__version__))
_NOTE_COPY = textwrap.dedent(f"""\
    Note: copied text remains available for pasting until
    {errers.SHORTNAME} is closed.""")
_CLICK_INPUT_FILE = 'Click here to select input file.'
_DEBUGGING = ('These options are mostly used to debug new substitution rules. '
              'The timeout option may also be helpful on slower computers.')
_FILTERED = ('Unless the verbose option is selected, only warnings and errors '
             'appear below, and informational messages are only saved to the '
             'log file. The log below may be empty after uneventful '
             'extractions.')
_MACOS14 = textwrap.fill(textwrap.dedent("""\
        Starting with macOS 14, it is preferable to use Python 3.11.7 or more
        recent, as buttons may become unresponsive with the version of Tkinter
        included in earlier versions. There are two workarounds for the
        unresponsiveness bug if upgrading Python is not an option: the first is
        to use keyboard shortcuts, and the second one is to move the window
        (which reactivates the buttons)."""), width=1000)
_LANGUAGE_VARIANTS = textwrap.dedent("""\
        Microsoft Word detected the following languages. Where multiple
        variants are available, please select which one to apply.""")


class _MainWindow:
    r"""Main GUI window.

    Widgets are laid out using the grid geometry manager. Two columns are used,
    each of which is subdivided into two columns:

        - In the left column:
            - Section labels are laid out across the two columns.
            - For text fields, the first column contains the labels while the
              second one contains contains the text fields themselves and an
              additional description (if applicable).
            - Check boxes are laid out across the two columns.
            - Buttons are laid out in a row across the two columns.
        - In the right column:
            - The section label is laid out across the two columns.
            - The log box is in the first column, and its scroll bar is in the
              second column.

    Methods:
        __init__ -- window initializer
        reset -- reset GUI to prepare for new extraction
        set_minsize -- set minimum window size
        set_title -- set window title
        ask_input_file -- prompt user for input file
        start_extraction -- start thread for LaTeX to text extraction
        run_extraction -- extract text from LaTeX file
        finalize_extraction -- reset GUI and handle exceptions from extraction
        copy_text -- copy text to clipboard
        copy_log -- copy log to clipboard
        start_check -- start thread for grammar check
        run_check -- launch Microsoft Word and start grammar check
        finalize_check -- handle exceptions from grammar check
        on_delete -- clean up when window is closed
        close -- close GUI, waiting for extraction interruption if needed
        update_time -- update elapsed time in the status bar

    Attributes:
        root -- root widget of window
        log -- text box for standard error log
        _interruption -- event to interrupt extraction thread
        _inpath -- path of input file
        _outpattern -- pattern for output file name
        _outname -- name of output file
        _btn_main -- main row of buttons
        _status -- status bar
        _update -- process waiting to update time in the status bar
        _min_width -- minimum window width
        _min_height_base -- minimum window height excluding height of field for
            input path
    """

    def __init__(self, root, *, init_inpath, init_outpattern, init_patterns,
                 init_steps, init_times, init_trace, init_verbose,
                 init_auto, init_default, init_local,
                 init_re, init_timeout):
        """Initialize main window.

        Arguments:
            root -- parent widget
            init_inpath -- initial value of input file path
            init_outpattern -- initial value of pattern of output file name
            init_patterns -- initial value of patterns option
            init_steps -- initial value of steps option
            init_times -- initial value of times option
            init_trace -- initial value of trace option
            init_verbose -- initial value of verbose option
            init_auto -- initial value of auto option
            init_default -- initial value of default option
            init_local -- initial value of local option
            init_re -- initial value of re option
            init_timeout -- initial value of timeout for search patterns and
                substitution rules
        """
        self.root = root
        # Create hidden options window
        self._options = _OptionsWindow(init_patterns, init_steps, init_times,
                                       init_trace, init_verbose, init_auto,
                                       init_default, init_local, init_re,
                                       init_timeout, self.set_option_list,
                                       lambda: self._opt_list.focus())
        self._options.withdraw()
        # Configure main window
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        frame = ttk.Frame(root)
        frame.grid(row=0, column=0, sticky='news')
        # Set-up a grid with two columns and three rows as follows:
        #   Controls   | Empty
        #   Log        | Log
        #   Status bar | Status bar
        # The left column absorbs the horizontal stretch. The log box and the
        # empty space on the right absorb the vertical stretch.
        controls = ttk.Frame(frame)
        controls.grid(row=0, column=0, sticky='nws')
        log = ttk.Frame(frame)
        log.grid(row=1, column=0, columnspan=2, sticky='news')
        status_bar = ttk.Frame(frame)
        status_bar.grid(row=2, column=0, columnspan=2, sticky='news')
        # Controls
        _SectionLabel(controls, 'Controls')
        self._inpath = _TextField(controls, '', 'Input:', underline=0,
                                  onclick=self.ask_input_file)
        _Spacer(controls)
        self._outpattern = _TextField(controls, init_outpattern, 'Output:',
                                      underline=0,
                                      description='(.txt added automatically; '
                                                  '%i = name of input file)',
                                      onedit=self.reset)
        _Spacer(controls)
        self._opt_list = _TextField(controls, '', 'Options:', underline=5,
                                    onclick=self.ask_options)
        _Spacer(controls)
        buttons = [('extract', 'Extract', 0, self.start_extraction, 'normal'),
                   ('copy text', 'Copy text', 0, self.copy_text, 'disabled'),
                   ('copy log', 'Copy log', 3, self.copy_log, 'disabled'),
                   ('reset', 'Reset', 0, self.reset, 'disabled'),
                   ('help', 'Help', 0, self.help, 'normal'),
                   ('quit', 'Quit', 0, self.on_delete, 'normal')]
        if 'win32com.client' in sys.modules:
            buttons.insert(1, ('check', 'Check', 4,
                               self.start_check, 'disabled'))
        self._btn_main = _ButtonRow(controls, buttons)
        _Spacer(controls)
        _Description(controls, 2, 100, _NOTE_COPY)
        _Spacer(controls, fill=True)
        controls.grid_columnconfigure(1, weight=1)
        # Extraction log
        _SectionLabel(log, 'Extraction log')
        _Description(log, 2, 100, _FILTERED)
        self.log = _LogBox(log, 60, 15)
        log.grid_rowconfigure(2, weight=1)
        log.grid_columnconfigure(0, weight=1)
        # Status bar
        self._status = _Status(status_bar, 'Ready')
        status_bar.grid_columnconfigure(0, weight=1)
        # Done placing widgets
        root.update()
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        # Set initial value and wrap length of input field.
        if init_inpath is None:
            self._inpath.set(_CLICK_INPUT_FILE)
            self._status.set(_FILENAME_REQUIRED)
        elif not _app.valid_input_file(init_inpath):
            _show_error(root=self.root, parent=None,
                        message=_INVALID_INPUT_FILE)
            self._inpath.set(_CLICK_INPUT_FILE)
            self._status.set(_FILENAME_REQUIRED)
        else:
            self._inpath.set(init_inpath)
        self.set_title()
        # Set initial value and wrap length of option list
        self._opt_list.set(self._options.list())
        # Set minimum size
        root.update()
        self._min_width = controls.winfo_width()
        self._min_height_base = (controls.winfo_height()
                                 + self._status.height()
                                 - self._inpath._field.winfo_height()
                                 - self._opt_list._field.winfo_height())
        self.set_minsize()
        # Keyboard shortcuts
        root.bind(f'<{MOD_KEY}-i>', self.ask_input_file)
        root.bind(f'<{MOD_KEY}-I>', self.ask_input_file)
        root.bind(f'<{MOD_KEY}-o>', lambda e: self._outpattern.focus())
        root.bind(f'<{MOD_KEY}-O>', lambda e: self._outpattern.focus())
        root.bind(f'<{MOD_KEY}-n>', self.ask_options)
        root.bind(f'<{MOD_KEY}-N>', self.ask_options)
        root.bind(f'<{MOD_KEY}-e>', lambda e: self.press('extract'))
        root.bind(f'<{MOD_KEY}-E>', lambda e: self.press('extract'))
        root.bind(f'<{MOD_KEY}-c>', lambda e: self.press('copy text'))
        root.bind(f'<{MOD_KEY}-C>', lambda e: self.press('copy text'))
        root.bind(f'<{MOD_KEY}-y>', lambda e: self.press('copy log'))
        root.bind(f'<{MOD_KEY}-Y>', lambda e: self.press('copy log'))
        root.bind(f'<{MOD_KEY}-r>', lambda e: self.press('reset'))
        root.bind(f'<{MOD_KEY}-R>', lambda e: self.press('reset'))
        root.bind(f'<{MOD_KEY}-h>', lambda e: self.press('help'))
        root.bind(f'<{MOD_KEY}-H>', lambda e: self.press('help'))
        root.bind(f'<{MOD_KEY}-q>', lambda e: self.press('quit'))
        root.bind(f'<{MOD_KEY}-Q>', lambda e: self.press('quit'))
        if 'win32com.client' in sys.modules:
            root.bind(f'<{MOD_KEY}-k>', lambda e: self.press('check'))
            root.bind(f'<{MOD_KEY}-K>', lambda e: self.press('check'))

    def press(self, button_name):
        """Visually press button and invoke handler.

        Arguments:
            button_name -- name of button to press
        """
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            button = self._btn_main[button_name]
            button.focus_set()
            button.state(['pressed'])
            self.root.after(100, button.state, ['!pressed'])
            button.invoke()
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def reset(self):
        """Reset GUI to prepare for a new extraction."""
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            self._status.set('Ready')
            self._btn_main['extract'].config(text='Extract', state='normal',
                                             underline=0)
            self._btn_main['copy text'].config(state='disabled')
            self._btn_main['copy log'].config(state='disabled')
            self._btn_main['reset'].config(state='disabled')
            if 'win32com.client' in sys.modules:
                self._btn_main['check'].config(state='disabled')
            self.log.reset()
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def set_minsize(self):
        """Set minimum windows size."""
        self.root.minsize(self._min_width,
                          self._min_height_base
                          + self._inpath._field.winfo_height()
                          + self._opt_list._field.winfo_height() + 180)

    def set_title(self):
        """Set window title.

        Title is set to file name if available, and to application name 
        otherwise.
        """
        inpath = Path(self._inpath.get())
        if _app.valid_input_file(inpath):
            title = inpath.stem
        else:
            title = '%s %s' % (errers.SHORTNAME, errers.__version__)
        self.root.title(title)

    def help(self):
        """Show help window."""
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            help_window = _HelpWindow()
            help_window.transient(self.root)
            _set_icon(help_window)
            help_window.withdraw()
            help_window.update_idletasks()
            _centre_window(self.root, help_window)
            help_window.deiconify()
            help_window.focus_set()
            help_window.grab_set()
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def ask_input_file(self, event):
        """Prompt user for input file."""
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            if self._inpath.locked():
                return
            initial_path = Path(self._inpath.get())
            if initial_path.is_file():
                initialfile = initial_path.name
            else:
                initialfile = ''
            if initial_path.parent.is_dir():
                initialdir = initial_path.parent
            else:
                initialdir = ''
            filename = tk.filedialog.askopenfilename(
                    parent=self.root,
                    title=errers.SHORTNAME + ' Input File',
                    filetypes=[('TeX files', '*.tex')],
                    initialdir=initialdir, initialfile=initialfile)
            # When no file is selected, filename may be an empty string or an
            # empty tuple.
            if len(filename) > 0 and filename != initial_path:
                # Path.resolve is needed because tk_askopenfilename always uses
                # a forward slash as directory separator.
                self._inpath.set(Path(filename).resolve())
                self.set_title()
                self.reset()
                self.root.update()
                self.set_minsize()
            self._inpath.focus()
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def ask_options(self, event):
        """Prompt user for option values.

        Arguments:
            root -- parent widget
        """
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            if self._inpath.locked():
                return
            self._options.transient(self.root)
            _set_icon(self._options)
            self._options.update_idletasks()
            _centre_window(self.root, self._options)
            self._options.deiconify()
            self._options.focus_set()
            self._options.grab_set()
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def set_option_list(self):
        """Update list of option values.

        Arguments:
            root -- parent widget
        """
        self._opt_list.set(self._options.list())
        self.reset()
        self.root.update()
        self.set_minsize()
        self._opt_list.focus()

    def start_extraction(self):
        """Start LaTeX to text extraction in separate thread."""
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            # Reset modification flag of input fields.
            self._inpath._field.edit_modified(False)
            self._outpattern._field.edit_modified(False)
            self._opt_list._field.edit_modified(False)
            # Check if input file path is valid.
            if not Path(self._inpath.get()).is_file():
                _show_error(root=self.root, parent=self.root,
                            message=_INVALID_INPUT_FILE)
                self._inpath.set(_CLICK_INPUT_FILE)
                self.set_title()
                self._status.set(_FILENAME_REQUIRED)
                return
            # Check if pattern for name of output file is valid.
            try:
                outroot = _app.output_file_root(Path(self._inpath.get()),
                                                self._outpattern.get())
            except _app.InvalidFilenamePattern as err:
                _show_error(root=self.root, parent=self.root, message=str(err))
                self._status.set(_INVALID_OUTPUT_FILE)
                return
            # If applicable, ask if output and log files should be overwritten.
            extensions = ['.txt', '-log.txt']
            if self._options.patterns.get():
                extensions.append('-patterns.txt')
            if self._options.steps.get():
                extensions.append('-steps.txt')
            if self._options.times.get():
                extensions.append('-times.csv')
            if self._options.trace.get():
                extensions.append('-trace.txt')
            existing = [str(outroot.stem) + ext
                        for ext in extensions
                        if outroot.with_name(outroot.stem + ext).is_file()]
            if existing:
                all_but_last = ', '.join(existing[:-1])
                last = existing[-1]
                if len(existing) > 2:
                    all_files = ', and '.join([all_but_last, last])
                elif len(existing) == 2:
                    all_files = ' and '.join([all_but_last, last])
                else:
                    all_files = last
                directory = outroot.parent
                message = 'Overwrite %s in %s?' % (all_files, directory)
                extract = _ask_yes_no(root=self.root, parent=self.root,
                                      question=message)
                self.root.focus_set()
            else:
                extract = True
            # Perform extraction.
            if extract:
                self._update = self.root.after(0, self.update_time)
                self._btn_main['extract'].config(
                        text='Extracting', state='disabled',
                        underline=-1)
                self._inpath.lock()
                self._outpattern.lock()
                self._opt_list.lock()
                self._interruption = threading.Event()
                kwargs = dict(inpath=Path(self._inpath.get()),
                              outpattern=self._outpattern.get(),
                              patterns=self._options.patterns.get(),
                              steps=self._options.steps.get(),
                              times=self._options.times.get(),
                              trace=self._options.trace.get(),
                              verbose=self._options.verbose.get(),
                              local=not self._options.nolocal.get(),
                              auto=not self._options.noauto.get(),
                              default=not self._options.nodefault.get(),
                              std_re=self._options.re.get(),
                              timeout=self._options.timeout.get(),
                              interruption=self._interruption)
                finalize = ft.partial(self.finalize_extraction,
                                      outroot=outroot)
                _BackgroundTask(self.root, 'extraction',
                                task=self.run_extraction,
                                kwargs=kwargs,
                                callback=finalize)
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def run_extraction(self, *, inpath, outpattern, patterns, steps, times,
                       trace, verbose, auto, default, local,
                       std_re, timeout, interruption):
        r"""Perform text extraction.

        Arguments:
            inpath -- path of input file (LaTeX)
            outpattern -- pattern for name of output file (text)
            patterns -- whether to print expanded patterns to patterns file
            steps -- whether to print text to steps file after each rule
            times -- whether to save compilation and run times of regular
                expressions to a CSV file (OUTNAME-times.csv)
            trace -- whether to list patterns and rules to trace file as they
                are run
            verbose -- whether to propagate informational message to the main
                log (if False, only warning and error messages are relayed)
            auto -- whether to define rules automatically for LaTeX commands
                defined in document using \newcommand, \renewcommand,
                \providecommand, \def, \edef, \gdef and \xdef
            default -- whether to apply default rules
            local -- whether to apply local rules
            std_re -- whether to use standard re module even when regex module
                is available
            timeout -- timeout for individual search patterns and substitution
                rules to detect likely catastrophic backtracking
            interruption -- event originating from the main thread indicating
                that the extraction thread must terminate

        Returns:
            name of output file as Path object
        """
        return _app.extract_and_save(inpath=inpath,
                                     outpattern=outpattern,
                                     patterns=patterns,
                                     steps=steps,
                                     times=times,
                                     trace=trace,
                                     verbose=verbose,
                                     local=local,
                                     auto=auto,
                                     default=default,
                                     std_re=std_re,
                                     timeout=timeout,
                                     interruption=interruption)

    def finalize_extraction(self, future, outroot):
        """Reset GUI and handle exceptions from extraction.

        Arguments:
            future -- execution of extraction
            outroot -- stem of output file name
        """
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            try:
                try:
                    self._outname = future.result()
                    self._btn_main['copy text'].config(
                            state='normal')
                    if 'win32com.client' in sys.modules:
                        self._btn_main['check'].config(
                                state='normal')
                except Exception:
                    self._outname = outroot.with_suffix('.txt')
                    self._btn_main['extract'].config(
                            text='Error', underline=-1)
                    raise
            except (_engine.extractor.EncodingError,
                    _engine.base.CatastrophicBacktracking) as err:
                _misc_logger.error(err)
            except _engine.base.RegularExpressionError:
                _misc_logger.error('Extraction interrupted by '
                                   'regular expression error.')
            except PermissionError as err:
                path = Path(err.filename).resolve()
                _misc_logger.error('Cannot write to %s in %s. It may '
                                   'be open in another application. '
                                   'If so, please close it and try '
                                   'again.',
                                   path.name, path.parent)
            except _engine.base.Interruption:
                _misc_logger.error(
                        'Extraction interrupted by user.')
            else:
                self._btn_main['extract'].config(text='Done',
                                                 underline=-1)
            finally:
                self._status.set(self._status.get() + ' (Done)')
                self._btn_main['copy log'].config(state='normal')
                self._btn_main['reset'].config(state='normal')
                self._inpath.unlock()
                self._outpattern.unlock()
                self._opt_list.unlock()
                _app.set_log_stream(self.log)
        except Exception:
            _misc_logger.exception(_UNEXPECTED)
        finally:
            # Quitting app is delayed until _interruption event is deleted.
            del self._interruption

    def copy_text(self):
        """Copy text to clipboard."""
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            with _Busy(self.root), \
                 open(self._outname, encoding='utf-8') as text_file:
                self.root.clipboard_clear()
                self.root.clipboard_append(text_file.read())
        except Exception:
            _misc_logger.exception(_UNEXPECTED)
        else:
            self._status.set('Text copied to clipboard')

    def copy_log(self):
        """Copy log to clipboard."""
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            logname = self._outname.parent.joinpath(self._outname.stem
                                                    + '-log.txt')
            with _Busy(self.root), \
                 open(logname, encoding='utf-8') as log_file:
                self.root.clipboard_clear()
                self.root.clipboard_append(log_file.read())
        except Exception:
            _misc_logger.exception(_UNEXPECTED)
        else:
            self._status.set('Log copied to clipboard')

    def start_check(self):
        """Start grammar check in separate thread."""
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            q_detected = queue.SimpleQueue()
            q_selected = queue.SimpleQueue()
            _BackgroundTask(self.root, 'document_review',
                            task=self.run_check,
                            args=(q_detected, q_selected),
                            callback=self.finalize_check)
            self.root.after(0, self.wait_for_languages, q_detected, q_selected)
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def run_check(self, q_detected, q_selected):
        """Launch Microsoft Word and start grammar check.

        Arguments:
            q_detected -- Queue object for detected languages
            q_selected -- Queue object for selected language variants
        """
        constants = win32com.client.constants
        pywintypes = win32com.client.pywintypes
        # Initialize COM libraries for this thread.
        pythoncom.CoInitialize()
        try:
            shell = _dispatch('Wscript.Shell')
        except AttributeError as err:
            raise _InterProcessError from err
        try:
            word = _dispatch('Word.Application')
        except AttributeError as err:
            raise _InterProcessError from err
        except pywintypes.com_error as err:
            raise _WordNotFoundError from err
        # Product language variant
        word_lang_id = word.International(constants.wdProductLanguageID)
        word_lang_variant \
            = _Language(word.Languages(word_lang_id).NameLocal).variant
        # Dictionary languages known to Word
        dic_names = defaultdict(list)
        for dic_lang in word.Languages:
            lang = _Language(dic_lang.NameLocal)
            if lang.base:
                dic_names[lang.base].append(lang.full)
        # Check for dialog boxes that would block document from opening.
        windows = word.Windows
        if (windows.Count and not win32gui.IsWindowEnabled(windows(1).Hwnd)):
            raise _ModalDialogError()
        try:
            # Load document and detect languages.
            doc = word.Documents.Open(str(self._outname.resolve()),
                                      Visible=False)
            doc.DetectLanguage()
            doc_lang_ids = {para.Range.LanguageID for para in doc.Paragraphs}
            doc_langs = {word.Languages(lang_id).NameLocal
                         for lang_id in doc_lang_ids
                         if lang_id != constants.wdUndefined}
            # Prepare language lists for option menus.
            menu_langs = []
            for doc_lang in sorted(doc_langs):
                lang_detected = _Language(doc_lang)
                lang_variants = sorted(dic_names[lang_detected.base])
                try:
                    lang_default \
                        = word.Languages('%s (%s)'
                                         % (lang_detected.base,
                                            word_lang_variant)).NameLocal
                except pywintypes.com_error:
                    lang_default = doc_lang
                menu_langs.append((doc_lang, lang_variants, lang_default))
            # Report on detected languages.
            q_detected.put(menu_langs)
            # Wait for selection of language variants.
            lang_mapping = q_selected.get()
            if lang_mapping is not None:  # None means "cancel check".
                # Apply selected language variants.
                id_mapping = {word.Languages(detected).ID:
                              word.Languages(selected).ID
                              for detected, selected in lang_mapping}
                id_mapping[constants.wdUndefined] = constants.wdUndefined
                for para in doc.Paragraphs:
                    para.Range.LanguageID = id_mapping[para.Range.LanguageID]
                # Show document, reset status bar, and launch review.
                doc.Windows(1).Visible = True
                shell.AppActivate(doc)
                word.StatusBar = False
                try:
                    # Try modern Editor sidebar first.
                    mso = "WritingAssistanceCheckDocument"
                    doc.CommandBars.ExecuteMso(mso)
                except pywintypes.com_error:
                    # Use old spelling and grammar checker as backup.
                    doc.CheckGrammar()
        finally:
            # On exception or cancellation: close document.
            if not doc.Windows(1).Visible:
                doc.Close(SaveChanges=constants.wdDoNotSaveChanges)
                if not word.Documents:
                    word.Quit()

    def wait_for_languages(self, q_detected, q_selected):
        """Open language selection window once detected languages are known.

        Arguments:
            q_detected -- Queue object for detected languages
            q_selected -- Queue object for selected language variants
        """
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            try:
                detected = q_detected.get(block=False)
            except queue.Empty:
                self.root.after(100, self.wait_for_languages,
                                q_detected, q_selected)
            else:
                lang_window = _LanguageWindow(detected, q_selected)
                lang_window.transient(self.root)
                _set_icon(lang_window)
                lang_window.withdraw()
                lang_window.update_idletasks()
                _centre_window(self.root, lang_window)
                lang_window.deiconify()
                lang_window.focus_set()
                lang_window.grab_set()
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def finalize_check(self, future):
        """Handle exceptions from grammar check.

        Arguments:
            future -- execution of grammar check
        """
        try:
            future.result()
        except (_InterProcessError, _WordNotFoundError,
                _ModalDialogError) as err:
            _show_error(root=self.root, parent=self.root, message=str(err))

    def on_delete(self):
        """Clean-up on window closure."""
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            if hasattr(self, '_interruption'):
                self._interruption.set()
                self.root.after(100, self.close)
            else:
                self.close()
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def close(self):
        """Close GUI, waiting for extraction interruption if needed."""
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            if hasattr(self, '_interruption'):
                self.root.after(1000, self.close)
            else:
                _main_logger.handlers.clear()
                self.root.destroy()
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def update_time(self, start=None):
        """Update elapsed time in status bar.

        Arguments:
            start -- start time (now if None)
        """
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            if start is None:
                start = time.monotonic()
            if not self._status.get().endswith(')'):
                self._status.set('Elapsed time: %d s'
                                 % (time.monotonic() - start))
                self._update = self.root.after(100, self.update_time, start)
        except Exception:
            _misc_logger.exception(_UNEXPECTED)


class _HelpWindow(tk.Toplevel):
    """Window with help text."""

    def __init__(self, *args, **kwargs):
        """Initialize help window."""
        width = 85
        super().__init__(*args, **kwargs)
        self.resizable(False, False)
        self.title('%s Help' % errers.SHORTNAME)
        description = ttk.Frame(self)
        _Spacer(description)
        description.grid(row=0, column=0, sticky='news')
        for desc in _DESCRIPTION:
            _Description(description, 2, width, desc)
        _Hyperlink(description, _MANUAL)
        _Description(description, 2, width, _FEEDBACK)
        _Hyperlink(description, _ISSUES_URL, _ISSUES)
        _Description(description, 2, width, _ALTERNATE)
        _Hyperlink(description, _CONTACT_URL, _CONTACT)
        _Description(description, 2, width, _NOTE_URL)
        buttons = [('ok', 'Ok', 0, self.destroy, 'normal')]
        _ButtonRow(description, buttons)
        # Keyboard shortcuts
        self.bind(f'<{MOD_KEY}-o>', lambda e: self.destroy())
        self.bind(f'<{MOD_KEY}-O>', lambda e: self.destroy())
        self.bind('<Return>', lambda e: self.destroy())
        self.bind('<Escape>', lambda e: self.destroy())


class _OptionsWindow(tk.Toplevel):
    r"""Window for option specification.

    Methods:
        __init__ -- initializer
        destroy -- close window rather than destroy
        on_cancel -- cancel changes to option values
        on_ok -- save changes to option values
        list -- return value of enabled options as string

    Attributes:
        patterns -- whether to log expanded patterns as they are compiled
        steps -- whether to log text after each rule
        times -- whether to save compilation and run times to CSV file
        trace -- whether to log Patterns and Rules as they are run
        verbose -- whether to propagate informational message to the main log
            (if False, only warning and error messages are relayed)
        noauto -- whether to omit defining rules automatically for LaTeX
            commands defined in document using \newcommand, \renewcommand,
            \providecommand, \def, \edef, \gdef and \xdef.
        nodefault -- whether to omit default rules
        nolocal -- whether to omit local rules
        re -- whether to use standard re module even if regex is available
        timeout -- timeout for search patterns and substitution rules
        _on_ok -- callback function for Ok button
        _on_cancel -- callback function for Cancel button
        _options -- list of options
        _values -- list of option values
    """

    def __init__(self, init_patterns, init_steps, init_times, init_trace,
                 init_verbose, init_auto, init_default, init_local,
                 init_re, init_timeout, on_ok, on_cancel, *args, **kwargs):
        """Initialize options window.

        Arguments:
            init_patterns -- initial value of patterns option
            init_steps -- initial value of steps option
            init_times -- initial value of times option
            init_trace -- initial value of trace option
            init_verbose -- initial value of verbose option
            init_auto -- initial value of auto option
            init_default -- initial value of default option
            init_local -- initial value of local option
            init_re -- initial value of re option
            init_timeout -- initial value of timeout for search patterns and
                substitution rules
            on_ok -- callback function for Ok button
            on_cancel -- callback function for Cancel button
        """
        super().__init__(*args, **kwargs)
        self.protocol('WM_DELETE_WINDOW', self.on_cancel)
        self.resizable(False, False)
        self.title('%s Options' % errers.SHORTNAME)
        controls = ttk.Frame(self)
        controls.grid(row=0, column=0, sticky='news')
        _Spacer(controls)
        _Description(controls, 2, 100, _DEBUGGING)
        _SectionLabel(controls, 'Logging')
        self.patterns = _CheckBox(controls, init_patterns, 'Patterns: print '
                                  'expanded patterns to %o-patterns.txt '
                                  ' as they are compiled',
                                  underline=0)
        self.steps = _CheckBox(controls, init_steps, 'Steps: print text to '
                               '%o-steps.txt file after each '
                               'modification by a substitution rule',
                               underline=0)
        self.times = _CheckBox(controls, init_times,
                               f'Times ({MOD_KEY}+X): save compilation and '
                               'run times of patterns and rules to '
                               '%o-times.csv file')
        self.trace = _CheckBox(controls, init_trace, 'Trace: list search '
                               'patterns and substitution rules to '
                               '%o-trace.txt file as they are run',
                               underline=0)
        self.verbose = _CheckBox(controls, init_verbose, 'Verbose: print '
                                 'additional information to extraction log '
                                 'in the main window', underline=0)
        _Description(controls, 2, 100, 'Note: %o = name of output file',
                     pady=(5, 0))
        _SectionLabel(controls, 'Substitution rules')
        self.noauto = _CheckBox(controls, not init_auto, 'No auto: omit '
                                'automatic rules for LaTeX commands defined '
                                'in document', underline=3)
        self.nodefault = _CheckBox(controls, not init_default,
                                   'No default: omit default rules',
                                   underline=3)
        if 'errers.rules.local' in sys.modules:
            nolocal_state = 'normal'
        else:
            nolocal_state = 'disabled'
            init_local = False
        self.nolocal = _CheckBox(controls, not init_local,
                                 'No local: omit local rules', nolocal_state,
                                 underline=3)
        _SectionLabel(controls, 'Regular expression module')
        if 'regex' in sys.modules:
            re_state = 'normal'
        else:
            re_state = 'disabled'
            init_re = True
        self.re = _CheckBox(controls, init_re, 're: use standard re module '
                            'rather than third-party regex module', re_state,
                            underline=20)
        self.timeout = _PositiveField(
               root=controls, initial=init_timeout, width=3,
               text='Timeout in seconds for individual search patterns and '
                    'substitution rules (regex module only)',
               underline=5,
               switch=self.re)
        self._on_ok = on_ok
        self._on_cancel = on_cancel
        buttons = [('ok', 'Ok', 0, self.on_ok, 'normal'),
                   ('cancel', 'Cancel', 0, self.on_cancel, 'normal')]
        _ButtonRow(controls, buttons)
        # Save values
        self._options = [self.patterns, self.steps, self.times, self.trace,
                         self.verbose, self.noauto, self.nodefault,
                         self.nolocal, self.re, self.timeout]
        self._values = [option.get() for option in self._options]
        # Keyboard shortcuts
        self.bind(f'<{MOD_KEY}-p>', lambda e: self.patterns.toggle())
        self.bind(f'<{MOD_KEY}-P>', lambda e: self.patterns.toggle())
        self.bind(f'<{MOD_KEY}-s>', lambda e: self.steps.toggle())
        self.bind(f'<{MOD_KEY}-S>', lambda e: self.steps.toggle())
        self.bind(f'<{MOD_KEY}-x>', lambda e: self.times.toggle())
        self.bind(f'<{MOD_KEY}-X>', lambda e: self.times.toggle())
        self.bind(f'<{MOD_KEY}-t>', lambda e: self.trace.toggle())
        self.bind(f'<{MOD_KEY}-T>', lambda e: self.trace.toggle())
        self.bind(f'<{MOD_KEY}-v>', lambda e: self.verbose.toggle())
        self.bind(f'<{MOD_KEY}-V>', lambda e: self.verbose.toggle())
        self.bind(f'<{MOD_KEY}-a>', lambda e: self.noauto.toggle())
        self.bind(f'<{MOD_KEY}-A>', lambda e: self.noauto.toggle())
        self.bind(f'<{MOD_KEY}-d>', lambda e: self.nodefault.toggle())
        self.bind(f'<{MOD_KEY}-D>', lambda e: self.nodefault.toggle())
        self.bind(f'<{MOD_KEY}-l>', lambda e: self.nolocal.toggle())
        self.bind(f'<{MOD_KEY}-L>', lambda e: self.nolocal.toggle())
        self.bind(f'<{MOD_KEY}-m>', lambda e: self.re.toggle())
        self.bind(f'<{MOD_KEY}-M>', lambda e: self.re.toggle())
        self.bind(f'<{MOD_KEY}-u>', lambda e: self.timeout.focus())
        self.bind(f'<{MOD_KEY}-U>', lambda e: self.timeout.focus())
        self.bind(f'<{MOD_KEY}-o>', lambda e: self.on_ok())
        self.bind(f'<{MOD_KEY}-O>', lambda e: self.on_ok())
        self.bind(f'<{MOD_KEY}-c>', lambda e: self.on_cancel())
        self.bind(f'<{MOD_KEY}-C>', lambda e: self.on_cancel())
        self.bind('<Return>', lambda e: self.on_ok())
        self.bind('<Escape>', lambda e: self.on_cancel())

    def on_cancel(self):
        """Restore values prior to callback, which closes window."""
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            for option, value in zip(self._options, self._values):
                option.set(value)
            self.withdraw()
            self.grab_release()
            self._on_cancel()
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def on_ok(self):
        """Save values prior to callback, which closes window."""
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            self.update()  # Process focus-out event of timeout field if needed
            self._values = [option.get() for option in self._options]
            self.withdraw()
            self.grab_release()
            self._on_ok()
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def list(self):
        """Return value of all enabled options as string."""
        checkboxes = ('patterns',
                      'steps',
                      'times',
                      'trace',
                      'verbose',
                      'no auto',
                      'no default',
                      'no local',
                      're')
        options = [label for label in checkboxes
                   if getattr(self, label.replace(' ', '')).get()]
        if not self.re.get():
            options.append('max %g seconds per rule' % self.timeout.get())
        return ', '.join(options)


class _LanguageWindow(tk.Toplevel):
    """Window for specifying language variants in document.

    Attributes:
        _q_selected -- Queue object for reporting selected language variants

    Methods:
        __init__ -- initializer
        on_cancel -- cancel document review
        on_ok -- apply selected langauges and review document
    """

    def __init__(self, detected, q_selected, *args, **kwargs):
        """Initialize language window.

        Arguments:
            detected -- sequence of triplets, where the first element of each
                triplet is the language variant detected by MS Word, the second
                element is the list of variants recognized by Word, and the
                third element is the initial value of the drop-down list
            q_selected -- Queue object for selected language variants
        """
        super().__init__(*args, **kwargs)
        self._q_selected = q_selected
        self.resizable(False, False)
        self.title('%s Language Variants' % errers.SHORTNAME)
        window = ttk.Frame(self)
        window.grid(row=0, column=0, sticky='news')
        _Description(window, 3, 90, _LANGUAGE_VARIANTS)
        window.grid_columnconfigure(0, weight=1)
        window.grid_columnconfigure(2, weight=1)
        # List of languages
        languages = ttk.Frame(window)
        languages.grid(row=1, column=1)
        # Column headers
        bold = tk.font.nametofont('TkDefaultFont').copy()
        bold.configure(weight='bold', size=bold.cget('size') + 2)
        header1 = ttk.Label(languages, text='Detected', font=bold)
        header2 = ttk.Label(languages, text='Selected', font=bold)
        header1.grid(row=0, column=0, padx=5, pady=5)
        header2.grid(row=0, column=1, padx=5, pady=5)
        # Languages
        self._languages = {}
        for lang_doc, lang_variants, lang_default in detected:
            lang_variants = lang_variants.copy()
            lang_variants.remove(lang_doc)
            lang_variants.insert(0, lang_doc)
            if lang_default == lang_doc:
                separator = 1
            else:
                lang_variants.remove(lang_default)
                lang_variants.insert(0, lang_default)
                separator = 2
            self._languages[lang_doc] \
                = _OptionList(languages, lang_doc, lang_variants,
                              initial=lang_default, separators=[separator])
        # Buttons
        _Spacer(languages)
        buttons = [('ok', 'Ok', 0, self.on_ok, 'normal'),
                   ('cancel', 'Cancel', 0, self.on_cancel, 'normal')]
        _ButtonRow(languages, buttons)
        # Keyboard shortcuts
        self.bind(f'<{MOD_KEY}-o>', lambda e: self.on_ok())
        self.bind(f'<{MOD_KEY}-O>', lambda e: self.on_ok())
        self.bind(f'<{MOD_KEY}-c>', lambda e: self.on_cancel())
        self.bind(f'<{MOD_KEY}-C>', lambda e: self.on_cancel())
        self.bind('<Return>', lambda e: self.on_ok())
        self.bind('<Escape>', lambda e: self.on_cancel())

    def on_cancel(self):
        """Cancel document review."""
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            self._q_selected.put(None)
            self.destroy()
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def on_ok(self):
        """Apply selected languages and review document."""
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            mapping = [(detected, selected.get())
                       for detected, selected in self._languages.items()]
            self._q_selected.put(mapping)
            self.destroy()
        except Exception:
            _misc_logger.exception(_UNEXPECTED)


class _ShortcutWindow:
    """Window for shortcut creation and deletion.

    Some shortcuts can also be used as drag-and-drop target for input files.

    Widgets are laid out in the same way as the main window.

    Class methods:
        for_windows -- create shortcut update window for Microsoft Windows
        for_macos -- create shortcut update window for macOS
        for_linux -- create shortcut update window for Linux

    Methods:
        __init__ -- window initializer
        start_update -- start thread for shortcut creation and deletion
        update -- create or delete selected shortcuts
        finalize_update -- close window and handle exceptions
        update_windows -- create or delete shortcut on Windows platform
        update_macos -- create or delete shortcut on macOS platform
        update_linux -- create or delete shortcut on Linux platform

    Attributes:
        root -- root widget of window
        _updaters -- mapping of folder to shortcut update function
        _checkboxes -- list of folder checkboxes

    Reference for Linux shortcuts:
        https://specifications.freedesktop.org/
    """

    def __init__(self, root, updaters, message):
        """Initialize shortcut window.

        Attribute:
            root -- root widget of window
            updaters -- mapping of folder to shortcut update function
            message -- message insert for shortcut window
        """
        self.root = root
        root.resizable(False, False)
        root.title('%s (Version %s)' % (errers.SHORTNAME,
                                        errers.__version__))
        frame = ttk.Frame(self.root)
        frame.grid(row=0, column=0, ipadx=5, sticky='news')
        _SectionLabel(frame, 'Shortcut creation and deletion')
        _Description(frame, 2, 85, textwrap.dedent("""\
            Creating shortcuts is optional, but it streamlines usage by
            providing a simple way to launch the tool and allowing
            drag-and-drop. """))
        _Description(frame, 2, 85, message)
        _Description(frame, 2, 85, textwrap.dedent("""\
            Which application shortcuts would you like to create or delete?
            (Creating shortcuts that already exist updates them to point to
            this %s installation.)""" % errers.SHORTNAME))
        self._updaters = updaters
        self._checkboxes = [_CheckBox(frame, 1, folder)
                            for folder in updaters]
        _ButtonRow(frame, [('create', 'Create', 0,
                            self.start_update, 'normal'),
                           ('delete', 'Delete', 0,
                            ft.partial(self.start_update, delete=True),
                            'normal'),
                           ('cancel', 'Cancel', 2,
                            self.root.destroy, 'normal')])
        root.bind(f'<{MOD_KEY}-c>', lambda e: self.start_update())
        root.bind(f'<{MOD_KEY}-C>', lambda e: self.start_update())
        root.bind(f'<{MOD_KEY}-d>', lambda e: self.start_update(delete=True))
        root.bind(f'<{MOD_KEY}-D>', lambda e: self.start_update(delete=True))
        root.bind(f'<{MOD_KEY}-n>', lambda e: root.destroy())
        root.bind(f'<{MOD_KEY}-N>', lambda e: root.destroy())
        root.bind('<Return>', lambda e: self.start_update())
        root.bind('<Escape>', lambda e: root.destroy())

    @classmethod
    def for_windows(cls, root):
        """Create shortcut creation and deletion window for Microsoft Windows.

        Attribute:
            root -- root widget of window
        """
        updaters = {}
        if 'win32com.client' in sys.modules:
            updaters['Desktop'] = ft.partial(cls.update_windows_other,
                                             folder_name='Desktop')
        updaters['Open With menu'] = cls.update_windows_open_with
        if 'win32com.client' in sys.modules:
            updaters['Start menu'] = ft.partial(cls.update_windows_other,
                                                folder_name='StartMenu')
        message = textwrap.dedent(f"""\
            For instance, right-clicking on a LaTeX file and choosing
            {errers.SHORTNAME} under the "Open With" submenu launches the
            application GUI with the input file path already filled out. """)
        if 'win32com.client' in sys.modules:
            message += textwrap.dedent("""\
                Dragging a LaTeX file and dropping it on a desktop shortcut
                does the same thing.""")
        return cls(root, updaters, message)

    @classmethod
    def for_macos(cls, root):
        """Create shortcut creation and deletion window for macOS.

        Attribute:
            root -- root widget of window
        """
        home = Path.home()
        applications = home.joinpath('Applications')
        updaters = {'User applications folder, Launchpad, '
                    'and "Open with" menu':
                    ft.partial(cls.update_macos, folder=applications)}
        message = textwrap.dedent(f"""\
            For instance, dragging a LaTeX file and dropping it on one of the
            shortcuts launches the application GUI with the input file path
            already filled out. Right-clicking on a LaTeX file and choosing
            {errers.SHORTNAME} under the "Open with" menu does the same thing.
            After creation, the shortcut from the Applications folder or the
            Launchpad can be dragged and dropped onto the Dock for easier
            access.""")
        return cls(root, updaters, message)

    @classmethod
    def for_linux(cls, root):
        """Create shortcut creation and deletion window for Linux.

        Attribute:
            root -- root widget of window
        """
        home = Path.home()
        config = Path(os.getenv('XDG_CONFIG_HOME',
                                str(home.joinpath('.config'))))
        user_dirs = config.joinpath('user-dirs.dirs')
        try:
            for line in user_dirs.read_text().splitlines():
                if 'XDG_DESKTOP_DIR' in line:
                    subdir = line.split('=', 1)[1].strip('"').split('/', 1)[1]
                    desktop = home.joinpath(subdir)
                    if desktop == home:
                        desktop = home.joinpath('Desktop')
                    break
        except FileNotFoundError:
            desktop = home.joinpath('Desktop')
        data = Path(os.getenv('XDG_DATA_HOME',
                              str(home.joinpath('.local', 'share'))))
        menu = data.joinpath('applications')
        short = f'{errers.SHORTNAME}.desktop'
        full = f'ca.gc.drdc_rddc.{short}'
        if desktop.exists() and desktop != home:
            updaters = {'Desktop':
                        ft.partial(cls.update_linux,
                                   file_path=desktop.joinpath(short),
                                   chmod=True)}
        else:
            updaters = {'Home':
                        ft.partial(cls.update_linux,
                                   file_path=home.joinpath(short),
                                   chmod=True)}
        if menu.exists():
            updaters['Application menu (under Utilities) '
                     'and "Open With" menu'] \
                    = ft.partial(cls.update_linux,
                                 file_path=menu.joinpath(full),
                                 chmod=False)
        message = textwrap.dedent(f"""\
            For instance, dragging a LaTeX file and dropping it on a desktop
            shortcut launches the application GUI with the input file path
            already filled out. Right-clicking on a LaTeX file and choosing
            {errers.SHORTNAME} under the "Open With" menu does the same thing.
            (Note: The application offers to create a shortcut in the home
            folder if the desktop folder is not found.)""")
        cls(root, updaters, message)

    def start_update(self, delete=False):
        """Start shortcut creation in separate thread.

        Argument:
            delete -- delete rather than create or update shortcut
        """
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            updaters = [updater
                        for checkbox, updater in zip(self._checkboxes,
                                                     self._updaters.values())
                        if checkbox.get()]
            _BackgroundTask(self.root, 'update_shortcuts',
                            task=self.update,
                            args=(updaters, delete),
                            callback=self.finalize_update)
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def update(self, updaters, delete):
        """Create or delete selected shortcuts.

        Argument:
            updaters -- updater functions to run
            delete -- delete rather than create or update shortcut
        """
        for updater in updaters:
            updater(self, delete=delete)

    def finalize_update(self, future):
        """Finalize update by closing window and handling exceptions.

        Argument:
            future -- execution of shortcut update
        """
        try:
            future.result(timeout=0)
        except Exception:
            _misc_logger.exception(_UNEXPECTED)
            _show_error(root=self.root, parent=self.root,
                        message=_UNEXPECTED_CONSOLE)
        finally:
            self.root.after(0, self.root.destroy)

    def update_windows_open_with(self, delete):
        """Add to, or remove from, "Open With" menu on Windows platform.

        Arguments:
            delete -- delete shortcut rather than create or update it
        """
        if delete:
            keys = [
                r'Software\Classes\tex_errers\shell\open\command',
                r'Software\Classes\tex_errers\shell\open',
                r'Software\Classes\tex_errers\shell',
                r'Software\Classes\tex_errers']
            values = [
                (r'Software\Microsoft\Windows\CurrentVersion\Explorer'
                 r'\FileExts\.tex\OpenWithProgids',
                 'tex_errers')]
            for sub_key in keys:
                try:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, sub_key)
                except FileNotFoundError:
                    pass
            for sub_key, sub_sub_key in values:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                      sub_key) as key:
                    try:
                        winreg.DeleteValue(key, sub_sub_key)
                    except FileNotFoundError:
                        pass
        else:
            if getattr(sys, 'frozen', False):
                # App is frozen
                command = '"%s"' % sys.executable
            else:
                # App is not frozen
                pyw = Path(sys.executable).parent.joinpath('pythonw.exe')
                command = ('"%s" -c "import errers; errers._cli.run()"'
                           % pyw)
            keys = [
                (r'Software\Classes\tex_errers\shell\open',
                 'FriendlyAppName',
                 winreg.REG_SZ,
                 'ERRERS'),
                (r'Software\Classes\tex_errers\shell\open\command',
                 '',
                 winreg.REG_SZ,
                 '%s --gui "%%1"' % command),
                (r'Software\Microsoft\Windows\CurrentVersion\Explorer'
                 r'\FileExts\.tex\OpenWithProgids',
                 'tex_errers',
                 winreg.REG_NONE,
                 b'')]
            for sub_key, sub_sub_key, value_type, value in keys:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                      sub_key) as key:
                    winreg.SetValueEx(key, sub_sub_key, 0,
                                      value_type, value)

    def update_windows_other(self, folder_name, delete):
        """Create or delete shortcut on Windows platform.

        Arguments:
            folder_name -- special folder where to create shortcut (should be
                "Desktop", "SendTo" or "StartMenu")
            delete -- delete shortcut rather than create or update it
        """
        # Initialize COM libraries for this thread.
        pythoncom.CoInitialize()
        try:
            shell = _dispatch('Wscript.Shell')
        except AttributeError as err:
            raise _InterProcessError from err
        folder = Path(shell.SpecialFolders(folder_name))
        shortcut_path = folder.joinpath(errers.SHORTNAME + '.lnk')
        if delete:
            shortcut_path.unlink(missing_ok=True)
        else:
            shortcut = shell.CreateShortcut(shortcut_path)
            if getattr(sys, 'frozen', False):
                # App is frozen
                shortcut.TargetPath = '"%s"' % sys.executable
                shortcut.Arguments = '--gui'
            else:
                # App is not frozen
                executable \
                    = Path(sys.executable).parent.joinpath('pythonw.exe')
                shortcut.TargetPath = '"%s"' % executable
                shortcut.Arguments \
                    = '-c "import errers; errers._cli.run()" --gui'
            shortcut.WorkingDirectory = r'%USERPROFILE%\Documents'
            shortcut.IconLocation \
                = str(Path(__file__).parent.joinpath('icon', 'errers.ico'))
            shortcut.Save()

    def update_macos(self, folder, delete):
        """Create or delete shortcut on macOS platform.

        This is done by creating an application using the osacompile utility
        provided by Apple.

        Arguments:
            folder -- folder where to create shortcut
            delete -- delete shortcut rather than create or update it
        """
        tmp = folder.joinpath(f'{errers.SHORTNAME}_tmp.app')
        final = folder.joinpath(f'{errers.SHORTNAME}.app')
        shutil.rmtree(str(tmp), ignore_errors=True)
        shutil.rmtree(str(final), ignore_errors=True)
        if not delete:
            icon_old = tmp.joinpath('Contents', 'Resources',
                                    'droplet.icns')
            icon_new = Path(__file__).parent.joinpath('icon',
                                                      'errers.icns')
            info_plist = tmp.joinpath('Contents', 'Info.plist')
            executable = Path(sys.executable).parent.joinpath('errers')
            script = textwrap.dedent(f"""\
                on run
                    do shell script "{executable} &>/dev/null &"
                end run

                on open LaTeX_file
                    set LaTeX_path to POSIX path of LaTeX_file
                    set command to "{executable} --gui " & LaTeX_path
                    do shell script command & " &>/dev/null &"
                end open""")
            folder.mkdir(parents=True, exist_ok=True)
            sp.run(['osacompile', '-o', str(tmp)], input=script,
                   universal_newlines=True, stderr=sp.PIPE, check=True)
            Path(icon_old).unlink()
            shutil.copy(str(icon_new), str(icon_old.parent))
            with open(info_plist, 'rb') as info_file:
                info = plistlib.load(info_file)
                doc_types = info['CFBundleDocumentTypes']
                doc_extensions = doc_types[0]['CFBundleTypeExtensions']
                doc_extensions[0] = 'tex'
                info['CFBundleName'] = 'ERRERS'
                info['CFBundleIconFile'] = 'errers'
                info['LSUIElement'] = True
            with open(info_plist, 'wb') as info_file:
                plistlib.dump(info, info_file)
            shutil.copytree(str(tmp), str(final))
            shutil.rmtree(str(tmp))

    def update_linux(self, file_path, chmod, delete):
        """Create or delete shortcut on Linux platform.

        Arguments:
            file_path -- path of shortcut file
            chmod -- whether to make the file executable
            delete -- delete shortcut rather than create or update it
        """
        if delete:
            file_path.unlink(missing_ok=True)
        else:
            icon = Path(__file__).parent.joinpath('icon', 'errers.png')
            executable = Path(sys.executable).parent.joinpath('errers')
            content = textwrap.dedent(f"""\
                [Desktop Entry]
                Type=Application
                Name={errers.SHORTNAME}
                Comment={errers.LONGNAME}
                Icon={icon}
                Exec={executable} --gui %f
                MimeType=text/x-tex
                Categories=Utility""")
            file_path.write_text(content)
            if chmod:
                os.chmod(file_path,
                         os.stat(file_path).st_mode | stat.S_IXUSR)


class _SectionLabel:
    """Section label in GUI.

    Method:
        __init__ -- initializer
    """

    def __init__(self, root, text):
        """Initialize section label.

        Widget is added to the last empty row of root.

        Arguments:
            root -- parent widget
            text -- label text
        """
        bold = tk.font.nametofont('TkDefaultFont').copy()
        bold.configure(weight='bold', size=bold.cget('size') + 2)
        label = ttk.Label(root, text=text, font=bold)
        label.grid(row=root.grid_size()[1], column=0, columnspan=2,
                   sticky='w', padx=5, pady=5)


class _SubSectionLabel:
    """Sub-section label in GUI.

    Method:
        __init__ -- initializer
    """

    def __init__(self, root, text, extra_top=0):
        """Initialize sub-section label.

        Widget is added to the last empty row of root.

        Arguments:
            root -- parent widget
            text -- label text
            extra_top -- extra padding on top
        """
        bold = tk.font.nametofont('TkDefaultFont').copy()
        bold.configure(weight='bold')
        label = ttk.Label(root, text=text, font=bold)
        label.grid(row=root.grid_size()[1], column=0, columnspan=2,
                   sticky='w', padx=5, pady=(5 + extra_top, 5))


class _TextField:
    """Single-line text field in GUI, with label and optional description.

    If an onclick handler function is provided, the text field is set to
    readonly and only the handler can modify it.

    Methods:
        __init__ -- initializer
        get -- return value of text field
        set -- set value of text field
        adjust_height -- adjust field height to fit content
        unlock -- unlock field
        lock -- lock field
        focus -- select text and move focus to widget
        next_widget -- move focus to next widget
        previous_widget -- move focus to previous widget
        mod_windows -- indicate how modifier keys should be handled on Windows
        mod_macos -- indicate how modifier keys should be handled on macOS
        mod_linux -- indicate how modifier keys should be handled on Linux
        modifiers -- indicate how modifier keys should be handled on this
            platform (set dynamically)
        keypress -- handle key presses

    Attribute:
        _field -- text field
        _onclick -- handler function for when user clicks on text field
    """

    def __init__(self, root, initial, text, *, description='', onclick=None,
                 onedit=None, underline=-1):
        """Initialize text field.

        Widget is added to the last empty row of root.

        Arguments:
            root -- parent widget
            initial -- initial value
            text -- name of text field
            description -- description of text field
            onclick -- handler function for when user clicks on text field
            onedit -- handler function for when user edits field value
            underline -- index of character to underline
        """
        label = ttk.Label(root, text=text, underline=underline)
        frame = ttk.Frame(root)
        self._onclick = onclick
        self._field = tk.Text(frame, width=30, height=1, wrap=tk.WORD,
                              relief=tk.FLAT, highlightthickness=1,
                              highlightbackground='grey70',
                              font=tk.font.nametofont('TkDefaultFont'))
        desc = ttk.Label(frame, text=description)
        row = root.grid_size()[1]
        label.grid(row=row, column=0, padx=5, sticky='nes')
        frame.grid(row=row, column=1, sticky='news')
        self._field.grid(row=0, column=0, sticky='news')
        desc.grid(row=0, column=1, padx=2.5 if description == '' else 5,
                  sticky='nws')
        frame.grid_columnconfigure(0, weight=1)
        self._field.update_idletasks()
        self.set(initial)
        if onclick is None:
            # Prevent newline characters from being entered, and adjust field
            # height automatically. The keypress method takes care of both
            # when onclick is present.
            self._field.bind('<Return>', lambda e: 'break')
            self._field.bind('<KeyRelease>', lambda e: self.adjust_height())
        else:
            self._field.config(insertofftime=10, insertontime=0)
            self._field.bind('<Key>', self.keypress)
        self._field.bind('<Tab>', self.next_widget)
        self._field.bind('<Shift-Tab>', self.previous_widget)
        if onclick is not None:
            self._field.bind('<Button-1>', onclick)
        if onedit is not None:
            self._field.bind('<<Modified>>', lambda *args: onedit())

    def get(self):
        """Return value of text field."""
        return self._field.get('1.0', 'end-1c')

    def set(self, value):
        """Set value of text field."""
        self._field.delete('1.0', 'end')
        self._field.insert("1.0", value)
        self.adjust_height()

    def adjust_height(self):
        """Adjust field height to fit content."""
        tcl_command = '%s count -update -displaylines 1.0 end' % self._field
        display_lines = int(self._field.tk.eval(tcl_command))
        self._field.configure(height=display_lines)

    def unlock(self):
        """Unlock field."""
        self._field.configure(state='normal')

    def lock(self):
        """Lock field."""
        self._field.configure(state='disable')

    def locked(self):
        """Is field locked?"""
        return str(self._field.cget('state')) == 'disable'

    def focus(self):
        """Set focus to this field."""
        self._field.focus_set()

    def next_widget(self, event):
        """Move focus to next widget."""
        event.widget.tk_focusNext().focus()
        return 'break'

    def previous_widget(self, event):
        """Move focus to previous widget."""
        event.widget.tk_focusPrev().focus()
        return 'break'

    def mod_windows(self, state):
        """Indicate how modifier keys should be handled on Windows.

        Arguments:
            state -- state of modifier keys reported by event

        Return 'block', 'dialog', or 'pass' depending on whether the character 
        should be blocked, trigger the dialog box, or let through.
        """
        shift = bool(state & 0x1)
        right_alt = state & 0x20004 == 0x20004
        left_alt = state & 0x20000 and not right_alt
        control = state & 0x4 and not right_alt
        if control or (shift + right_alt + left_alt) > 1:
            return 'block'
        elif left_alt:
            return 'pass'
        else:
            return 'dialog'

    def mod_macos(self, state):
        """Indicate how modifier keys should be handled on macOS.

        Arguments:
            state -- state of modifier keys reported by event

        Return 'block', 'dialog', or 'pass' depending on whether the character 
        should be blocked, trigger the dialog box, or let through.
        """
        shift = bool(state & 0x1)
        control = bool(state & 0x4)
        command = bool(state & 0x8)
        option = bool(state & 0x10)
        function = bool(state & 0x40)
        if command or function:
            return 'block'
        elif control:
            return 'pass'
        else:
            return 'dialog'

    def mod_linux(self, state):
        """Indicate how modifier keys should be handled on Linux.

        Arguments:
            state -- state of modifier keys reported by event

        Return 'block', 'dialog', or 'pass' depending on whether the character 
        should be blocked, trigger the dialog box, or let through.
        """
        shift = bool(state & 0x1)
        control = bool(state & 0x4)
        left_alt = bool(state & 0x8)
        windows = bool(state & 0x40)
        right_alt = bool(state & 0x80)
        if control or windows or (shift + left_alt + right_alt) > 1:
            return 'block'
        elif left_alt:
            return 'pass'
        else:
            return 'dialog'

    if platform.system() == 'Windows':
        modifiers = mod_windows
    elif platform.system() == 'Darwin':
        modifiers = mod_macos
    else:
        modifiers = mod_linux

    def keypress(self, event):
        """Handle key presses."""
        # Non-modified keys trigger on-click response.
        mod_category = self.modifiers(event.state)
        if (mod_category == 'block'
            or event.keysym in ('Return', 'Escape', 'BackSpace', 'Insert',
                                'Delete', 'Prior', 'Next', 'Home', 'End',
                                'Left', 'Right', 'Up', 'Down', 'KP_Enter',
                                'KP_Prior', 'KP_Next', 'KP_Home', 'KP_End',
                                'KP_Insert', 'KP_Delete')):
            return 'break'
        elif mod_category == 'pass' or event.keysym[-3:] == 'Tab':
            return
        else:
            # mod_category == 'dialog'
            if len(event.char) >= 1:
                self._onclick(event)
            return 'break'


class _PositiveField:
    """Single-line text field with positive number in GUI.

    Static methods:
        validate -- determine whether value is valid

    Methods:
        __init__ -- initializer
        invalid -- reset invalid value
        get -- return value of text field
        set -- set value of text field
        enable -- enable or disable field based on associated checkbox (if any)
        disable -- disable field
        focus -- select text and move focus to widget

    Attribute:
        _default -- default value (used to reset field when invalid value is
            entered)
        _variable -- variable tied to text field
        _field - actual field
        _label - field label
        _switch -- checkbox that turns field on or off
    """

    def __init__(self, root, initial, width, text, switch=None, underline=-1):
        """Initialize text field.

        Widget is added to the last empty row of root.

        Arguments:
            root -- parent widget
            initial -- initial value (and default value when invalid value
                is entered)
            width -- field width
            text -- field label
            switch -- checkbox that turns field on or off
            underline -- index of character to underline
        """
        self._default = initial
        self._variable = tk.DoubleVar()
        self._variable.set(initial)
        self._switch = switch
        frame = ttk.Frame(root)
        self._field = ttk.Entry(
                frame, textvariable=self._variable, width=width,
                justify=tk.CENTER, validate='all',
                validatecommand=(root.register(self.validate), '%d', '%P'),
                invalidcommand=(root.register(self.invalid), '%d', '%P', '%s'))
        # Generate focus-out event when return key is pressed. Otherwise, field
        # may be left with invalid value.
        self._field.bind('<Return>',
                         lambda event: event.widget.tk_focusNext().focus())
        self._label = ttk.Label(frame, text=text, underline=underline)
        row = root.grid_size()[1]
        frame.grid(row=row, column=0, columnspan=2, padx=5, sticky='we')
        self._field.grid(row=0, column=0)
        self._label.grid(row=0, column=1, padx=5, sticky='w')
        if switch is not None:
            switch._widget.configure(command=self.enable)
            self.enable()

    @staticmethod
    def validate(action, new_value):
        """Validate proposed field value.

        Arguments:
            action -- 0: deletion; 1: insertion; -1: focus in/out or change in
                value of variable
            new_value -- value entered by user

        Returns:
            whether the value is valid
        """
        try:
            if action == '-1':
                # Strict compliance on focus in/out
                return float(new_value) > 0
            # Allow zero while typing
            return float(new_value) >= 0
        except ValueError:
            return False

    def invalid(self, action, new_value, old_value):
        """Reset invalid value to default.

        Arguments:
            action -- 0: deletion; 1: insertion; -1: focus in/out or change in
                value of variable
            new_value -- value entered by user
            old_value -- previous value
        """
        reaction = {'0': new_value,      # Deletion: allow
                    '1': old_value,      # Insertion: forbid
                    '-1': self._default  # Entry/exit: revert to default
                    }
        self._variable.set(reaction[action])

    def get(self):
        """Return value of text field."""
        return self._variable.get()

    def set(self, value):
        """Set value of text field."""
        return self._variable.set(value)

    def enable(self):
        """Enable field."""
        if self._switch.get():
            self._field.configure(state='disable')
            self._label.configure(state='disable')
        else:
            self._field.configure(state='normal')
            self._label.configure(state='normal')

    def disable(self):
        """Disable field."""
        self._field.configure(state='disable')
        self._label.configure(state='disable')

    def focus(self):
        """Set focus to this field."""
        self._field.select_range(0, 1000)
        self._field.focus_set()


class _Description:
    """Multi-line label.

    Methods:
        __init__ -- initializer
    """

    def __init__(self, root, span, width, text, pady=(0, 5)):
        """Initialize description box.

        Arguments:
            root -- parent widget
            span -- number of columns spanned by widget
            width -- width to which text must be wrapped
            text -- description text
        """
        label = ttk.Label(root, text=textwrap.fill(text, width=width))
        row = root.grid_size()[1]
        label.grid(row=row, column=0, columnspan=span, padx=5, pady=pady,
                   sticky='news')


class _Hyperlink:
    """Centred hyperlink.

    Methods:
        __init__ -- initializer

    Attributes:
        _url -- URL for hyperlink
        _label -- GUI element containing hyperlink

    Methods (internal):
        _on_press -- event handler when mouse button pressed
        _on_release_left -- event handler when left mouse button released
        _on_release_right -- event handler when right mouse button released
        _activate -- event handler when cursor enters hyperlink area
        _deactivate -- event handler when cursor leaves hyperlink area
    """

    def __init__(self, root, url, text=None):
        """Initialize hyperlink.

        Arguments:
            root -- parent widget
            url -- URL for hyperlink
            text -- text of hyperlink (URL is displayed if text is None)
        """
        self._root = root
        self._url = url
        self._label = ttk.Label(root, text=url if text is None else text,
                                foreground='blue', cursor='hand2')
        self._active = True
        row = root.grid_size()[1]
        self._label.grid(row=row, column=0, columnspan=2, padx=5, pady=(0, 5))
        self._label.bind('<ButtonPress>', self._on_press)
        self._label.bind('<ButtonRelease-1>', self._on_release_left)
        if platform.system() == 'Darwin':
            right_click = '<ButtonRelease-2>'
            # Control + left-click = right-click on macOS
            self._label.bind('<Control-ButtonRelease-1>',
                             self._on_release_right)
        else:
            right_click = '<ButtonRelease-3>'
        self._label.bind(right_click, self._on_release_right)
        self._label.bind('<Enter>', self._activate)
        self._label.bind('<Leave>', self._deactivate)

    def _on_press(self, _):
        """Event handler for when user presses any mouse button.

        Arguments:
            event -- event details (ignored)
        """
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            self._label.configure(relief=tk.SUNKEN)
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def _on_release_left(self, _):
        """Event handler for when user releases left mouse button.

        Arguments:
            event -- event details (ignored)
        """
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            self._label.configure(relief=tk.FLAT)
            if self._active:
                _BackgroundTask(self._root, 'open_browser',
                                task=webbrowser.open,
                                args=(self._url,),
                                widgets=[self._label])
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def _on_release_right(self, _):
        """Event handler for when user releases right mouse button.

        Arguments:
            event -- event details (ignored)
        """
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            self._label.configure(relief=tk.FLAT)
            if self._active:
                self._root.clipboard_clear()
                self._root.clipboard_append(self._label.cget('text'))
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def _activate(self, _):
        """Event handler for when cursor enters hyperlink area.

        Arguments:
            event -- event details (ignored)
        """
        self._active = True

    def _deactivate(self, _):
        """Event handler for when cursor leaves hyperlink area.

        Arguments:
            event -- event details (ignored)
        """
        self._active = False


class _LogBox:
    """Multi-line text box in GUI for logging purposes.

    Textbox can be used as replacement for sys.stdout or sys.stderr. (Ref:
    www.blog.pythonlibrary.org/2014/07/14/tkinter-redirecting-stdout-stderr/)

    Methods:
        __init__ -- initializer
        write -- queue string for addition to text box
        _monitor_queue -- periodically check queue and write text to text box
        flush -- do nothing, as flushing is done automatically after writing
        get -- return value of text box
        reset -- delete text box content
        row -- return row index of location in grid

    Attribute:
        _root -- parent widget
        _text -- Tk Text object
        _queue -- thread-safe queue object for text to be written to text box
    """

    def __init__(self, root, width, height):
        """Initialize text box.

        Widget is added to the last empty row of root.

        Arguments:
            root -- parent widget
            width -- initial width of text field
            height -- initial height of text field
        """
        self._root = root
        # Create text box and scroll bar
        self._text = tk.Text(root, width=width, height=height,
                             state='disabled', cursor='', wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(root, command=self._text.yview)
        self._text['yscrollcommand'] = scrollbar.set
        row = root.grid_size()[1]
        self._text.grid(row=row, column=0, sticky='news')
        scrollbar.grid(row=row, column=1, sticky='news')
        # Create tags for line formatting
        font = tk.font.nametofont(name=self._text.cget('font'))
        indent = font.measure('CRITICAL - ')
        self._text.tag_configure('first', lmargin2=indent)
        self._text.tag_configure('other', lmargin1=indent, lmargin2=indent)
        # Create queue for inter-thread communication and schedule monitoring
        # task
        self._queue = queue.SimpleQueue()
        root.after(0, self._monitor_queue)

    def write(self, string):
        """Append string to queue, for addition to text box.

        Argument:
            string -- string to be appended
        """
        self._queue.put(string)

    def _monitor_queue(self):
        """Append strings from queue to text box.

        Called periodically.
        """
        try:
            while True:
                string = self._queue.get(block=False)
                lines = string.splitlines(keepends=True)
                self._text.config(state='normal')
                self._text.insert('end', lines[0], 'first')
                for line in lines[1:]:
                    self._text.insert('end', line, 'other')
                self._text.config(state='disabled')
                self._text.see('end')
        except queue.Empty:
            self._text.update_idletasks()
            self._root.after(100, self._monitor_queue)

    def flush(self):
        """Do nothing, as flushing is done automatically after writing.

        Required for stdout/stderr interface.
        """

    def get(self):
        """Return value of text box."""
        return self._text.get('1.0', 'end-1c')

    def reset(self):
        """Delete text box content."""
        self._text.config(state='normal')
        self._text.delete('1.0', 'end')
        self._text.config(state='disabled')

    def row(self):
        """Return row index of location in grid."""
        return self._text.grid_info()['row']


class _CheckBox:
    """Check box in GUI.

    Note: assumes a 4-column grid.

    Methods:
        __init__ -- initializer
        get -- return value of checkbox
        set -- set value of checkbox
        toggle -- toggle checkbox
        enable -- enable checkbox if not permanently disabled
        disable -- disable checkbox

    Attributes:
        _variable -- variable tied to checkbox
        _widget -- checkbox widget
        _state -- initial state (if 'disabled', always remains disabled)
    """

    def __init__(self, root, initial, text, state='normal', underline=-1):
        """Initialize checkbox.

        Widget is added to the last empty row of root.

        Arguments:
            root -- parent window
            initial -- initial value of checkbox (zero: not checked; non-zero:
                checked)
            text -- checkbox label
            state -- checkbox state (normal or disabled)
        """
        self._variable = tk.IntVar()
        self._variable.set(initial)
        self._widget = ttk.Checkbutton(root, text=text,
                                       variable=self._variable, state=state,
                                       underline=underline)
        self._widget.grid(row=root.grid_size()[1], column=0, columnspan=2,
                          padx=5, sticky='w')
        self._state = state

    def get(self):
        """Return value of checkbox (zero: not checked; non-zero: checked)."""
        return self._variable.get()

    def set(self, value):
        """Set value of checkbox (zero: not checked; non-zero: checked).

        Argument:
            value -- checkbox value
        """
        return self._variable.set(value)

    def toggle(self):
        """Toggle checkbox."""
        self._widget.invoke()

    def enable(self):
        """Enable checkbox if not permanently disabled."""
        if self._state != 'disabled':
            self._widget.configure(state='normal')

    def disable(self):
        """Disable checkbox if enabled."""
        self._widget.configure(state='disabled')


class _OptionList:
    """Option menu in GUI.

    Note: assumes a 2-column grid.

    Methods:
        __init__ -- initializer
        get -- return value of option list

    Attributes:
        _variable -- variable tied to option list
        _widget -- option list widget
    """

    def __init__(self, root, label, values, initial, separators):
        """Initialize option list.

        Arguments:
            root -- parent widget
            label -- label of option list
            values -- values in list
            initial -- value selected initially
            separators -- indices of separator positions in list
        """
        self._variable = tk.StringVar()
        self._variable.set(initial)
        label = ttk.Label(root, text=label)
        self._widget = ttk.OptionMenu(root, self._variable, initial, *values)
        for sep in separators:
            self._widget['menu'].insert_separator(sep)
        row = root.grid_size()[1]
        label.grid(row=row, column=0, padx=5, sticky='w')
        self._widget.grid(row=row, column=1, padx=5, sticky='w')
        if len(values) == 1:
            self._widget.configure(state='disabled')

    def get(self):
        """Return selected value."""
        return self._variable.get()


class _Spacer:
    """Spacer widget in GUI.

    Method:
        __init__ -- spacer initializer
    """

    def __init__(self, root, fill=False):
        """Initialize spacer.

        Widget is added to the last empty row of root.

        Arguments:
            root -- parent widget
        """
        row = root.grid_size()[1]
        frame = ttk.Frame(root, height=10)
        frame.grid(row=row)
        if fill:
            root.grid_rowconfigure(row, weight=1)


class _ButtonRow:
    """Row of buttons in GUI.

    Attributes:
        _buttons -- dictionary of Tk button widgets

    Methods:
        __init__ -- button initializer
        __getitem__ -- return specified Tk button widget
    """

    def __init__(self, root, buttons):
        """Initialize button.

        Buttons are added to the last empty row of root.

        Arguments:
            root -- parent widget
            buttons -- sequence of [name, text, command, state] sequences,
                where:
                    name -- internal name for use with __dict__
                    text -- initial button label
                    char -- index of character to underline (omit if None)
                    command -- function executed when button clicked
                    state -- initial button state
        """
        self._buttons = {}
        frame = ttk.Frame(root)
        frame.grid(row=root.grid_size()[1], column=0, columnspan=2)
        for (column, (name, text, char, command, state)) in enumerate(buttons):
            self._buttons[name] = ttk.Button(frame, text=text, command=command,
                                             state=state, underline=char)
            self._buttons[name].grid(row=0, column=column,
                                     sticky='w', padx=5, pady=5)

    def __getitem__(self, name):
        """Return button with given name."""
        return self._buttons[name]


class _Status:
    """Status bar.

    Methods:
        __init__ -- initializer
        get -- get value of text field in status bar
        set -- set value of text field in status bar

    Attribute:
        _variable -- variable tied to text field
    """

    def __init__(self, root, initial):
        """Initialize status bar.

        Widget is added to the last empty row of root and is aligned to the
        bottom.

        Arguments:
            root -- parent widget
            initial -- initial value
        """
        self._variable = tk.StringVar()
        self._variable.set(initial)
        self._label = ttk.Label(root, textvariable=self._variable,
                                relief=tk.SUNKEN)
        row = root.grid_size()[1]
        self._label.grid(row=row, column=0, padx=5, sticky='news')

    def get(self):
        """Get value of text field."""
        return self._variable.get()

    def set(self, value):
        """Set value of text field."""
        return self._variable.set(value)

    def height(self):
        """Return height of text field."""
        return self._label.winfo_height()


class _Busy:
    """Context manager displaying a busy cursor in GUI.

    Methods:
        __init__ -- initializer
        __enter__ -- enter busy context: display busy cursor
        __exit__ -- exit busy context: hide busy cursor

    Attribute:
        _root -- root widget of window
        _widgets -- sequence of widgets for which to show busy cursor
        _default -- sequence of original cursors
    """

    def __init__(self, root, widgets=None):
        """Initialize busy cursor.

        Arguments:
            root -- root widget of window
            widgets -- list of widgets for which to show busy cursor (apply to
                root if None)
        """
        self._root = root
        if widgets is None:
            self._widgets = [root]
        else:
            self._widgets = widgets
        if widgets is not None:
            self._widgets += list(widgets)
        self._default = [widget.cget('cursor') for widget in self._widgets]

    def __enter__(self):
        """Start busy cursor."""
        for widget in self._widgets:
            widget.config(cursor='watch')
        self._root.update()

    def __exit__(self, exception_type, exception_value, traceback):
        """Stop busy cursor."""
        for (widget, default) in zip(self._widgets, self._default):
            widget.configure(cursor=default)
        self._root.update()


class _BackgroundTask:
    """Background task running in another thread.

    The busy cursor is displayed while the task is run.

    Attributes:
        _root -- parent widget
        _busy -- context manager displaying busy cursor
        _executor -- task executor managing separate thread
        _future -- object representing asynchronous execution of task
        _callback -- callable to be executed on normal task completion

    Methods:
        _monitor -- monitor task progress and cleanup on completion
    """

    def __init__(self, root, thread_name, *, task, args=(), kwargs={},
                 callback=None, widgets=None):
        """Initialize background task.

        Arguments:
            root -- parent widget
            thread_name -- thread name (for debugging)
            task -- callable to be run in other thread
            args -- positional arguments of task
            kwargs -- keyword arguments of task
            callback -- callable to be called on completion of task, with
                Future object (from concurrent.futures) as single argument;
                must call future.result to trigger exception handling;
                Future.result is called directly if callback is None
            widgets -- list of widgets for which to show busy cursor (root if
                None)
        """
        self._root = root
        self._busy = _Busy(root, widgets)
        self._busy.__enter__()
        # Manually trigger garbage collection to avoid Tkinter objects being
        # garbage collected in another thread.
        gc.collect()
        self._executor = futures.ThreadPoolExecutor(1, thread_name)
        self._future = self._executor.submit(task, *args, **kwargs)
        self._callback = callback
        root.after(100, self._monitor)

    def _monitor(self):
        """Monitor task completion.

        On completion, call callback function and restore regular cursor.
        """
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            try:
                self._future.exception(timeout=0)
            except futures.TimeoutError:
                self._root.after(100, self._monitor)
                return
            try:
                if self._callback is None:
                    self._future.result()
                else:
                    self._callback(self._future)
            finally:
                self._executor.shutdown()
                self._busy.__exit__(*sys.exc_info())
        except Exception:
            _misc_logger.exception(_UNEXPECTED)


class _InterProcessError(Exception):
    """Exception raised on inter-process communication error

    Methods:
        __init__ -- initializer
    """

    def __init__(self):
        """Initialize exception."""
        super().__init__(_CORRUPT_GEN_PY)


class _WordNotFoundError(Exception):
    """Exception raised when MS Word not found

    Methods:
        __init__ -- initializer
    """

    def __init__(self):
        """Initialize exception."""
        super().__init__(_WORD_NOT_FOUND)


class _ModalDialogError(Exception):
    """Exceptions raised when Word is unresponsive due to an open dialog box.

    Methods:
        __init__ -- initializer
    """

    def __init__(self):
        super().__init__(_MODAL_DIALOG)


class _Language:
    """Interface to language name from MS Word

    Attributes:
        full -- full name (base + variant)
        base -- base name (e.g., French or English)
        variant -- language variant (e.g., Canada)

    Methods:
        __init__ -- initializer
    """

    def __init__(self, local_name):
        """Initialize language

        Arguments:
            local_name -- local name provided by MS Word
        """
        try:
            self.full = local_name
            base, variant = self.full.split('(', maxsplit=1)
            self.base = base[:-1]
            self.variant = variant[0:-1]
        except ValueError:
            self.base = self.full
            self.variant = None


def run(init_inpath=None, *, init_outpattern=_app.OUTPATTERN,
        init_patterns=False, init_steps=False, init_times=False,
        init_trace=False, init_verbose=False,
        init_auto=True, init_default=True, init_local=True,
        init_re=False, init_timeout=_engine.extractor.TIMEOUT,
        init_log=None):
    """Start Graphical User Interface (GUI).

    Arguments:
        init_inpath -- initial value of input file path field
        init_outpattern -- initial value of output file name field
        init_steps -- initial state of steps checkbox
        init_times -- initial state of times checkbox
        init_trace -- initial state of trace checkbox
        init_verbose -- initial state of verbose checkbox
        init_auto -- initial value of noauto checkbox (reversed)
        init_default -- initial state of nodefault checkbox (reversed)
        init_local -- initial value of nolocal checkbox (reversed)
        init_re -- initial state of re checkbox
        init_timeout -- initial value of timeout field
        init_log -- initial value of extraction log
    """
    # pylint: disable=broad-except
    # Reason: exception logged
    _app.set_log_stream(sys.stderr)
    if platform.system() == 'Windows':
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    try:
        root = tk.Tk()
        root.withdraw()
        _set_icon(root)
        if platform.system() == 'Darwin':
            # Set font color of disabled buttons manually to ensure they are
            # greyed on macOS too.
            style = ttk.Style()
            style.map('TButton', foreground=[('disabled', 'gray70')])
        main_window = _MainWindow(root=root,
                                  init_inpath=init_inpath,
                                  init_outpattern=init_outpattern,
                                  init_patterns=init_patterns,
                                  init_steps=init_steps,
                                  init_times=init_times,
                                  init_trace=init_trace,
                                  init_verbose=init_verbose,
                                  init_auto=init_auto,
                                  init_default=init_default,
                                  init_local=init_local,
                                  init_re=init_re,
                                  init_timeout=init_timeout)
        # Display messages temporarily saved to string, if any.
        if init_log is not None:
            main_window.log.write(init_log)
        _app.set_log_stream(main_window.log)
        # Warn of tkinter bug for macOS >= 14. Rely on Darwin version, because
        # platform.mac_ver() does not return more than 10.16 on python < 3.8.
        if (platform.system() == 'Darwin'
                and int(platform.release().split('.')[0]) >= 23
                and sys.version_info < (3, 11, 7)):
            _misc_logger.warning(_MACOS14)
        root.protocol('WM_DELETE_WINDOW', main_window.on_delete)
        root.deiconify()
        root.mainloop()
    except Exception:
        _misc_logger.exception(_UNEXPECTED)


def update_shortcuts():
    """Start GUI for shortcut creation or deletion."""
    # pylint: disable=broad-except
    # Reason: exception logged
    _app.set_log_stream(sys.stderr)
    if platform.system() == 'Windows':
        sw_init = _ShortcutWindow.for_windows
    elif platform.system() == 'Darwin':
        sw_init = _ShortcutWindow.for_macos
    else:
        # Attempt same method as Linux for all other platforms.
        sw_init = _ShortcutWindow.for_linux
    try:
        root = tk.Tk()
        root.withdraw()
        _set_icon(root)
        sw_init(root)
        root.deiconify()
        root.mainloop()
    except Exception:
        _misc_logger.exception(_UNEXPECTED)


def _set_icon(root):
    """Set window icon.

    Argument:
        root -- root widget of window
    """
    if platform.system() == 'Windows':
        # The 32x32 icon looks better on Windows.
        icon_name = 'errers32.png'
    else:
        # The 256x256 icon looks better on macOS when using Command-Tab. It
        # doesn't seem to matter on Linux.
        icon_name = 'errers.png'
    icon_path = Path(__file__).parent.joinpath('icon', icon_name)
    photo = tk.PhotoImage(file=icon_path)
    root.iconphoto(False, photo)


def _dispatch(prog_id):
    """Return COM object with early-binding, clearing cache if needed.

    Argument:
        prog_id -- programmatic identifier of object

    Returns:
        COM object
    """
    gencache = win32com.client.gencache
    try:
        com_object = gencache.EnsureDispatch(prog_id)
    except AttributeError:
        # Delete gen_py cache generated by makepy, and reraise exception.
        shutil.rmtree(gencache.GetGeneratePath(), ignore_errors=True)
        raise
    return com_object


def _centre_window(parent, child):
    """Centre one window over another.

    Arguments:
        parent -- window over which to centre
        child -- window to be centred
    """
    # Assume child windows are already centred on Linux.
    if platform.system() in ('Darwin', 'Windows'):
        x_shift = (parent.winfo_width() - child.winfo_reqwidth()) // 2
        y_shift = (parent.winfo_height() - child.winfo_reqheight()) // 2
        child.geometry('+%d+%d' % (parent.winfo_x() + x_shift,
                                   parent.winfo_y() + y_shift))


def _show_error(root, parent, message):
    """Custom error dialog box.

    Arguments:
        root -- root widget
        parent -- parent window
        message -- message to display
    """
    # Build dialog box
    dialog = tk.Toplevel(parent)
    dialog.withdraw()
    dialog.resizable(False, False)
    dialog.title('ERRERS')
    frame = ttk.Frame(dialog)
    frame.grid(row=0, column=0)
    icon = ttk.Label(frame, image='::tk::icons::error')
    text = ttk.Label(frame, text=textwrap.fill(message, width=60))
    ok = ttk.Button(frame, text='Ok', underline=0,
                    command=dialog.destroy)
    icon.grid(row=0, column=0, padx=(20, 5), pady=10, sticky='n')
    text.grid(row=0, column=1, padx=(0, 30), pady=10)
    ok.grid(row=1, column=0, columnspan=2, pady=(0, 10))
    _set_icon(dialog)
    # Keyboard shortcuts
    dialog.bind(f'<{MOD_KEY}-o>', lambda e: dialog.destroy())
    dialog.bind(f'<{MOD_KEY}-O>', lambda e: dialog.destroy())
    dialog.bind('<Return>', lambda e: dialog.destroy())
    dialog.bind('<Escape>', lambda e: dialog.destroy())
    # Show window and wait for acknowledgement
    dialog.withdraw()
    dialog.update_idletasks()
    if parent is None:
        root.eval('tk::PlaceWindow %s center' % dialog.winfo_toplevel())
    else:
        dialog.transient(parent)
        _centre_window(parent, dialog)
    dialog.deiconify()
    dialog.focus_set()
    dialog.grab_set()
    dialog.wait_window(dialog)


def _ask_yes_no(root, parent, question):
    """Custom yes-no dialog box.

    Arguments:
        root -- root widget
        parent -- parent window
        question -- yes-no question
    """
    # Function to save answer
    answer = None

    def set_answer(value):
        nonlocal answer
        answer = value
        dialog.destroy()

    # Build dialog box
    dialog = tk.Toplevel(parent)
    dialog.withdraw()
    dialog.resizable(False, False)
    dialog.title('ERRERS')
    dialog.protocol('WM_DELETE_WINDOW', lambda: set_answer(False))
    frame = ttk.Frame(dialog)
    frame.grid(row=0, column=0)
    icon = ttk.Label(frame, image='::tk::icons::question')
    text = ttk.Label(frame, text=textwrap.fill(question, width=60))
    buttons = ttk.Frame(frame)
    icon.grid(row=0, column=0, padx=(20, 5), pady=10, sticky='n')
    text.grid(row=0, column=1, padx=(0, 30), pady=10)
    buttons.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10))
    yes = ttk.Button(buttons, text='Yes', underline=0,
                     command=lambda: set_answer(True))
    no = ttk.Button(buttons, text='No', underline=0,
                    command=lambda: set_answer(False))
    yes.grid(row=0, column=0, padx=5)
    no.grid(row=0, column=1, padx=5)
    _set_icon(dialog)
    # Keyboard shortcuts
    dialog.bind(f'<{MOD_KEY}-y>', lambda e: set_answer(True))
    dialog.bind(f'<{MOD_KEY}-Y>', lambda e: set_answer(True))
    dialog.bind(f'<{MOD_KEY}-n>', lambda e: set_answer(False))
    dialog.bind(f'<{MOD_KEY}-N>', lambda e: set_answer(False))
    dialog.bind('<Return>', lambda e: set_answer(True))
    dialog.bind('<Escape>', lambda e: set_answer(False))
    # Show window and wait for answer
    dialog.withdraw()
    dialog.update_idletasks()
    if parent is None:
        root.eval('tk::PlaceWindow %s center' % dialog.winfo_toplevel())
    else:
        dialog.transient(parent)
        _centre_window(parent, dialog)
    dialog.deiconify()
    dialog.focus_set()
    dialog.grab_set()
    parent.wait_window(dialog)
    return answer
