	cpu Z80
	listing off

; ====================================================
SFXPtrTableZ80:
	dw	zloc_105C
	dw	zloc_108F
	dw	zloc_10BB
	dw	zloc_10EA
	dw	zloc_1112
	dw	zloc_115E
	dw	zloc_118F
	dw	zloc_11B7
	dw	zloc_11E1
	dw	zloc_1231
	dw	zloc_1259
	dw	zloc_128F
	dw	zloc_12B7
	dw	zloc_12E0
	dw	zloc_130A
	dw	zloc_1334
	dw	zloc_135C
	dw	zloc_1385
	dw	zloc_13B8
	dw	zloc_1404
	dw	zloc_142D
	dw	zloc_1459
	dw	zloc_1494
	dw	zloc_14BD
	dw	zloc_14ED
	dw	zloc_1515
	dw	zloc_153E
	dw	zloc_156A
	dw	zloc_1595
	dw	zloc_15D6
	dw	zloc_1600
	dw	zloc_162F
	dw	zloc_165E
	dw	zloc_1688
	dw	zloc_16CD
	dw	zloc_16FE
	dw	zloc_172A
	dw	zloc_1780
	dw	zloc_17B2
	dw	zloc_1802
	dw	zloc_182E
	dw	zloc_1856
; ====================================================
	
; Special SFX pointers
; ====================================================
SpecialSFXPtrs:
	dw	zloc_1688
	dw	zloc_16CD
	dw	zloc_156A
	dw	zloc_1802
; ====================================================
	
zloc_105C:
	db	76h, 10h, 01h, 02h
	db	80h, 06h, 6Ch, 10h, 00h, 0Bh, 80h, 0A0h, 71h, 10h, 00h, 03h, 0EFh, 00h, 0F6h, 73h
	db	10h, 0F5h, 09h, 0A0h, 06h, 0F2h, 07h, 38h, 38h, 38h, 37h, 1Fh, 1Fh, 1Fh, 1Fh, 0Fh
	db	1Fh, 4Ch, 2Ah, 05h, 04h, 05h, 04h, 0FFh, 0FFh, 0FFh, 0FFh, 92h, 80h, 92h, 80h
	
zloc_108F:
	db	0A2h
	db	10h, 01h, 01h, 0A0h, 06h, 99h, 10h, 05h, 00h, 0EFh, 00h, 96h, 00h, 03h, 9Fh, 07h
	db	0Ch, 0F2h, 2Ah, 03h, 06h, 06h, 06h, 1Fh, 1Fh, 1Fh, 1Fh, 00h, 10h, 03h, 0Dh, 07h
	db	32h, 02h, 0Ah, 7Fh, 6Fh, 5Fh, 5Fh, 00h, 00h, 10h, 80h
	
zloc_10BB:
	db	0D1h, 10h, 01h, 01h, 0A0h
	db	06h, 0C5h, 10h, 01h, 00h, 0EFh, 00h, 93h, 00h, 03h, 93h, 00h, 03h, 99h, 0FCh, 0Ch
	db	0F2h, 2Dh, 00h, 32h, 11h, 14h, 1Fh, 1Eh, 1Fh, 1Fh, 4Dh, 0Dh, 09h, 0Fh, 1Fh, 1Dh
	db	1Ch, 16h, 7Dh, 6Dh, 5Dh, 5Dh, 00h, 83h, 90h, 80h
	
zloc_10EA:
	db	0F9h, 10h, 01h, 01h, 80h, 06h
	db	0F4h, 10h, 08h, 00h, 0EFh, 00h, 8Dh, 10h, 0F2h, 3Ah, 2Bh, 25h, 25h, 2Ah, 1Fh, 1Fh
	db	1Fh, 1Fh, 10h, 06h, 15h, 0Dh, 00h, 12h, 0Ah, 19h, 7Fh, 6Fh, 5Fh, 5Fh, 00h, 00h
	db	10h, 80h
	
zloc_1112:
	db	2Ch, 11h, 01h, 02h, 80h, 06h, 22h, 11h, 00h, 00h, 80h, 05h, 27h, 11h
	db	00h, 00h, 0EFh, 00h, 0F6h, 29h, 11h, 0EFh, 01h, 8Dh, 10h, 0F2h, 23h, 30h, 31h, 78h
	db	78h, 0Eh, 1Eh, 1Fh, 1Fh, 0Dh, 08h, 1Ah, 0Fh, 01h, 00h, 18h, 0Ah, 7Fh, 6Fh, 5Fh
	db	5Fh, 00h, 00h, 09h, 80h, 36h, 31h, 31h, 78h, 78h, 0Eh, 1Fh, 1Fh, 1Fh, 0Dh, 08h
	db	1Ah, 3Fh, 01h, 00h, 18h, 3Ah, 7Fh, 6Fh, 5Fh, 5Fh, 00h, 80h, 89h, 80h
	
zloc_115E:
	db	76h, 11h
	db	01h, 01h, 80h, 06h, 68h, 11h, 00h, 00h, 0EFh, 00h, 86h, 03h, 80h, 01h, 0F7h, 00h
	db	05h, 68h, 11h, 88h, 05h, 0F2h, 32h, 0Ch, 03h, 02h, 01h, 1Fh, 1Eh, 1Fh, 1Fh, 8Eh
	db	8Ch, 85h, 9Fh, 00h, 03h, 00h, 05h, 0FAh, 0FAh, 37h, 08h, 20h, 13h, 10h, 80h
	
zloc_118F:
	db	9Eh
	db	11h, 01h, 01h, 80h, 0A0h, 99h, 11h, 00h, 00h, 0F5h, 00h, 0A2h, 05h, 0F2h, 05h, 06h
	db	06h, 06h, 06h, 1Fh, 1Fh, 1Fh, 1Fh, 02h, 06h, 13h, 0Fh, 00h, 12h, 0Ch, 1Ah, 7Fh
	db	6Fh, 5Fh, 5Fh, 00h, 84h, 9Bh, 80h
	
zloc_11B7:
	db	0C8h, 11h, 01h, 01h, 80h, 06h, 0C1h, 11h, 00h
	db	00h, 0EFh, 00h, 8Dh, 04h, 92h, 06h, 0F2h, 18h, 00h, 13h, 24h, 23h, 1Eh, 1Eh, 1Fh
	db	1Fh, 07h, 14h, 14h, 2Bh, 05h, 01h, 04h, 1Ah, 7Fh, 6Fh, 5Fh, 5Fh, 00h, 04h, 1Bh
	db	80h
	
zloc_11E1:
	db	0FFh, 11h, 01h, 02h, 0A0h, 05h, 0F1h, 11h, 00h, 00h, 0A0h, 06h, 0F6h, 11h, 00h
	db	00h, 0EFh, 00h, 0F6h, 0F8h, 11h, 0EFh, 01h, 95h, 0FEh, 06h, 98h, 20h, 0Ch, 0F2h, 31h
	db	01h, 52h, 33h, 30h, 1Fh, 1Fh, 0Fh, 19h, 00h, 00h, 1Ch, 00h, 00h, 00h, 0Ah, 00h
	db	0FFh, 0FCh, 0FFh, 0F9h, 1Ah, 10h, 10h, 88h, 31h, 00h, 0Bh, 33h, 30h, 1Fh, 1Fh, 0Fh
	db	1Fh, 04h, 02h, 15h, 00h, 04h, 00h, 0Ah, 00h, 0FFh, 0FCh, 0FFh, 0F9h, 1Ah, 10h, 10h
	db	88h
	
zloc_1231:
	db	40h, 12h, 01h, 01h, 80h, 06h, 3Bh, 12h, 00h, 00h, 0EFh, 00h, 8Dh, 40h, 0F2h
	db	0Fh, 37h, 33h, 32h, 32h, 1Ch, 0Bh, 0Dh, 1Fh, 27h, 26h, 25h, 2Fh, 16h, 12h, 3Ch
	db	3Ah, 7Fh, 6Fh, 5Fh, 5Fh, 80h, 84h, 9Bh, 80h
	
zloc_1259:
	db	76h, 12h, 01h, 01h, 80h, 06h, 69h
	db	12h, 00h, 00h, 80h, 0C0h, 69h, 12h, 00h, 00h, 0EFh, 00h, 8Dh, 04h, 80h, 0Ch, 8Dh
	db	04h, 80h, 0Ch, 8Dh, 04h, 0F2h, 04h, 18h, 17h, 16h, 13h, 1Fh, 1Fh, 1Fh, 1Fh, 0Fh
	db	15h, 17h, 12h, 0Fh, 15h, 17h, 12h, 0FFh, 0FFh, 0FFh, 0FFh, 10h, 80h, 00h, 80h
	
zloc_128F:
	db	9Eh
	db	12h, 01h, 01h, 80h, 06h, 99h, 12h, 00h, 00h, 0EFh, 00h, 8Dh, 18h, 0F2h, 23h, 2Dh
	db	3Eh, 3Fh, 3Ch, 1Fh, 1Fh, 1Fh, 1Fh, 02h, 10h, 0Eh, 2Dh, 02h, 10h, 0Eh, 2Bh, 7Fh
	db	6Fh, 5Fh, 5Fh, 00h, 0Ch, 1Bh, 80h
	
zloc_12B7:
	db	0C7h, 12h, 01h, 01h, 0A0h, 06h, 0C1h, 12h, 00h
	db	00h, 0EFh, 00h, 8Dh, 23h, 60h, 0F2h, 0Eh, 11h, 14h, 16h, 17h, 0Dh, 10h, 1Dh, 1Dh
	db	0Bh, 03h, 07h, 0Fh, 05h, 05h, 0Ch, 07h, 7Fh, 6Fh, 5Fh, 5Fh, 00h, 84h, 9Bh, 80h
	
zloc_12E0:
	db	0F1h, 12h, 01h, 01h, 80h, 06h, 0EAh, 12h, 00h, 00h, 0EFh, 00h, 8Dh, 06h, 0A0h, 0Bh
	db	0F2h, 1Ah, 22h, 2Ah, 5Ah, 2Bh, 1Fh, 1Fh, 1Fh, 1Fh, 08h, 0Ah, 0Ah, 0Fh, 08h, 0Ah
	db	0Ah, 0Fh, 7Fh, 7Fh, 7Fh, 7Fh, 00h, 04h, 1Bh, 80h
	
zloc_130A:
	db	1Bh, 13h, 01h, 01h, 80h, 06h
	db	14h, 13h, 00h, 00h, 0EFh, 00h, 8Dh, 40h, 80h, 20h, 0F2h, 38h, 0Fh, 0Fh, 0Fh, 00h
	db	1Fh, 1Fh, 1Fh, 06h, 80h, 80h, 80h, 80h, 40h, 80h, 0C0h, 4Ah, 00h, 03h, 03h, 06h
	db	00h, 00h, 00h, 80h
	
zloc_1334:
	db	43h, 13h, 01h, 01h, 80h, 06h, 3Eh, 13h, 00h, 00h, 0EFh, 00h
	db	8Dh, 10h, 0F2h, 0Dh, 17h, 51h, 21h, 21h, 0Eh, 0Fh, 0Fh, 1Fh, 02h, 14h, 13h, 0Fh
	db	00h, 12h, 0Ch, 1Ah, 7Fh, 6Fh, 5Fh, 5Fh, 00h, 84h, 9Bh, 80h
	
zloc_135C:
	db	6Ch, 13h, 01h, 01h
	db	0A0h, 06h, 66h, 13h, 00h, 00h, 0EFh, 00h, 97h, 0F3h, 28h, 0F2h, 3Fh, 22h, 23h, 12h
	db	02h, 1Bh, 1Bh, 14h, 11h, 0Dh, 1Dh, 0Fh, 0Fh, 0Ah, 49h, 4Ah, 01h, 07h, 2Ah, 0Bh
	db	1Fh, 86h, 86h, 95h, 83h
	
zloc_1385:
	db	9Fh, 13h, 01h, 01h, 80h, 06h, 8Fh, 13h, 00h, 00h, 0EFh
	db	00h, 8Dh, 03h, 80h, 02h, 0F7h, 00h, 04h, 91h, 13h, 8Dh, 03h, 95h, 15h, 0F2h, 3Bh
	db	26h, 13h, 12h, 12h, 0Dh, 11h, 0Fh, 1Fh, 02h, 14h, 13h, 0Fh, 00h, 12h, 0Ch, 1Ah
	db	7Ah, 6Ch, 59h, 59h, 00h, 04h, 1Bh, 80h
	
zloc_13B8:
	db	0D2h, 13h, 01h, 01h, 80h, 06h, 0C2h, 13h
	db	0FBh, 00h, 0EFh, 00h, 92h, 02h, 80h, 01h, 0F7h, 00h, 07h, 0C2h, 13h, 0EFh, 01h, 8Dh
	db	20h, 0F2h, 02h, 21h, 20h, 22h, 22h, 1Ch, 1Ch, 1Fh, 1Fh, 12h, 09h, 14h, 0Fh, 18h
	db	12h, 0Ch, 1Ah, 7Fh, 6Fh, 5Fh, 5Fh, 00h, 04h, 1Bh, 80h, 38h, 08h, 57h, 03h, 02h
	db	5Fh, 1Fh, 1Fh, 9Fh, 8Ah, 89h, 8Ah, 91h, 06h, 06h, 06h, 04h, 79h, 99h, 79h, 19h
	db	12h, 12h, 12h, 80h
	
zloc_1404:
	db	14h, 14h, 01h, 01h, 0A0h, 06h, 0Eh, 14h, 00h, 00h, 0EFh, 00h
	db	8Dh, 1Ah, 29h, 0F2h, 37h, 23h, 52h, 21h, 22h, 1Fh, 1Fh, 1Fh, 1Fh, 07h, 06h, 13h
	db	0Fh, 05h, 12h, 0Ch, 1Ah, 7Fh, 6Fh, 5Fh, 5Fh, 80h, 84h, 9Bh, 80h
	
zloc_142D:
	db	40h, 14h, 01h
	db	01h, 0A0h, 06h, 37h, 14h, 00h, 00h, 0EFh, 00h, 0C6h, 03h, 11h, 8Dh, 20h, 37h, 0F2h
	db	2Eh, 28h, 3Dh, 28h, 2Bh, 0Ch, 0Dh, 0Eh, 0Dh, 02h, 06h, 13h, 0Fh, 02h, 04h, 0Ch
	db	1Bh, 7Fh, 6Fh, 5Fh, 5Fh, 00h, 84h, 9Bh, 80h
	
zloc_1459:
	db	7Bh, 14h, 01h, 01h, 0A0h, 06h, 63h
	db	14h, 00h, 00h, 0EFh, 00h, 8Fh, 05h, 03h, 92h, 05h, 03h, 95h, 05h, 03h, 8Bh, 05h
	db	03h, 94h, 05h, 03h, 8Eh, 05h, 03h, 9Ah, 08h, 20h, 0F2h, 25h, 2Fh, 22h, 23h, 2Fh
	db	0Dh, 0Eh, 0Fh, 1Fh, 00h, 16h, 13h, 0Fh, 00h, 04h, 0Ch, 0Ah, 7Fh, 6Fh, 5Fh, 5Fh
	db	00h, 84h, 9Bh, 80h
	
zloc_1494:
	db	0A4h, 14h, 01h, 01h, 0A0h, 06h, 9Eh, 14h, 00h, 00h, 0EFh, 00h
	db	8Dh, 20h, 18h, 0F2h, 16h, 26h, 25h, 24h, 22h, 16h, 19h, 1Fh, 1Fh, 07h, 06h, 13h
	db	0Fh, 05h, 12h, 0Ch, 1Ah, 7Fh, 6Fh, 5Fh, 5Fh, 00h, 84h, 9Bh, 80h
	
zloc_14BD:
	db	0D4h, 14h, 01h
	db	01h, 80h, 06h, 0C7h, 14h, 00h, 00h, 0EFh, 00h, 9Ah, 05h, 9Ah, 05h, 9Ah, 05h, 9Ah
	db	05h, 9Ah, 05h, 0F2h, 15h, 0Fh, 0Fh, 0Fh, 0Fh, 12h, 0Eh, 1Fh, 1Fh, 00h, 11h, 1Ah
	db	12h, 01h, 04h, 00h, 01h, 0Fh, 6Fh, 0FFh, 0FFh, 00h, 80h, 80h, 80h
	
zloc_14ED:
	db	0FCh, 14h, 01h
	db	01h, 80h, 06h, 0F7h, 14h, 00h, 00h, 0EFh, 00h, 9Dh, 19h, 0F2h, 1Dh, 1Bh, 1Bh, 1Ah
	db	19h, 1Fh, 1Fh, 1Fh, 1Fh, 0Ch, 09h, 0Ch, 0Ch, 07h, 06h, 05h, 0Ah, 7Fh, 7Fh, 7Fh
	db	7Fh, 00h, 84h, 9Bh, 80h
	
zloc_1515:
	db	25h, 15h, 01h, 01h, 0A0h, 06h, 1Fh, 15h, 00h, 00h, 0EFh
	db	00h, 8Dh, 30h, 20h, 0F2h, 07h, 28h, 27h, 26h, 25h, 1Fh, 1Fh, 1Fh, 1Fh, 02h, 03h
	db	03h, 04h, 00h, 02h, 05h, 05h, 7Fh, 6Fh, 5Fh, 5Fh, 80h, 84h, 9Bh, 80h
	
zloc_153E:
	db	51h, 15h
	db	01h, 01h, 80h, 06h, 48h, 15h, 00h, 00h, 0EFh, 00h, 8Dh, 04h, 80h, 02h, 91h, 18h
	db	0F2h, 28h, 1Eh, 11h, 22h, 21h, 0Ah, 13h, 13h, 1Bh, 0Eh, 03h, 0Dh, 08h, 0Dh, 12h
	db	0Ah, 06h, 7Fh, 6Fh, 57h, 59h, 00h, 04h, 1Bh, 80h
	
zloc_156A:
	db	7Ch, 15h, 01h, 01h, 0A0h, 06h
	db	74h, 15h, 00h, 00h, 0EFh, 00h, 87h, 0FCh, 30h, 0F6h, 76h, 15h, 2Ch, 21h, 20h, 22h
	db	21h, 1Fh, 1Fh, 1Fh, 1Fh, 00h, 02h, 03h, 08h, 00h, 02h, 0Bh, 07h, 7Fh, 6Fh, 5Fh
	db	5Fh, 00h, 84h, 1Bh, 80h
	
zloc_1595:
	db	0BDh, 15h, 02h, 01h, 80h, 06h, 9Fh, 15h, 00h, 06h, 0EFh
	db	00h, 9Dh, 02h, 0A1h, 0A4h, 0A9h, 0ADh, 0B0h, 0B5h, 0B9h, 0BCh, 0C1h, 0Ch, 0E3h, 0EFh, 00h
	db	98h, 02h, 9Dh, 0A1h, 0A4h, 0A9h, 0ADh, 0B0h, 0B5h, 0B9h, 0BCh, 0Ch, 0F2h, 16h, 73h, 71h
	db	34h, 32h, 1Fh, 16h, 1Fh, 1Fh, 00h, 0Fh, 00h, 0Fh, 00h, 09h, 00h, 09h, 0FFh, 0FEh
	db	0FEh, 0FAh, 12h, 80h, 95h, 80h
	
zloc_15D6:
	db	0E7h, 15h, 01h, 01h, 80h, 06h, 0E0h, 15h, 02h, 00h
	db	0EFh, 00h, 8Dh, 07h, 95h, 08h, 0F2h, 33h, 11h, 12h, 02h, 02h, 1Fh, 1Fh, 1Fh, 1Fh
	db	0Fh, 0Dh, 1Fh, 0Bh, 0Fh, 1Bh, 0Bh, 02h, 0Fh, 2Fh, 0Fh, 1Fh, 06h, 06h, 15h, 83h
	
zloc_1600:
	db	16h, 16h, 01h, 01h, 0A0h, 06h, 0Ah, 16h, 00h, 00h, 0EFh, 00h, 8Bh, 04h, 0Dh, 8Bh
	db	09h, 0Eh, 92h, 0F1h, 24h, 0F2h, 3Bh, 38h, 53h, 21h, 31h, 4Eh, 1Fh, 1Fh, 9Fh, 8Ah
	db	89h, 8Ah, 91h, 06h, 06h, 06h, 04h, 75h, 96h, 76h, 16h, 12h, 12h, 12h, 80h
	
zloc_162F:
	db	45h
	db	16h, 01h, 01h, 80h, 06h, 39h, 16h, 00h, 00h, 0EFh, 00h, 8Dh, 04h, 0F7h, 00h, 05h
	db	3Bh, 16h, 8Ah, 08h, 0F2h, 29h, 06h, 57h, 03h, 02h, 5Fh, 1Fh, 1Fh, 9Fh, 8Ah, 89h
	db	8Ah, 91h, 06h, 06h, 06h, 04h, 76h, 96h, 76h, 16h, 12h, 12h, 12h, 80h
	
zloc_165E:
	db	6Fh, 16h
	db	01h, 01h, 80h, 06h, 68h, 16h, 00h, 00h, 0EFh, 00h, 8Dh, 07h, 90h, 06h, 0F2h, 35h
	db	00h, 02h, 01h, 01h, 1Fh, 1Fh, 1Fh, 1Fh, 0Eh, 0Dh, 0Ch, 06h, 0Eh, 0Dh, 08h, 07h
	db	1Fh, 2Fh, 1Fh, 1Fh, 06h, 86h, 95h, 83h
	
zloc_1688:
	db	0B4h, 16h, 01h, 01h, 80h, 06h, 92h, 16h
	db	00h, 04h, 0EFh, 00h, 8Dh, 08h, 80h, 03h, 0E6h, 0FEh, 8Dh, 08h, 80h, 03h, 0E6h, 0FEh
	db	8Dh, 08h, 80h, 03h, 0E6h, 02h, 8Dh, 08h, 80h, 03h, 0E6h, 02h, 8Dh, 13h, 80h, 70h
	db	0F6h, 92h, 16h, 0F2h, 3Eh, 04h, 01h, 02h, 10h, 0Eh, 0Eh, 0Bh, 01h, 05h, 0Fh, 06h
	db	00h, 00h, 12h, 05h, 00h, 80h, 59h, 3Fh, 5Fh, 00h, 84h, 9Bh, 80h
	
zloc_16CD:
	db	0E5h, 16h, 01h
	db	01h, 80h, 06h, 0D7h, 16h, 0FBh, 09h, 0EFh, 00h, 8Dh, 01h, 80h, 0Bh, 92h, 05h, 80h
	db	03h, 0F6h, 0D7h, 16h, 0F2h, 39h, 07h, 5Ah, 05h, 02h, 5Fh, 1Fh, 1Fh, 9Fh, 8Ah, 89h
	db	8Ah, 91h, 06h, 06h, 06h, 04h, 79h, 99h, 79h, 19h, 12h, 12h, 12h, 80h
	
zloc_16FE:
	db	11h, 17h
	db	01h, 01h, 0A0h, 06h, 08h, 17h, 00h, 00h, 0EFh, 00h, 82h, 03h, 0Bh, 8Dh, 1Bh, 20h
	db	0F2h, 02h, 2Dh, 3Fh, 3Eh, 3Ch, 1Fh, 1Fh, 1Fh, 1Fh, 02h, 10h, 0Eh, 2Dh, 02h, 10h
	db	0Eh, 2Bh, 7Fh, 6Fh, 5Fh, 5Fh, 00h, 0Ch, 1Bh, 80h
	
zloc_172A:
	db	4Eh, 17h, 01h, 02h, 0A0h, 05h
	db	3Ah, 17h, 00h, 00h, 0A0h, 06h, 49h, 17h, 00h, 00h, 0EFh, 00h, 88h, 00h, 07h, 88h
	db	00h, 07h, 88h, 04h, 20h, 8Dh, 0FBh, 70h, 0F2h, 0EFh, 01h, 0F6h, 3Ch, 17h, 37h, 53h
	db	32h, 32h, 32h, 0Fh, 0Fh, 1Fh, 1Fh, 04h, 08h, 03h, 07h, 00h, 08h, 07h, 04h, 7Ah
	db	69h, 8Ah, 59h, 80h, 84h, 9Bh, 80h, 29h, 30h, 31h, 31h, 31h, 1Fh, 1Fh, 1Fh, 1Fh
	db	03h, 12h, 00h, 03h, 01h, 16h, 16h, 14h, 7Ah, 69h, 8Ah, 59h, 00h, 04h, 1Bh, 80h
	
zloc_1780:
	db	99h, 17h, 01h, 01h, 0A0h, 06h, 8Ah, 17h, 00h, 00h, 0EFh, 00h, 8Fh, 05h, 03h, 90h
	db	05h, 03h, 90h, 05h, 03h, 90h, 00h, 50h, 0F2h, 3Ch, 11h, 12h, 21h, 22h, 09h, 0Fh
	db	1Fh, 1Fh, 02h, 06h, 06h, 0Fh, 00h, 02h, 0Ch, 0Ah, 79h, 6Ah, 5Ah, 5Ah, 00h, 84h
	db	1Bh, 80h
	
zloc_17B2:
	db	0D0h, 17h, 01h, 02h, 80h, 05h, 0C2h, 17h, 00h, 00h, 80h, 06h, 0CBh, 17h
	db	00h, 00h, 0EFh, 00h, 84h, 07h, 85h, 06h, 8Ah, 20h, 0F2h, 0EFh, 01h, 0F6h, 0C4h, 17h
	db	34h, 11h, 21h, 21h, 21h, 0Fh, 0Fh, 1Fh, 1Fh, 03h, 06h, 03h, 02h, 05h, 02h, 04h
	db	03h, 7Fh, 6Fh, 5Fh, 5Fh, 00h, 84h, 1Bh, 80h, 33h, 53h, 32h, 32h, 32h, 0Fh, 0Fh
	db	1Fh, 1Fh, 04h, 08h, 03h, 07h, 00h, 08h, 07h, 04h, 7Ah, 69h, 8Ah, 59h, 00h, 04h
	db	1Bh, 80h
	
zloc_1802:
	db	15h, 18h, 01h, 01h, 80h, 06h, 0Ch, 18h, 00h, 00h, 0EFh, 00h, 84h, 07h
	db	80h, 01h, 0F6h, 0Eh, 18h, 04h, 21h, 20h, 22h, 21h, 1Fh, 1Fh, 1Fh, 1Fh, 00h, 02h
	db	03h, 08h, 00h, 02h, 0Bh, 07h, 7Fh, 6Fh, 5Fh, 5Fh, 00h, 84h, 1Bh, 80h
	
zloc_182E:
	db	3Dh, 18h
	db	01h, 01h, 80h, 06h, 38h, 18h, 00h, 00h, 0EFh, 00h, 9Dh, 19h, 0F2h, 1Dh, 1Bh, 1Bh
	db	1Ah, 19h, 1Fh, 1Fh, 1Fh, 1Fh, 0Ch, 09h, 0Ch, 0Ch, 07h, 06h, 05h, 0Ah, 7Fh, 7Fh
	db	7Fh, 7Fh, 00h, 84h, 9Bh, 80h
	
zloc_1856:
	db	66h, 18h, 01h, 01h, 0A0h, 06h, 60h, 18h, 00h, 00h
	db	0EFh, 00h, 8Dh, 30h, 20h, 0F2h, 07h, 28h, 27h, 26h, 25h, 1Fh, 1Fh, 1Fh, 1Fh, 02h
	db	03h, 03h, 04h, 00h, 02h, 05h, 05h, 7Fh, 6Fh, 5Fh, 5Fh, 80h, 84h, 9Bh, 80h, 92h
	db	18h, 01h, 01h, 80h, 06h, 89h, 18h, 00h, 00h, 0EFh, 00h, 8Dh, 04h, 80h, 02h, 91h
	db	18h, 0F2h, 28h, 1Eh, 11h, 22h, 21h, 0Ah, 13h, 13h, 1Bh, 0Eh, 03h, 0Dh, 08h, 0Dh
	db	12h, 0Ah, 06h, 7Fh, 6Fh, 57h, 59h, 00h, 04h, 1Bh, 80h, 0BAh, 18h, 01h, 01h, 80h
	db	06h, 0B5h, 18h, 00h, 00h, 0EFh, 00h, 8Ah, 10h, 0F2h, 07h, 21h, 20h, 22h, 22h, 1Fh
	db	1Fh, 1Fh, 1Fh, 00h, 02h, 03h, 08h, 00h, 02h, 0Bh, 07h, 7Fh, 6Fh, 5Fh, 5Fh, 80h
	db	84h, 9Bh, 80h, 0FBh, 18h, 02h, 01h, 80h, 06h, 0DDh, 18h, 00h, 06h, 0EFh, 00h, 9Dh
	db	02h, 0A1h, 0A4h, 0A9h, 0ADh, 0B0h, 0B5h, 0B9h, 0BCh, 0C1h, 0Ch, 0E3h, 0EFh, 00h, 98h, 02h
	db	9Dh, 0A1h, 0A4h, 0A9h, 0ADh, 0B0h, 0B5h, 0B9h, 0BCh, 0Ch, 0F2h, 06h, 73h, 71h, 34h, 32h
	db	1Fh, 16h, 1Fh, 1Fh, 00h, 0Fh, 00h, 0Fh, 00h, 09h, 00h, 09h, 0FFh, 0FEh, 0FEh, 0FAh
	db	12h, 80h, 95h, 80h, 23h, 19h, 01h, 01h, 80h, 06h, 1Eh, 19h, 00h, 00h, 0EFh, 00h
	db	8Dh, 10h, 0F2h, 38h, 12h, 12h, 13h, 13h, 5Fh, 1Fh, 1Fh, 9Fh, 0Ah, 05h, 05h, 02h
	db	0Bh, 05h, 04h, 01h, 9Ch, 9Ch, 8Dh, 9Dh, 12h, 12h, 12h, 80h, 52h, 19h, 01h, 01h
	db	0A0h, 06h, 46h, 19h, 00h, 00h, 0EFh, 00h, 8Bh, 04h, 0Dh, 8Bh, 09h, 0Eh, 92h, 0F1h
	db	24h, 0F2h, 3Bh, 38h, 53h, 21h, 31h, 4Eh, 1Fh, 1Fh, 9Fh, 8Ah, 89h, 8Ah, 91h, 06h
	db	06h, 06h, 04h, 75h, 96h, 76h, 16h, 12h, 12h, 12h, 80h, 81h, 19h, 01h, 01h, 80h
	db	06h, 75h, 19h, 00h, 00h, 0EFh, 00h, 8Dh, 04h, 0F7h, 00h, 05h, 77h, 19h, 8Ah, 08h
	db	0F2h, 29h, 06h, 57h, 03h, 02h, 5Fh, 1Fh, 1Fh, 9Fh, 8Ah, 89h, 8Ah, 91h, 06h, 06h
	db	06h, 04h, 76h, 96h, 76h, 16h, 12h, 12h, 12h, 80h
SFXPtrTableZ80_End:

; ---------------------------------------------------------------------------
; Unused values
; ---------------------------------------------------------------------------
	db	16h, 12h, 12h, 12h, 80h, 75h
	db	96h, 76h, 16h, 12h, 12h, 12h, 80h, 0F6h, 18h, 01h, 01h, 80h, 06h, 0EAh, 18h, 00h
	db	00h, 0EFh, 00h, 8Dh, 04h, 0F7h, 00h, 05h, 0ECh, 18h, 8Ah, 08h, 0F2h, 29h, 06h, 57h
	db	03h, 02h, 5Fh, 1Fh, 1Fh, 9Fh, 8Ah, 89h, 8Ah, 91h, 06h, 06h, 06h, 04h, 76h, 96h
	db	76h, 16h, 12h, 12h, 12h, 80h, 00h
; ---------------------------------------------------------------------------
AllSFXPtrTableZ80_End: