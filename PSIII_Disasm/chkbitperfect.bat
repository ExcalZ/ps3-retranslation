@ECHO OFF

REM // build the ROM
call build %1

REM  // run fc
echo -------------------------------------------------------------
IF EXIST ps3built.bin ( fc /b ps3built.bin ps3original.bin
) ELSE echo ps3built.bin does not exist, probably due to an assembly error

REM // clean up after us
IF EXIST ps3.p del ps3.p
IF EXIST ps3.h del ps3.h
IF EXIST ps3.lst del ps3.lst
IF EXIST ps3built.bin del ps3built.bin
IF EXIST ps3built.prev.bin del ps3built.prev.bin
IF EXIST ps3.log ( IF "%1"=="-pe" del ps3.log )

REM // if someone ran this from Windows Explorer, prevent the window from disappearing immediately
pause
