# -*- mode: python ; coding: utf-8 -*-
#
# SPDX-FileCopyrightText: 2023 His Majesty in Right of Canada
#
# SPDX-License-Identifier: LicenseRef-MIT-DND
#
# This file is part of the ERRERS package.

import sys
import os
import shutil
import pathlib
import sysconfig
import re
sys.path.insert(0, '..')
import errers

# Prepare file with version information

version_info_string = f"""
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ), 
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct('CompanyName', 'Defence Research and Development Canada'),
        StringStruct('FileDescription', '{errers.LONGNAME}'),
        StringStruct('FileVersion', '{errers.__version__}'),
        StringStruct('InternalName', '{errers.SHORTNAME}'),
        StringStruct('LegalCopyright', 'DND - MDN. Contains third-party components subject to separate licenses.'),
        StringStruct('OriginalFilename', 'errers.exe'),
        StringStruct('ProductName', '{errers.SHORTNAME}'),
        StringStruct('ProductVersion', '{errers.__version__}')])
      ]), 
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""

with open('version_info.txt', 'w') as version_info:
    version_info.write(version_info_string)

# Standard spec file content

block_cipher = None

base_dir = pathlib.Path(sys.base_prefix)
venv_dir = pathlib.Path(sysconfig.get_paths()['purelib'])
license_dir = pathlib.Path('Third party licenses')
pywin32_dir = license_dir.joinpath('pywin32')

main_a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('../src/errers/icon/errers.ico', 'errers/icon'),
           ('../src/errers/icon/errers32.png', 'errers/icon'),
           ('../README.rst', 'doc'),
           ('../CHANGELOG.rst', 'doc'),
           ('../CONTRIBUTING.rst', 'doc'),
           ('../LICENSES/LicenseRef-MIT-DND.txt', 'doc')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

main_pyz = PYZ(main_a.pure, main_a.zipped_data, cipher=block_cipher)

main_exe = EXE(
    main_pyz,
    main_a.scripts,
    [],
    exclude_binaries=True,
    name='errers',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon='../src/errers/icon/errers.ico',
)

coll = COLLECT(
    main_exe,
    main_a.binaries,
    main_a.zipfiles,
    main_a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=errers.SHORTNAME,
)

# Move documentation to main folder and rename to .txt

errers_dir = pathlib.Path('dist/errers')
internal_dir = errers_dir.joinpath('_internal')
doc_dir = internal_dir.joinpath('doc')
for file in doc_dir.glob('*'):
    file.rename(errers_dir.joinpath(file.with_suffix('.txt').name))
license = errers_dir.joinpath('LicenseRef-MIT-DND.txt')
license.rename(license.parent.joinpath('LICENSE.txt'))
doc_dir.rmdir()

# Copy third-party software licenses

base_dir = pathlib.Path(sys.base_prefix)
venv_dir = pathlib.Path(sysconfig.get_paths()['purelib'])
license_dir = errers_dir.joinpath('Third party licenses')
pywin32_dir = license_dir.joinpath('pywin32')
license_dir.mkdir()
pywin32_dir.mkdir()
shutil.copy(base_dir.joinpath('LICENSE.txt'),
            license_dir.joinpath('Python.txt'))
shutil.copy(base_dir.joinpath('tcl/tk8.6/license.terms'),
            license_dir.joinpath('Tcl_Tk.txt'))
shutil.copy(venv_dir.joinpath('pythonwin/license.txt'),
            pywin32_dir.joinpath('pythonwin.txt'))
shutil.copy(next(venv_dir.glob('pywin32_ctypes-*.dist-info/LICENSE.txt')),
            pywin32_dir.joinpath('pywin32_ctypes.txt'))
shutil.copy(venv_dir.joinpath('win32/license.txt'),
            pywin32_dir.joinpath('win32.txt'))
shutil.copy(venv_dir.joinpath('win32com/license.txt'),
            pywin32_dir.joinpath('win32com.txt'))
shutil.copy(next(venv_dir.glob('regex-*.dist-info/LICENSE.txt')),
            license_dir.joinpath('regex.txt'))
shutil.copy(next(venv_dir.glob('pyinstaller-*.dist-info/COPYING.txt')),
            license_dir.joinpath('pyinstaller.txt'))

# Delete redistributable Microsoft files.

for msfile in internal_dir.glob('**/vcruntime*.dll'):
    msfile.unlink()
for msfile in internal_dir.glob('**/mfc*.dll'):
    msfile.unlink()

# Rename distribution directory and create zip file.

origin = pathlib.Path('./dist/errers')
target = pathlib.Path(f'./dist/errers-{errers.__version__}-windows')
shutil.move(errers_dir, target)
shutil.make_archive(target, 'zip', target)

# Copy README file to dist folder.

origin = pathlib.Path('README.txt')
target = pathlib.Path('dist')
shutil.copy(origin, target)
