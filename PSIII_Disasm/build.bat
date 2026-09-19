@ECHO OFF

REM // make sure we can write to the file ps3built.bin
REM // also make a backup to ps3built.prev.bin
IF NOT EXIST ps3built.bin goto LABLNOCOPY
IF EXIST ps3built.prev.bin del ps3built.prev.bin
IF EXIST ps3built.prev.bin goto LABLNOCOPY
move /Y ps3built.bin ps3built.prev.bin
IF EXIST ps3built.bin goto LABLERROR3
:LABLNOCOPY

REM // delete some intermediate assembler output just in case
IF EXIST ps3.p del ps3.p
IF EXIST ps3.p goto LABLERROR2
IF EXIST ps3.h del ps3.h
IF EXIST ps3.h goto LABLERROR1

REM // clear the output window
REM cls

REM // run the assembler
REM // -xx shows the most detailed error output
REM // -E creates log file for errors/warnings
REM // -A gives us a small speedup
set AS_MSGPATH=AS/win32
set USEANSI=n

REM // allow the user to choose to output error messages to file by supplying the -logerrors parameter
IF "%1"=="-logerrors" ( "AS/win32/asw.exe" -xx -c -E -A -L ps3.asm ) ELSE "AS/win32/asw.exe" -xx -c -E -A -L ps3.asm

REM // if there were errors, a log file is produced
IF EXIST ps3.log goto LABLERROR4

REM // combine the assembler output into a rom
IF EXIST ps3.p "AS/win32/ps3p2bin" ps3.p ps3built.bin ps3.h

REM // done -- pause if we seem to have failed, then exit
IF NOT EXIST ps3.p goto LABLPAUSE
IF NOT EXIST ps3built.bin goto LABLPAUSE
fixheader ps3built.bin
exit /b
:LABLPAUSE

pause


exit /b

:LABLERROR1
echo Failed to build because write access to ps3.h was denied.
pause


exit /b

:LABLERROR2
echo Failed to build because write access to ps3.p was denied.
pause


exit /b

:LABLERROR3
echo Failed to build because write access to ps3built.bin was denied.
pause

exit /b

:LABLERROR4
REM // display a noticeable message
echo.
echo ***************************************************************************
echo *                                                                         *
echo *   There were build errors/warnings. See ps3.log for more details.   *
echo *                                                                         *
echo ***************************************************************************
echo.
pause

