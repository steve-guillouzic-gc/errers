# coding=utf-8
#
# SPDX-FileCopyrightText: 2023 His Majesty the King in Right of Canada, as represented by the Minister of National Defence
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
    _CORRUPT_GEN_PY, _INVALID_INPUT_FILE, _FILENAME_REQUIRED, _DESCRIPTION,
    _MANUAL, _FEEDBACK, _CONTACT, _CONTACT_URL, _NOTE_URL, _NOTE_COPY,
    _CLICK_INPUT_FILE, _DEBUGGING

Constants: logging
    _main_logger -- parent logger to all ERRERS loggers
    _misc_logger -- miscellaneous log messages

Classes (internal):
    _MainWindow -- main GUI window
    _HelpWindow -- window for help text
    _OptionsWindow -- window for specifying options
    _ShortcutWindow -- window for shortcut creation
    _SectionLabel -- section label in GUI
    _SubSectionLabel -- sub-section label in GUI
    _TextField -- single-line text field in GUI
    _PositiveField -- single-line text field with positive number in GUI
    _Description -- multi-line label
    _Hyperlink -- centred hyperlink
    _LogBox -- multi-line text box in GUI for logging purposes
    _CheckBox -- checkbox in GUI
    _Spacer -- spacer widget in GUI
    _ButtonRow -- row of buttons in GUI
    _Status -- status bar
    _Busy -- context manager displaying a busy cursor in GUI

Functions (internal):
    _dispatch -- return COM object with early-binding, clearing cache if needed
"""

__all__ = ['run']

import functools as ft
import logging
import os
from pathlib import Path
import platform
import plistlib
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
    import pythoncom
    import win32com.client
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
_UNEXPECTED_MESSAGE = 'Unexpected error'
_UNEXPECTED_DETAIL = ('Details written to console window. '
                      'Please report to developer.')
_WORD_NOT_FOUND = 'Microsoft Word not found'
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
        fields. For most widgets, the shortcut is the {MOD_KEY} key combined
        with the underlined letter in the widget label. The only exception is
        the Times option, for which the shortcut is {MOD_KEY}+X. In dialog
        boxes, the enter and return keys can also be used for "Yes" and "Ok",
        while the escape key can be used for "No" and "Cancel"."""),
    "More information in user manual:"
]
_MANUAL = 'https://cradpdf.drdc-rddc.gc.ca/PDFS/unc372/p813656_A1b.pdf'
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
        ask_input_file -- prompt user for input file
        start_extraction -- start thread for LaTeX to text extraction
        run_extraction -- extract text from LaTeX file
        copy_text -- copy text to clipboard
        copy_log -- copy log to clipboard
        start_check -- start thread for grammar check
        run_check -- launch Microsoft Word and start grammar check
        on_delete -- clean up when window is closed
        close -- close GUI, waiting for extraction interruption if needed
        update_time -- update elapsed time in the status bar

    Attributes:
        root -- root widget of window
        log -- text box for standard error log
        _extractor -- extraction thread
        _interruption -- event to interrupt extraction thread
        _inpath -- path of input file
        _outpattern -- pattern for output file name
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
                                       self.root.focus_set)
        self._options.withdraw()
        # Configure main window
        root.title('%s %s' % (errers.SHORTNAME, errers.__version__))
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
        _Description(controls, 100, _NOTE_COPY)
        _Spacer(controls, fill=True)
        controls.grid_columnconfigure(1, weight=1)
        # Extraction log
        _SectionLabel(log, 'Extraction log')
        _Description(log, 100, _FILTERED)
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
        self._inpath.set_wraplength()
        if init_inpath is None:
            self._inpath.set(_CLICK_INPUT_FILE)
            self._status.set(_FILENAME_REQUIRED)
        elif not _app.valid_input_file(init_inpath):
            tk.messagebox.showerror(title=errers.SHORTNAME + ' Error',
                                    message=_INVALID_INPUT_FILE,
                                    parent=self.root)
            self._inpath.set(_CLICK_INPUT_FILE)
            self._status.set(_FILENAME_REQUIRED)
        else:
            self._inpath.set(init_inpath)
        # Set initial value and wrap length of option list
        self._opt_list.set_wraplength()
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
        root.bind(f'<{MOD_KEY}-o>', lambda e: self._outpattern.focus())
        root.bind(f'<{MOD_KEY}-n>', self.ask_options)
        root.bind(f'<{MOD_KEY}-e>', lambda e: self.press('extract'))
        root.bind(f'<{MOD_KEY}-c>', lambda e: self.press('copy text'))
        root.bind(f'<{MOD_KEY}-y>', lambda e: self.press('copy log'))
        root.bind(f'<{MOD_KEY}-r>', lambda e: self.press('reset'))
        root.bind(f'<{MOD_KEY}-h>', lambda e: self.press('help'))
        root.bind(f'<{MOD_KEY}-q>', lambda e: self.press('quit'))
        if 'win32com.client' in sys.modules:
            root.bind(f'<{MOD_KEY}-k>', lambda e: self.press('check'))

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

    def help(self):
        """Show help window."""
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            help_window = _HelpWindow()
            help_window.transient(self.root)
            help_window.update_idletasks()
            help_window.focus_set()
            help_window.grab_set()
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def ask_input_file(self, event):
        """Prompt user for input file."""
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
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
                # Path.resolve is needed because tk_askpenfilename always uses
                # a forward slash as directory separator.
                self._inpath.set(Path(filename).resolve())
                self.reset()
                self.root.update()
                self.set_minsize()
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
            self._options.transient(self.root)
            self._options.deiconify()
            self._options.update_idletasks()
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
        self.root.focus_set()

    def start_extraction(self):
        """Start LaTeX to text extraction in separate thread."""
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            if not Path(self._inpath.get()).is_file():
                tk.messagebox.showerror(title=errers.SHORTNAME + ' Error',
                                        message=_INVALID_INPUT_FILE,
                                        parent=self.root)
                self._inpath.set(_CLICK_INPUT_FILE)
                self._status.set(_FILENAME_REQUIRED)
            elif not self._outpattern.get():
                tk.messagebox.showerror(title=errers.SHORTNAME + ' Error',
                                        message=_INVALID_OUTPUT_FILE,
                                        parent=self.root)
                self._status.set(_INVALID_OUTPUT_FILE)
            else:
                self._interruption = threading.Event()
                self._extractor = threading.Thread(target=self.run_extraction)
                self._extractor.start()
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def run_extraction(self):
        """Perform text extraction."""
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            outroot = _app.output_file_root(Path(self._inpath.get()),
                                            self._outpattern.get())
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
                extract = tk.messagebox.askyesno(title=errers.LONGNAME,
                                                 message=message,
                                                 default='yes')
                self.root.focus_set()
            else:
                extract = True
            if extract:
                self._update = self.root.after(0, self.update_time)
                with _Busy(self.root):
                    try:
                        try:
                            self._btn_main['extract'].config(
                                    text='Extracting', state='disabled',
                                    underline=-1)
                            options = self._options
                            self._outname = _app.extract_and_save(
                                    inpath=Path(self._inpath.get()),
                                    outpattern=self._outpattern.get(),
                                    patterns=options.patterns.get(),
                                    steps=options.steps.get(),
                                    times=options.times.get(),
                                    trace=options.trace.get(),
                                    verbose=options.verbose.get(),
                                    local=not options.nolocal.get(),
                                    auto=not options.noauto.get(),
                                    default=not options.nodefault.get(),
                                    std_re=options.re.get(),
                                    timeout=options.timeout.get(),
                                    interruption=self._interruption)
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
                    except _engine.base.CatastrophicBacktracking as err:
                        _misc_logger.error(err)
                    except _engine.base.RegularExpressionError:
                        _misc_logger.error('Extraction interrupted by '
                                           'regular expression error.')
                    except PermissionError as err:
                        _misc_logger.error('Cannot write to %s. It may be '
                                           'open in another application. '
                                           'If so, please close it and '
                                           'try again.',
                                           Path(err.filename).name)
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
                        _app.set_log_stream(self.log)
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

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
            self._checker = threading.Thread(target=self.run_check)
            self._checker.start()
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def run_check(self):
        """Launch Microsoft Word and start grammar check."""
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            constants = win32com.client.constants
            pywintypes = win32com.client.pywintypes
            # Initialize COM libraries for this thread.
            pythoncom.CoInitialize()
            with _Busy(self.root):
                try:
                    shell = _dispatch('Wscript.Shell')
                except AttributeError:
                    tk.messagebox.showerror(
                            title=errers.SHORTNAME + ' Error',
                            message=_CORRUPT_GEN_PY, parent=self.root)
                    return
                try:
                    word = _dispatch('Word.Application')
                except AttributeError:
                    tk.messagebox.showerror(
                            title=errers.SHORTNAME + ' Error',
                            message=_CORRUPT_GEN_PY, parent=self.root)
                    return
                except pywintypes.com_error:
                    tk.messagebox.showerror(
                            title=errers.SHORTNAME + ' Error',
                            message=_WORD_NOT_FOUND, parent=self.root)
                    return
                doc = word.Documents.Open(str(self._outname))
                word.Visible = True
                shell.AppActivate(doc)
                if word.WindowState == constants.wdWindowStateMinimize:
                    word.WindowState = constants.wdWindowStateNormal
                doc.DetectLanguage()
                doc.CheckGrammar()
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

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
            if hasattr(self, '_extractor') and self._extractor.is_alive():
                self.root.after(100, self.close)
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
            _Description(description, width, desc)
        _Hyperlink(description, _MANUAL)
        _Description(description, width, _FEEDBACK)
        _Hyperlink(description, _ISSUES_URL, _ISSUES)
        _Description(description, width, _ALTERNATE)
        _Hyperlink(description, _CONTACT_URL, _CONTACT)
        _Description(description, width, _NOTE_URL)
        buttons = [('ok', 'Ok', 0, self.destroy, 'normal')]
        _ButtonRow(description, buttons)
        # Keyboard shortcuts
        self.bind(f'<{MOD_KEY}-o>', lambda e: self.destroy())
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
        _Description(controls, 100, _DEBUGGING)
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
        _Description(controls, 100, 'Note: %o = name of output file',
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
        self.bind(f'<{MOD_KEY}-s>', lambda e: self.steps.toggle())
        self.bind(f'<{MOD_KEY}-x>', lambda e: self.times.toggle())
        self.bind(f'<{MOD_KEY}-t>', lambda e: self.trace.toggle())
        self.bind(f'<{MOD_KEY}-v>', lambda e: self.verbose.toggle())
        self.bind(f'<{MOD_KEY}-a>', lambda e: self.noauto.toggle())
        self.bind(f'<{MOD_KEY}-d>', lambda e: self.nodefault.toggle())
        self.bind(f'<{MOD_KEY}-l>', lambda e: self.nolocal.toggle())
        self.bind(f'<{MOD_KEY}-m>', lambda e: self.re.toggle())
        self.bind(f'<{MOD_KEY}-u>', lambda e: self.timeout.focus())
        self.bind(f'<{MOD_KEY}-o>', lambda e: self.on_ok())
        self.bind(f'<{MOD_KEY}-c>', lambda e: self.on_cancel())
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
            options.append('max %i seconds per rule' % self.timeout.get())
        return ', '.join(options)


class _ShortcutWindow:
    """Window for shortcut creation.

    Some shortcuts can also be used as drag-and-drop target for input files.

    Widgets are laid out in the same way as the main window.

    Class methods:
        for_windows -- create shortcut creation window for Microsoft Windows
        for_macos -- create shortcut creation window for macOS
        for_linux -- create shortcut creation window for Linux

    Methods:
        __init__ -- window initializer
        start_creation -- start thread for shortcut creation
        create -- create selected shortcuts
        create_windows -- create shortcut on Windows platform
        create_macos -- create shortcut on macOS platform
        create_linux -- create shortcut on Linux platform

    Attributes:
        root -- root widget of window
        _functions -- mapping of folder to shortcut creation function
        _checkboxes -- list of folder checkboxes

    Reference for Linux shortcuts:
        https://specifications.freedesktop.org/
    """

    def __init__(self, root, functions, message):
        """Initialize shortcut window.

        Attribute:
            root -- root widget of window
            functions -- mapping of folder to shortcut creation function
            message -- message insert for shortcut window
        """
        self.root = root
        root.resizable(False, False)
        root.title('%s (Version %s)' % (errers.SHORTNAME,
                                        errers.__version__))
        frame = ttk.Frame(self.root)
        frame.grid(row=0, column=0, ipadx=5, sticky='news')
        _SectionLabel(frame, 'Shortcut creation')
        _Description(frame, 85, textwrap.dedent("""\
            Creating shortcuts is optional, but it streamlines usage by
            providing a simple way to launch the tool and allowing
            drag-and-drop. """))
        _Description(frame, 85, message)
        _Description(frame, 85, textwrap.dedent("""\
            Where would you like to create application shortcuts? (If shortcuts
            already exist in those locations, they will be updated to point to
            this %s installation.)""" % errers.SHORTNAME))
        self._functions = functions
        self._checkboxes = [_CheckBox(frame, 1, folder)
                            for folder in functions]
        _ButtonRow(frame, [('create', 'Create', 0,
                           self.start_creation, 'normal'),
                           ('cancel', 'Cancel', 2,
                           self.root.destroy, 'normal')])
        root.bind(f'<{MOD_KEY}-c>', lambda e: self.start_creation())
        root.bind(f'<{MOD_KEY}-n>', lambda e: root.destroy())
        root.bind('<Return>', lambda e: self.start_creation())
        root.bind('<Escape>', lambda e: root.destroy())

    @classmethod
    def for_windows(cls, root):
        """Create shortcut creation window for Microsoft Windows.

        Attribute:
            root -- root widget of window
        """
        functions = {'Desktop': ft.partial(cls.create_windows,
                                           folder_name='Desktop'),
                     'SendTo menu': ft.partial(cls.create_windows,
                                               folder_name='SendTo'),
                     'Start menu': ft.partial(cls.create_windows,
                                              folder_name='StartMenu')}
        message = textwrap.dedent(f"""\
            For instance, dragging a LaTeX file and dropping it on a desktop
            shortcut launches the application GUI with the input file path
            already filled out. Right-clicking on a LaTeX file and choosing
            {errers.SHORTNAME} under the "Send To" submenu does the same
            thing.""")
        return cls(root, functions, message)

    @classmethod
    def for_macos(cls, root):
        """Create shortcut creation window for macOS.

        Attribute:
            root -- root widget of window
        """
        home = Path.home()
        applications = home.joinpath('Applications')
        functions = {'User applications folder, Launchpad, '
                     'and "Open with" menu':
                     ft.partial(cls.create_macos, folder=applications)}
        message = textwrap.dedent(f"""\
            For instance, dragging a LaTeX file and dropping it on one of the
            shortcuts launches the application GUI with the input file path
            already filled out. Right-clicking on a LaTeX file and choosing
            {errers.SHORTNAME} under the "Open with" menu does the same thing.
            After creation, the shortcut from the Applications folder or the
            Launchpad can be dragged and dropped onto the Dock for easier
            access.""")
        return cls(root, functions, message)

    @classmethod
    def for_linux(cls, root):
        """Create shortcut creation window for Linux.

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
            functions = {'Desktop':
                         ft.partial(cls.create_linux,
                                    file_path=desktop.joinpath(short),
                                    chmod=True)}
        else:
            functions = {'Home':
                         ft.partial(cls.create_linux,
                                    file_path=home.joinpath(short),
                                    chmod=True)}
        if menu.exists():
            functions['Application menu (under Utilities) '
                      'and "Open With" menu'] \
                    = ft.partial(cls.create_linux,
                                 file_path=menu.joinpath(full),
                                 chmod=False)
        message = textwrap.dedent(f"""\
            For instance, dragging a LaTeX file and dropping it on a desktop
            shortcut launches the application GUI with the input file path
            already filled out. Right-clicking on a LaTeX file and choosing
            {errers.SHORTNAME} under the "Open With" menu does the same thing.
            (Note: The application offers to create a shortcut in the home
            folder if the desktop folder is not found.)""")
        cls(root, functions, message)

    def start_creation(self):
        """Start shortcut creation in separate thread."""
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            self._creator = threading.Thread(target=self.create,
                                             daemon=True)
            self._creator.start()
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def create(self):
        """Create selected shortcuts."""
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            with _Busy(self.root):
                for checkbox, function in zip(self._checkboxes,
                                              self._functions.values()):
                    if checkbox.get():
                        if not function(self):
                            break
            self.root.destroy()
        except Exception:
            _misc_logger.exception(_UNEXPECTED)

    def create_windows(self, folder_name):
        """Create shortcut on Windows platform.

        Argument:
            folder_name -- special folder where to create shortcut (should be
                "Desktop", "SendTo" or "StartMenu")

        Returns:
            Boolean indicating if shortcut creation was successful
        """
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            # Initialize COM libraries for this thread.
            pythoncom.CoInitialize()
            try:
                shell = _dispatch('Wscript.Shell')
            except AttributeError:
                tk.messagebox.showerror(title=errers.SHORTNAME + ' Error',
                                        message=_CORRUPT_GEN_PY,
                                        parent=self.root)
                return False
            folder = Path(shell.SpecialFolders(folder_name))
            shortcut = shell.CreateShortcut(
                    folder.joinpath(errers.SHORTNAME + '.lnk'))
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
            return True
        except Exception:
            _misc_logger.exception(_UNEXPECTED)
            tk.messagebox.showerror(title=errers.SHORTNAME + ' Error',
                                    message=_UNEXPECTED_MESSAGE,
                                    detail=_UNEXPECTED_DETAIL,
                                    parent=self.root)
            return False

    def create_macos(self, folder):
        """Create shortcut on macOS platform.

        This is done by creating an application using the osacompile utility
        provided by Apple.

            folder -- folder where to create shortcut
        """
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
            tmp = folder.joinpath(f'{errers.SHORTNAME}_tmp.app')
            final = folder.joinpath(f'{errers.SHORTNAME}.app')
            icon_old = tmp.joinpath('Contents', 'Resources', 'droplet.icns')
            icon_new = Path(__file__).parent.joinpath('icon', 'errers.icns')
            info_plist = tmp.joinpath('Contents', 'Info.plist')
            executable = Path(sys.executable).parent.joinpath('errers')
            script = textwrap.dedent(f"""\
                on run
                    do shell script "{executable}"
                end run

                on open LaTeX_file
                    set LaTeX_path to POSIX path of LaTeX_file
                    do shell script "{executable} --gui " & LaTeX_path
                end open""")
            folder.mkdir(parents=True, exist_ok=True)
            shutil.rmtree(str(tmp), ignore_errors=True)
            shutil.rmtree(str(final), ignore_errors=True)
            sp.run(['osacompile', '-o', str(tmp)], input=script,
                   universal_newlines=True, stderr=sp.PIPE, check=True)
            Path(icon_old).unlink()
            shutil.copy(str(icon_new), str(icon_old.parent))
            with open(info_plist, 'rb') as info_file:
                info = plistlib.load(info_file)
                doc_types = info['CFBundleDocumentTypes']
                doc_extensions = doc_types[0]['CFBundleTypeExtensions']
                doc_extensions[0] = 'tex'
                info['CFBundleIconFile'] = 'errers'
            with open(info_plist, 'wb') as info_file:
                plistlib.dump(info, info_file)
            shutil.copytree(str(tmp), str(final))
            shutil.rmtree(str(tmp))
            return True
        except Exception:
            _misc_logger.exception(_UNEXPECTED)
            tk.messagebox.showerror(title=errers.SHORTNAME + ' Error',
                                    message=_UNEXPECTED_MESSAGE,
                                    detail=_UNEXPECTED_DETAIL,
                                    parent=self.root)
            return False

    def create_linux(self, file_path, chmod):
        """Create shortcut on Linux platform.

        Argument:
            file_path -- path of shortcut file
            chmod -- whether to make the file executable
        """
        # pylint: disable=broad-except
        # Reason: exception logged
        try:
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
                os.chmod(file_path, os.stat(file_path).st_mode | stat.S_IXUSR)
            return True
        except Exception:
            _misc_logger.exception(_UNEXPECTED)
            tk.messagebox.showerror(title=errers.SHORTNAME + ' Error',
                                    message=_UNEXPECTED_MESSAGE,
                                    detail=_UNEXPECTED_DETAIL,
                                    parent=self.root)
            return False


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
        set_wraplength -- set wrap length to current width
        focus -- select text and move focus to widget

    Attribute:
        _variable -- variable tied to text field
        _field -- text field
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
        self._variable = tk.StringVar()
        self._variable.set(initial)
        label = ttk.Label(root, text=text, underline=underline)
        frame = ttk.Frame(root)
        if onclick is None:
            self._field = ttk.Entry(frame, textvariable=self._variable,
                                    state='normal')
        else:
            # Use Label so text can wrap.
            if platform.system() == 'Windows':
                relief = 'solid'
            else:
                relief = 'sunken'
            self._field = ttk.Label(frame, textvariable=self._variable,
                                    state='readonly', background='white',
                                    relief=relief, padding=1,
                                    style='Field.TLabel', width=80)
        if onedit is not None:
            self._variable.trace('w', lambda *args: onedit())
        desc = ttk.Label(frame, text=description)
        row = root.grid_size()[1]
        label.grid(row=row, column=0, padx=5, sticky='nes')
        frame.grid(row=row, column=1, sticky='news')
        self._field.grid(row=0, column=0, sticky='news')
        desc.grid(row=0, column=1, padx=2.5 if description == '' else 5,
                  sticky='nws')
        frame.grid_columnconfigure(0, weight=1)
        if onclick is not None:
            self._field.bind('<Button-1>', onclick)

    def get(self):
        """Return value of text field."""
        return self._variable.get()

    def set(self, value):
        """Set value of text field."""
        return self._variable.set(value)

    def set_wraplength(self):
        """Set wrap length to current width."""
        self._field.config(wraplength=self._field.winfo_width())

    def focus(self):
        self._field.select_range(0, 1000)
        self._field.focus_set()


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
                justify=tk.CENTER, validate='focusout',
                validatecommand=(root.register(self.validate), '%P'),
                invalidcommand=(root.register(self.invalid),))
        self._label = ttk.Label(frame, text=text, underline=underline)
        row = root.grid_size()[1]
        frame.grid(row=row, column=0, columnspan=2, padx=5, sticky='we')
        self._field.grid(row=0, column=0)
        self._label.grid(row=0, column=1, padx=5, sticky='w')
        if switch is not None:
            switch._widget.configure(command=self.enable)
            self.enable()

    @staticmethod
    def validate(value):
        """Validate proposed field value.

        Arguments:
            value -- value entered by user

        Returns:
            whether the value is valid
        """
        try:
            return float(value) > 0
        except ValueError:
            return False

    def invalid(self):
        """Reset invalid value to default."""
        self._variable.set(self._default)

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
        self._field.select_range(0, 1000)
        self._field.focus_set()


class _Description:
    """Multi-line label.

    Methods:
        __init__ -- initializer
    """

    def __init__(self, root, width, text, pady=(0, 5)):
        """Initialize description box.

        Arguments:
            root -- parent widget
            width -- width to which text must be wrapped
            text -- description text
        """
        label = ttk.Label(root, text=textwrap.fill(text, width=width))
        row = root.grid_size()[1]
        label.grid(row=row, column=0, columnspan=2, padx=5, pady=pady,
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
        _open_browser -- open browser and reset cursor once done
        _copy_text -- copy hyperlink text to clipboard
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
        self._label.configure(relief=tk.SUNKEN)

    def _on_release_left(self, _):
        """Event handler for when user releases left mouse button.

        Arguments:
            event -- event details (ignored)
        """
        self._label.configure(relief=tk.FLAT)
        if self._active:
            threading.Thread(target=self._open_browser, daemon=True).start()

    def _on_release_right(self, _):
        """Event handler for when user releases right mouse button.

        Arguments:
            event -- event details (ignored)
        """
        self._label.configure(relief=tk.FLAT)
        if self._active:
            threading.Thread(target=self._copy_text, daemon=True).start()

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

    def _open_browser(self):
        """Open browser and reset cursor once done."""
        with _Busy(self._root, [self._label]):
            webbrowser.open(self._url)

    def _copy_text(self):
        """Copy hyperlink text to clipboard."""
        self._root.clipboard_clear()
        self._root.clipboard_append(self._label.cget('text'))


class _LogBox:
    """Multi-line text box in GUI for logging purposes.

    Textbox can be used as replacement for sys.stdout or sys.stderr. (Ref:
    www.blog.pythonlibrary.org/2014/07/14/tkinter-redirecting-stdout-stderr/)

    Methods:
        __init__ -- initializer
        write -- append string to text box
        flush -- update text box content immediately
        get -- return value of text box
        reset -- delete text box content
        row -- return row index of location in grid

    Attribute:
        _text -- Tk Text object
    """

    def __init__(self, root, width, height):
        """Initialize text box.

        Widget is added to the last empty row of root.

        Arguments:
            root -- parent widget
            width -- initial width of text field
            height -- initial height of text field
        """
        # Create text box and scroll bar
        self._text = tk.Text(root, width=width, height=height,
                             state='disabled', cursor='', wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(root, command=self._text.yview)
        self._text['yscrollcommand'] = scrollbar.set
        row = root.grid_size()[1]
        self._text.grid(row=row, column=0, columnspan=2, sticky='news')
        scrollbar.grid(row=row, column=2, sticky='news')
        # Create tags for line formatting
        font = tk.font.nametofont(name=self._text.cget('font'))
        indent = font.measure('CRITICAL - ')
        self._text.tag_configure('first', lmargin2=indent)
        self._text.tag_configure('other', lmargin1=indent, lmargin2=indent)

    def write(self, string):
        """Append string to text box.

        Argument:
            string -- string to be appended
        """
        lines = string.splitlines(keepends=True)
        self._text.config(state='normal')
        self._text.insert('end', lines[0], 'first')
        for line in lines[1:]:
            self._text.insert('end', line, 'other')
        self._text.config(state='disabled')
        self._text.see('end')

    def flush(self):
        """Update text box content immediately."""
        self._text.update_idletasks()

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
    try:
        root = tk.Tk()
        root.withdraw()
        _set_icon(root)
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
        root.protocol('WM_DELETE_WINDOW', main_window.on_delete)
        root.deiconify()
        root.mainloop()
    except Exception:
        _misc_logger.exception(_UNEXPECTED)


def create_shortcuts():
    """Start GUI for shortcut creation."""
    # pylint: disable=broad-except
    # Reason: exception logged
    _app.set_log_stream(sys.stderr)
    if platform.system() == 'Windows':
        if 'win32com.client' in sys.modules:
            sw_init = _ShortcutWindow.for_windows
        else:
            _misc_logger.error('On Microsoft Windows, shortcut creation '
                               'requires the pywin32 package.')
            return
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
