..
   SPDX-FileCopyrightText: 2023 His Majesty in Right of Canada

   SPDX-License-Identifier: LicenseRef-MIT-DND

   This file is part of the ERRERS package.

==============================
ERRERS: Standalone Application
==============================

The ERRERS source distribution includes a script that be used to bundle ERRERS
and its dependencies into a package that can be run on Microsoft Windows
computers where Python is not installed.

Creation
========

To create the bundle, follow the following steps on a Windows computer:

1. Install one of the official releases of Python from
   https://python.org/downloads (64-bit Windows installer recommended). To
   install Python for the current user only, uncheck the box beside "Install
   launcher for all users" (installing for all users requires administrative
   rights).
2. Download the source distribution of
   ERRERS from https://pypi.org/project/errers/#files or
   https://github.com/steve-guillouzic-gc/errers/releases. The file is called
   errers-VERSION.zip, where VERSION is the desired ERRERS version number.
3. Unzip the errers-VERSION.zip file, and open the errers-VERSION folder.
4. Double-click on the bundle.bat file in the bundle subfolder. This opens a
   command window and initiates the creation of the ERRERS bundle. The process
   takes a few minutes. Once done, the bundle is placed in a subfolder called
   "dist", and the messages "Bundling done" and "Press any key to continue..."
   are displayed in the command window. Press any key to close the command
   window and open the dist folder. The bundle is available in two formats: a
   folder and a zip file, which are respectively called errers-VERSION-windows
   and errers-VERSION-windows.zip.

Notes:

a) The bundling algorithm fetches packages online using the pip package
   installer. It fails on networks where firewalls prevent pip from doing this.
b) The bundling algorithm may work with other Python distributions. For
   instance, with Anaconda, the bundling can be done by launching the Anaconda
   Prompt from the Start Menu, navigating to the directory that contains the
   bundle.bat file, and entering the "bundle.bat" command at the command
   prompt. Bundles created using Anaconda are a bit larger than those generated
   using the official releases of Python, because they contain additional
   files.

Installation
============

To install the resulting standalone application:

1. Copy the errers-VERSION-windows folder or the errers-VERSION-windows.zip
   file to the computer where you want to run ERRERS. They can be placed in an
   arbitrary location on the destination computer.
2. If applicable, unzip the errers-VERSION-windows.zip file. It can then be
   deleted.
3. Open a command prompt and change directory to the errers-VERSION-windows
   folder, which contains the errers.exe file.
4. Type ``errers --shortcuts`` at the command prompt and press enter.
5. In the shortcut-creation window that appears, choose the locations where you
   would like application shortcuts to be created and click "Create". The
   available locations on Windows are Desktop, "Send To" menu, and Start menu.
6. Copy shortcuts to other locations if desired, such as the Windows taskbar.

Removal
=======

To remove the standalone application:

1. Open a command prompt and change directory to the errers-VERSION-windows
   folder, which contains the errers.exe file.
2. Type ``errers --shortcuts`` at the command prompt and press enter.
3. In the shortcut-update window that appears, click "Delete" to delete
   application shortcuts. If shortcuts had been copied to other locations, they
   must be deleted manually.
4. Delete the errers-VERSION-windows folder.

Note: Bundled application requires redistributable files from Microsoft Visual
Studio. Without them, Windows complains about being unable to load the Python
DLL when starting ERRERS. For applications compiled with Python 3.6 to 3.12,
they can be installed using the freely available "Microsoft Visual C++
Redistributable for Visual Studio 2015-2022":
https://learn.microsoft.com/en-US/cpp/windows/latest-supported-vc-redist.
