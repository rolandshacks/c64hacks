@ECHO OFF

REM #
REM # sidc - Sid file data extractor
REM # (C) Roland Schabenberger
REM #

SETLOCAL
PUSHD %~dp0
SET SCRIPT_DIR=%CD%
POPD
python %SCRIPT_DIR%\sidc.py %1 %2 %3 %4 %5 %6 %7 %8
ENDLOCAL
