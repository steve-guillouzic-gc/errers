# SPDX-FileCopyrightText: 2023 His Majesty the King in Right of Canada, as represented by the Minister of National Defence
#
# SPDX-License-Identifier: LicenseRef-MIT-DND
#
# This file is part of the ERRERS package.

Files in this directory can be used to bundle ERRERS and its dependencies into
a package that can be run on Microsoft Windows computers where Python is
not installed. To create the bundle, follow the following steps on a Windows
computer:
1. Install one of the official releases of Python from
   https://python.org/downloads (64-bit Windows installer recommended). During
   installation, check the box beside "Add Python 3.X to PATH", where 3.X is
   the version of Python being installed. To install Python for the current
   user only, uncheck the box beside "Install launcher for all users"
   (installing for all users requires administrative rights).
2. Double-click on the bundle.bat file in this directory. This will create the
   ERRERS bundle and place it in a subdirectory called "dist". The bundle is
   available in two formats: a directory and a zip file. They are respectively
   called ERRERS_v3.Y and ERRERS_v3.Y_windows.zip, where 3.Y is the version of
   ERRERS being bundled.

To install the resulting bundle:
1. Copy the ERRERS_v3.Y directory or the ERRERS_v3.Y_windows.zip file to the
   computer where you want to run ERRERS. They can be placed in an arbitrary
   location on the destination computer, but the zip file must be unzipped.
2. Open a command prompt and change directory to the ERRERS_v3.Y directory,
   which contains the errers.exe file.
3. Type ``errers --shortcuts`` at the command prompt and press enter.
4. In the shortcut-creation window that appears, choose the locations where you
   would like application shortcuts to be created and click "Create". The
   available locations on Windows are Desktop, "Send To" menu, and Start menu.
5. Copy shortcuts to other locations if desired, such as the Windows taskbar.

Notes:
a) Bundled application requires redistributable files from Microsoft Visual
   Studio. Without them, Windows complains about being unable to load the
   Python DLL when starting ERRERS. For applications compiled with Python 3.6
   to 3.12, they can be installed using the freely available "Microsoft Visual 
   C++ Redistributable for Visual Studio 2015-2022":
   https://learn.microsoft.com/en-US/cpp/windows/latest-supported-vc-redist.
b) The bundling algorithm fetches packages online using the pip package
   installer. It fails on networks where firewalls prevent pip from doing this.
c) The bundling algorithm may work with other Python distributions. For
   instance, with Anaconda, the bundling can be done by launching the Anaconda
   Prompt from the Start Menu, navigating to the directory that contains the
   bundle.bat file, and entering the "bundle.bat" command at the command
   prompt. Bundles created using Anaconda are a bit larger than those generated
   using the official releases of Python, because they contain additional
   files.
