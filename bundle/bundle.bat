REM Bundle ERRERS using virtual environment
REM
REM SPDX-FileCopyrightText: 2023 His Majesty the King in Right of Canada, as represented by the Minister of National Defence
REM
REM SPDX-License-Identifier: LicenseRef-MIT-DND
REM
REM This file is part of the ERRERS package.

set PY_PYTHON=3.11

REM Determine which python command to use
if "%1" NEQ "" (set PYTHON=%1 & goto run)

where /q py
if %ERRORLEVEL% EQU 0 (set PYTHON=py & goto run)

where /q python
if %ERRORLEVEL% EQU 0 (set PYTHON=python & goto run)

where /q python3
if %ERRORLEVEL% EQU 0 (set PYTHON=python3 & goto run)

echo "Python not found"
exit /b 1

:run

REM Ensure script is run in correct directory
cd %~dp0

REM Delete old files (if applicable)
rmdir /s /q dist
rmdir /s /q venv

REM Create and activate virtual environment
%PYTHON% -m venv venv
call venv\Scripts\activate

REM Reactivate echo (turned off by activate script)
echo on

REM Upgrade and install required packages
python -m pip install --upgrade pip
python -m pip install wheel
python -m pip install pyinstaller
python -m pip install ..

REM Bundle application
pyinstaller errers.spec --noconfirm --clean

REM Deactivate virtual environment
call deactivate

REM Keep window open until user presses a key if launched by double-clicking
REM Ref: https://stackoverflow.com/questions/5859854/
if /i %0 equ "%~dpnx0" pause
