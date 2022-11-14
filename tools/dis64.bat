@ECHO OFF

REM #
REM # dis64 - Disassembler for MOS 6502/6510
REM # (C) Roland Schabenberger
REM #

SETLOCAL
PUSHD %~dp0
SET SCRIPT_DIR=%CD%
POPD
python %SCRIPT_DIR%\dis64.py %1 %2 %3 %4 %5 %6 %7 %8
ENDLOCAL
