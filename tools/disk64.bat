@ECHO OFF

REM #
REM # disk64 - Disk tool for C64 .D64 files
REM # (C) Roland Schabenberger
REM #

SETLOCAL
PUSHD %~dp0
SET SCRIPT_DIR=%CD%
POPD
python %SCRIPT_DIR%\disk64.py %1 %2 %3 %4 %5 %6 %7 %8
ENDLOCAL
