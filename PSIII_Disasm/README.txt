=============================================================
| PHANTASY STAR III DISASSEMBLY FOR MEGA DRIVE/SEGA GENESIS |
=============================================================

---------------------------------------------------------------------------
	Macro Assembler AS
	
Used to assemble code of many processors including Motorola 68000 and Z80

Here's the home page for this assembler:

http://john.ccac.rwth-aachen.de:8000/as/

Here's the documentation for AS:

http://john.ccac.rwth-aachen.de:8000/as/as_EN.html


Some basic features you should know:

	- Nameless Temporary Symbols
	- String Constants
	- Operators
	- CHARSET instruction
	
Knowledge of common features for assemblers is recommended. 
Particularly you should be familiar with labels, macros and the ORG instruction

---------------------------------------------------------------------------

---------------------------------------------------------------------------
	build.bat
	
Just double-click on this file and a Phantasy Star III bin file should be produced
If a bin file is not produced, then an error in the asm code most likely occurred.
If a PSIII bin file already exists, then a copy of the previous file is kept
---------------------------------------------------------------------------

---------------------------------------------------------------------------
	chkbitperfect.bat
	
Compares the ROM produced by the disassembly with the original ROM.
The internal checksum of the original ROM should be 0x3A33.
After you get a hold of it, rename it to ps3original.bin. 
You can change the name of this ROM provided that you do so in the
chkbitperfect.bat file as well.
---------------------------------------------------------------------------

---------------------------------------------------------------------------
	fixheader.exe
	
Automatically fixes the checksum of the produced ROM after assembling.
---------------------------------------------------------------------------