	cpu Z80
	listing off

SoundDriver_Start:
	di
	di
	im	1		; interrupt mode 1 (for zVblank)
	jr	InitDriver
	nop
	nop
	
WaitForYM:
	ld	a, (4000h)
	bit	7, a
	jr	nz, WaitForYM
	ret

WriteFMMain:
	bit	7, (ix+1)
	ret	nz
	jp	WriteFMIorII

JmpTo_WriteFMI:	
	jp	WriteFMI
	nop
	nop
	nop
	nop
	nop

GetListOffset:
	ld	hl, (1C02h)
	
JmpTo_GetPtrListOfs:
	ld	b, 0
	jp	GetPtrListOfs

ReadPtrTable:	
	ld	c, a
	ld	b, 0
	add	hl, bc
	add	hl, bc
	nop
	nop
	nop

ReadPtrFromHL:	
	ld	a, (hl)
	inc	hl
	ld	h, (hl)
	ld	l, a
	ret
	nop
	nop
	nop
	
zVBlank:
	push	af
	push 	bc		; save some registers
	push 	de
	push 	hl
	ld	hl, 1FFFh	; HL = Skip Update counter
	ld	a, (hl)
	or	a			; Counter == 0?
	jr	z, +		; yes -	update sound
	dec	(hl)		; no - decrement
	jr	++			; and don't do anything else
+
	ld	a, (1C07h)	; 1C07 - Timing	Mode
	or	a
	call	z, UpdateAll	; update only when 1C07	== 00
+
	pop	hl		; restore the registers
	pop	de
	pop	bc
	pop	af
	ei
	ret
	
InitDriver:
	ld	sp, 1FFDh
	ld	a, 3
	ld	(1FFFh), a	; make it skip 3 updates
	
-
	ei			; enable V blanking
	ld	a, (1FFFh)
	or	a		; wait for 3 V blankings
	jp	nz, -

	call	StopAllSound
	call	SetupBank
	call	RefreshTimerA
	call	RefreshTimerB

zloc_6F:
	ei
	call	DoSoundQueue
	ld	a, (1C07h)	; Timing Mode
	or	a
	jr	z, zloc_6F	; Timing Mode 0, update on zVBlank
	di
	jp	p, TimerB_Update	; Timing Mode 40 - Update on YM2612 Timer A

; TimerAB_Update		Timing Mode 80
	call	DoSoundQueue
	ld	a, (4000h)		; Music	Update on YM2612 Timer A
	and	3				; SFX Update on	YM2612 Timer B
	jr	z, zloc_6F		; none of the YM2612 Timers expired - jump back
	bit	1, a
	jr	z, zloc_9B		; Timer	B not yet expired - try	Timer A
	call	RefreshTimerB	; Timer	B expired - update SFX
	ld	hl, zloc_9B		; make it jump to the Timer A update check when returning from UpdateSFXTracks
	push	hl			; returning from UpdateSFXTracks
	call	DoPause
	call	PlaySoundID
	jp	UpdateSFXTracks
	
zloc_9B:
	ld	a, (4000h)
	bit	0, a
	jr	z, zloc_6F
	call	RefreshTimerA	; Timer	A expires - update Music
	call	UpdateAll
	jr	zloc_6F

TimerB_Update:
	ld	a, (4000h)
	bit	1, a
	jr	z, zloc_6F
	call	RefreshTimerB	; update everything when Timer B expires
	call	UpdateAll
	jr	zloc_6F
	
RefreshTimerA:
	ld	hl, (1C04h)
	ld	a, l
	and	3
	ld	c, a
	ld	a, 25h
	rst	JmpTo_WriteFMI	; write	Timer A	LSB
	srl	h
	rr	l
	srl	h
	rr	l
	ld	c, l
	ld	a, 24h
	rst	JmpTo_WriteFMI	; write	Timer A	MSB
	ld	a, 1Fh
	jr	ResetYMTimer

	
RefreshTimerB:
	ld	a, (1C06h)
	ld	c, a
	ld	a, 26h
	rst	JmpTo_WriteFMI	; write	Timer B
	ld	a, 2Fh
	
ResetYMTimer:
	ld	hl, 1C12h
	or	(hl)
	ld	c, a
	ld	a, 27h
	rst	JmpTo_WriteFMI	; Reset	Timer
	ret
	
UpdateAll:
	call	DoPause
	call	DoTempo
	call	DoFading
	call	PlaySoundID
	ld	a, (1C07h)		; Timing Mode
	or	a
	call	p, UpdateSFXTracks	; 1C07 < 80 - update SFX (SFX use Music Timing)
	xor	a
	ld	(1C19h), a	; 00 - Music Mode
	ld	ix, 1C40h	; 1C40 - Music Track Drum
	bit	7, (ix+0)
	call	nz, DrumUpdateTrack
	ld	b, 9			; 9 Music Tracks (10 minus Drum	Track)
	ld	ix, 1C70h		; 1C70 - Music Track FM1
	jr	TrkUpdateLoop
	
UpdateSFXTracks:
	ld	a, 1
	ld	(1C19h), a		; 01 - SFX Mode
	ld	ix, 1E80h		; 1E80 - SFX Tracks
	ld	b, 6			; 6 SFX	tracks
	call	TrkUpdateLoop
	ld	a, 80h
	ld	(1C19h), a		; 80 - Special SFX Mode
	ld	b, 2			; 2 special SFX	tracks
	ld	ix, 1E20h		; 1E20 - Special SFX Tracks
	
TrkUpdateLoop:
	push	bc
	bit	7, (ix+0)		; 'in use' flag set?
	call	nz, UpdateTrack
	ld	de, 30h			; next track
	add	ix, de
	pop	bc
	djnz	TrkUpdateLoop
	ret
	
UpdateTrack:
	bit	7, (ix+1)
	jp	nz, UpdatePSGTrk
	call	TrackTimeout
	jr	nz, +
	call	TrkUpdate_Proc
	bit	4, (ix+0)
	ret	nz
	call	PrepareModulat
	call	DoPitchSlide
	call	DoModulation
	call	SendFMFreq
	jp	DoNoteOn
	
+
	call	ExecPanAnim
	bit	4, (ix+0)
	ret	nz
	call	DoFMVolEnv
	ld	a, (ix+1Eh)
	or	a
	jr	z, +
	dec	(ix+1Eh)
	jp	z, SendNoteOff
	
+
	call	DoPitchSlide
	bit	6, (ix+0)
	ret	nz
	call	DoModulation
	
SendFMFreq:
	bit	2, (ix+0)
	ret	nz
	bit	0, (ix+0)
	jp	nz, +

-	
	ld	a, 0A4h
	ld	c, h
	rst	WriteFMMain
	ld	a, 0A0h
	ld	c, l
	rst	WriteFMMain
	ret
	
+
	ld	a, (ix+1)
	cp	2
	jr	nz, -

	call	GetFM3FreqPtr
	exx
	ld	hl, SpcFM3Regs
	ld	b, 4

-
	ld	a, (hl)
	push	af
	inc	hl
	exx
	ex	de, hl
	ld	c, (hl)
	inc	hl
	ld	b, (hl)
	inc	hl
	ex	de, hl
	ld	l, (ix+0Dh)
	ld	h, (ix+0Eh)
	add	hl, bc
	pop af
	push	af
	ld	c, h
	rst	JmpTo_WriteFMI
	pop	af
	sub	4
	ld	c, l
	rst	JmpTo_WriteFMI
	exx
	djnz	-
	
	exx
	ret

; --------------------------------	
SpcFM3Regs:
	db	0ADh, 0AEh, 0ACh, 0A6h
; --------------------------------

GetFM3FreqPtr:
	ld	de, 1C2Ah
	ld	a, (1C19h)
	or	a
	ret	z			; Music	Mode (00) - 1C2A
	ld	de, 1C1Ah
	ret	p			; Special SFX Mode (80)	- 1C1A
	ld	de, 1C22h
	ret				; SFX Mode (01)	- 1C2
	
TrkUpdate_Proc:
	ld	e, (ix+3)
	ld	d, (ix+4)
	res	1, (ix+0)
	res	4, (ix+0)
	
zloc_1E4:
	ld	a, (de)
	inc de
	cp	0E0h
	jp	nc, cfHandler
	ex	af, af'
	call	DoNoteOff
	call	DoPanAnimation
	ex	af, af'
	bit	3, (ix+0)
	jp	nz, DoRawFreqMode
	or	a
	jp	p, SetDuration		; 00-7F	- Delay
	sub	81h
	jp	p, GetNote		; 81-DF	- Note
	call	SetRest		; 80 - Rest
	jr	zloc_236
	
GetNote:
	add	a, (ix+5)
	ld	hl, PSGFreqs
	push	af
	rst	ReadPtrTable
	pop	af
	bit	7, (ix+1)
	jr	nz, zloc_230
	push	de
	ld	d, 8
	ld	e, 0Ch
	ex	af, af'
	xor	a

-
	ex	af, af'
	sub	e
	jr	c, +
	ex	af, af'
	add	a, d
	jr	-

	ex	af, af'
+
	add	a, e
	ld	hl, FMFreqs
	rst	ReadPtrTable
	ex	af, af'
	or	h
	ld	h, a
	pop	de
	
zloc_230:
	ld	(ix+0Dh), l
	ld	(ix+0Eh), h
	
zloc_236:
	bit	5, (ix+0)
	jr	nz, +
	ld	a, (de)
	or	a
	jp	p, zloc_275
	ld	a, (ix+0Ch)
	ld	(ix+0Bh), a
	jr	zloc_27C
	
+
	ld	a, (de)
	inc	de
	ld	(ix+10h), a
	jr	zloc_274
	
DoRawFreqMode:
	ld	h, a
	ld	a, (de)
	inc	de
	ld	l, a
	or	h
	jr	z, ++
	ld	a, (ix+5)
	ld	b, 0
	or	a
	jp	p, +

	dec	b
+
	ld	c, a
	add	hl, bc
+
	ld	(ix+0Dh), l
	ld	(ix+0Eh), h
	bit	5, (ix+0)
	jr	z, zloc_274
	ld	a, (de)
	inc	de
	ld	(ix+10h), a
	
zloc_274:
	ld	a, (de)
	
zloc_275:
	inc	de
	
SetDuration:
	call	TickMultiplier
	ld	(ix+0Ch), a
	
zloc_27C:
	ld	(ix+3), e
	ld	(ix+4), d
	ld	a, (ix+0Ch)
	ld	(ix+0Bh), a
	bit	1, (ix+0)
	ret	nz
	xor	a
	ld	(ix+25h), a
	ld	(ix+22h), a
	ld	a, (ix+1Fh)
	ld	(ix+1Eh), a
	ld	(ix+17h), a
	ret
	
TickMultiplier:
	ld	b, (ix+2)
	dec	b
	ret	z
	ld	c, a

-
	add	a, c
	djnz	-
	ret
	
DoPanAnimation:
	ld	a, (ix+11h)
	dec	a
	ret	m
	jr	nz, zloc_2EA
	bit	1, (ix+0)
	ret	nz

zloc_2B4:	
	dec	(ix+16h)
	ret	nz
	exx
	ld	a, (ix+15h)
	ld	(ix+16h), a
	ld	a, (ix+12h)
	ld	hl, PanAniPtrList
	rst	ReadPtrTable
	ld	e, (ix+13h)
	inc	(ix+13h)
	ld	a, (ix+14h)
	dec	a
	cp	e
	jr	nz, +
	dec	(ix+13h)
	ld	a, (ix+11h)
	cp	2
	jr	z, +
	ld	(ix+13h), 0
	
+
	ld	d, 0
	add	hl, de
	ex	de, hl
	call	cfE0_Pan
	exx
	ret
	
zloc_2EA:
	xor	a
	ld	(ix+13h), a
	
ExecPanAnim:
	ld	a, (ix+11h)
	sub	2
	ret	m
	jr	zloc_2B4

; ====================================	
PanAniPtrList:
	dw	zloc_2FE
	dw	zloc_2FF
	dw	zloc_300
	dw	zloc_301
	
zloc_2FE:	db	0C0h
zloc_2FF:	db	80h
zloc_300:	db	0C0h
zloc_301:	db	40h, 80h, 0C0h
; ====================================

TrackTimeout:
	ld	a, (ix+0Bh)
	dec	a
	ld	(ix+0Bh), a
	ret
	
DoFMVolEnv:
	ld	a, (ix+18h)
	or	a
	ret	z
	ret	m
	dec	a
	ld	c, 0Ah
	rst	GetListOffset	; get List 5 (PSG/Volume envelopes)
	rst	ReadPtrTable
	call	DoPSGVolEnv
	ld	h, (ix+1Dh)
	ld	l, (ix+1Ch)
	ld	de, Volume_Ops
	ld	b, 4
	ld	c, (ix+19h)
	
-
	push	af
	sra	c
	push	bc
	jr	nc, +
	add	a, (hl)
	and	7Fh
	ld	c, a
	ld	a, (de)
	rst	WriteFMMain
+
	pop	bc
	inc	de
	inc	hl
	pop	af
	djnz	-
	ret
	
PrepareModulat:
	bit	7, (ix+7)
	ret	z
	bit	1, (ix+0)
	ret	nz
	ld	e, (ix+20h)
	ld	d, (ix+21h)
	push	ix
	pop	hl
	ld	b, 0
	ld	c, 24h
	add	hl, bc
	ex	de, hl
	ldi
	ldi
	ldi
	ld	a, (hl)
	srl	a
	ld	(de), a
	xor	a
	ld	(ix+22h), a
	ld	(ix+23h), a
	ret
	
DoModulation:
	ld	a, (ix+7)
	or	a
	ret	z			; ModType 00 ->	return (modulation off)
	cp	80h
	jr	nz, DoModEnv	; ModType != 80	-> jump
	dec	(ix+24h)		; ModType 80 ->	manual modulation parameters
	ret	nz
	inc	(ix+24h)
	push	hl
	ld	l, (ix+22h)
	ld	h, (ix+23h)
	dec	(ix+25h)
	jr	nz, zloc_3A2
	ld	e, (ix+20h)
	ld	d, (ix+21h)
	push	de
	pop	iy
	ld	a, (iy+1)
	ld	(ix+25h), a
	ld	a, (ix+26h)
	ld	c, a
	and	80h
	rlca
	neg
	ld	b, a
	add	hl, bc
	ld	(ix+22h), l
	ld	(ix+23h), h
	
zloc_3A2:
	pop	bc
	add	hl, bc
	dec	(ix+27h)
	ret	nz
	ld	a, (iy+3)
	ld	(ix+27h), a
	ld	a, (ix+26h)
	neg
	ld	(ix+26h), a
	ret
	
DoModEnv:
	dec	a
	ex	de, hl
	ld	c, 8
	rst	GetListOffset	; get List 4 (Modulation Pointers)
	rst	ReadPtrTable
	jr	zloc_3C2
	
zloc_3BF:
	ld	(ix+25h), a
	
zloc_3C2:
	push	hl
	ld	c, (ix+25h)
	call	GetEnvData	; BC = HL (base) + BC (index), A = (BC)
	pop	hl
	bit	7, a
	jp	z, ModEnv_Positive
	cp	82h
	jr	z, ModEnv_Jump2Idx		; 82	xx - jump to byte xx
	cp	80h
	jr	z, ModEnv_Reset		; 80 - loop back to beginning
	cp	84h
	jr	z, ModEnv_ChgMult	; 84 - change	Modulation Multipler
	ld	h, 0FFh				; make HL negative (FFxx)
	jr	nc, ModEnv_Next
	set	6, (ix+0)
	pop	hl
	ret
	
ModEnv_Jump2Idx:
	inc	bc
	ld	a, (bc)
	jr	zloc_3BF
	
ModEnv_Reset:
	xor	a
	jr	zloc_3BF
	
ModEnv_ChgMult:
	inc	bc
	ld	a, (bc)
	add	a, (ix+22h)
	ld	(ix+22h), a
	inc	(ix+25h)
	inc	(ix+25h)
	jr	zloc_3C2
	
ModEnv_Positive:
	ld	h, 0		; make HL positive (00xx)
	
ModEnv_Next:
	ld	l, a
	ld	b, (ix+22h)
	inc	b
	ex	de, hl

-
	add	hl, de
	djnz	-
	inc	(ix+25h)
	ret
	
DoNoteOn:
	ld	a, (ix+0Dh)
	or	(ix+0Eh)
	ret	z
	ld	a, (ix+0)
	and	6
	ret	nz
	ld	a, (ix+1)
	or	0F0h
	ld	c, a
	ld	a, 28h
	rst	JmpTo_WriteFMI
	ret
	

DoNoteOff:
	ld	a, (ix+0)
	and	6
	ret	nz
	
SendNoteOff:
	ld	c, (ix+1)
	bit	7, c
	ret	nz
	
FMNoteOff:
	ld	a, 28h
	rst	JmpTo_WriteFMI
	ret
	
DoPitchSlide:
	ld	b, 0
	ld	a, (ix+10h)
	or	a
	jp	p, +
	dec	b
+
	ld	h, (ix+0Eh)
	ld	l, (ix+0Dh)
	ld	c, a
	add	hl, bc
	bit	7, (ix+1)
	jr	nz, zloc_46C
	ex	de, hl
	ld	a, 7
	and	d
	ld	b, a
	ld	c, e
	or	a
	ld	hl, 283h
	sbc	hl, bc
	jr	c, zloc_45E
	ld	hl, -57Bh
	add	hl, de
	jr	zloc_46C
	
zloc_45E:
	or	a
	ld	hl, 508h
	sbc	hl, bc
	jr	nc, zloc_46B
	ld	hl, 57Ch
	add	hl, de
	ex	de, hl
	
zloc_46B:
	ex	de, hl
	
zloc_46C:
	bit	5, (ix+0)
	ret	z
	ld	(ix+0Eh), h
	ld	(ix+0Dh), l
	ret
	
GetPtrListOfs:
	add	hl, bc
	ex	af, af'
	rst	ReadPtrFromHL
	ex	af, af'
	ret
	
GetEnvData:
	ld	b, 0
	add	hl, bc
	ld	c, l
	ld	b, h
	ld	a, (bc)
	ret

GetFMInsPtr:	
	ld	hl, (1C37h)
	ld	a, (1C19h)
	or	a
	jr	z, JumpToInsData	; Mode	00 (Music Mode)	- jump
	ld	l, (ix+2Ah)			; load SFX track Instrument Pointer (Trk+2A/2B)
	ld	h, (ix+2Bh)

JumpToInsData:
	xor	a
	or	b
	jr	z, +
	ld	de, 19h
	
-
	add	hl, de
	djnz	-
	
+
	ret
	
WriteFMIorII:
	bit	2, (ix+1)			; is FM	4-6?
	jr	nz, WriteFMIIPart
	bit	2, (ix+0)
	ret	nz
	add	a, (ix+1)			; add Channel Bits to register value
	
WriteFMI:
	ld	(4000h), a
	rst	WaitForYM
	ld	a, c
	ld	(4001h), a
	ret
	
WriteFMIIPart:
	bit	2, (ix+0)
	ret	nz
	add	a, (ix+1)
	sub	4
	
WriteFMII:
	ld	(4002h), a
	rst	WaitForYM
	ld	a, c
	ld	(4003h), a
	ret

; ====================================	
FMInsOperators:
	db	0B0h
	db	30h, 38h, 34h, 3Ch
	db	50h, 58h, 54h, 5Ch
	db	60h, 68h, 64h, 6Ch
	db	70h, 78h, 74h, 7Ch
	db	80h, 88h, 84h, 8Ch
	
Volume_Ops:
	db	40h, 48h, 44h, 4Ch
	
SSGEG_Ops:
	db	90h, 98h, 94h, 9Ch
; ====================================

SendFMIns:
	ld	de, FMInsOperators
	ld	c, (ix+0Ah)
	ld	a, 0B4h
	rst	WriteFMMain
	call	WriteInsReg
	ld	(ix+1Bh), a
	ld	b, 14h

-
	call	WriteInsReg
	djnz	-
	ld	(ix+1Ch), l
	ld	(ix+1Dh), h
	jp	RefreshVolume
	
WriteInsReg:
	ld	a, (de)
	inc	de
	ld	c, (hl)
	inc	hl
	rst	WriteFMMain
	ret
	
PlaySoundID:
	ld	a, (1C09h)
	
PlaySnd_JumpIn:
	bit	7, a
	jp	z, StopAllSound
	cp	0B0h
	jp	c, PlayMusic	; 80-AF	- Music
	cp	0DAh
	jp	c, PlaySFX		; B0-D9	- SFX
	cp	0E0h
	jp	c, PlaySpcSFX	; DA-DF	- Special SFX
	cp	0F9h
	jp	nc, StopAllSound	; F9-FF - Stop	All
	
PlaySnd_Command:		; E0-F8	- Special Commands
	sub	0E0h
	push	af
	xor	a
	ld	(1C18h), a		; reset	Current	Sound Priority
	pop	af
	ld	hl, CmdPtrTable
	rst	ReadPtrTable
	jp	(hl)
	
; ==============================
CmdPtrTable:
	dw	FadeOutMusic
	dw	StopAllSound
	dw	SilencePSG
	dw	StopSpcSFX
; ==============================

StopSpcSFX:
	ld	ix, 1E20h		; 1E20 - Special SFX tracks
	ld	b, 2
	ld	a, 80h
	ld	(1C19h), a		; 80 - Special SFX Mode

-
	push	bc
	bit	7, (ix+0)		; Track	in use?
	call	nz, zloc_557	; yes -	stop it
	ld	de, 30h
	add	ix, de			; next track
	pop	bc				; restore BC (C	has the	remaining number of tracks)
	djnz	-
	ret

zloc_557:
	push	hl			; push 4 bytes onto the	stack to make StopTrack
	push	hl			; return to the	correct	routine.
	jp	cfF2_StopTrk
	
PlayMusic:
	sub	81h				; Sound	ID -> Music Index
	ret	m				; was 80 (dummy	command) - return
	push	af
	call	StopAllSound
	pop	af
	ld	c, 4
	rst	GetListOffset	; get List 2 (Music Pointers)
	rst	ReadPtrTable
	push	hl
	push	hl
	rst	ReadPtrFromHL
	ld	(1C37h), hl		; save Instrument Pointer
	pop	hl
	pop	iy
	ld	a, (iy+5)		; read Tempo
	ld	(1C13h), a		; Tempo	work counter
	ld	(1C14h), a		; Tempo	Reset value
	ld	de, 6
	add	hl, de
	ld	(1C33h), hl
	ld	hl, FMInitBytes
	ld	(1C35h), hl
	ld	de, 1C40h	; 1C40 - Music Track RAM
	ld	b, (iy+2)	; load FM tracks
	ld	a, (iy+4)	; load Tick Multiplier
	
-
	push	bc
	ld	hl, (1C35h)
	ldi
	ldi
	ld	(de), a
	inc	de
	ld	(1C35h), hl
	ld	hl, (1C33h)
	ldi
	ldi
	ldi
	ldi
	ld	(1C33h), hl
	call	FinishFMTrkInit
	pop	bc
	djnz	-
	
	ld	a, (iy+3)			; load PSG tracks
	or	a
	jp	z, ClearSoundID		; no PSG tracks	- skip
	ld	b, a
	ld	hl, PSGInitBytes
	ld	(1C35h), hl
	ld	de, 1D90h			; 1D90 - Music Track PSG1
	ld	a, (iy+4)			; load Tick Multiplier
	
zloc_5C5:
	push	bc		; same as FM init loop ...
	ld	hl, (1C35h)
	ldi
	ldi
	ld	(de), a
	inc	de
	ld	(1C35h), hl
	ld	hl, (1C33h)
	ld	bc, 6
	ldir
	ld	(1C33h), hl
	call	FinishTrkInit
	pop	bc
	djnz	zloc_5C5
	
ClearSoundID:
	ld	a, 80h
	ld	(1C09h), a
	ret

; ===========================	
FMInitBytes:
	db	80h, 2
	db	80h, 0
	db	80h, 1
	db	80h, 4
	db	80h, 5
	db	80h, 6
	db	80h, 2
	
PSGInitBytes:
	db	80h, 80h
	db	80h, 0A0h
	db	80h, 0C0h
; ===========================

PlaySpcSFX:
	sub	0DAh			; Sound	ID -> SFX Index
	ex	af, af'
	xor	a
	ld	(1C18h), a	; reset	Current	Sound Priority
	ld	a, 80h
	ld	c, 2
	jr	zloc_610
	
PlaySFX:
	sub	0B0h
	ex	af, af'
	xor	a
	ld	c, 6
	
zloc_610:
	ld	(1C19h), a
	ex	af, af'
	rst	GetListOffset
	rst	ReadPtrTable
	push	hl
	rst	ReadPtrFromHL
	ld	(1C39h), hl
	xor	a
	ld	(1C15h), a
	pop	hl
	push	hl
	pop	iy
	ld	a, (iy+2)
	ld	(1C3Bh), a
	ld	de, 4
	add	hl, de
	ld	b, (iy+3)
	
zloc_630:
	push	bc
	push	hl
	inc	hl
	ld	c, (hl)
	call	GetSFXChnPtrs
	set	2, (hl)
	push	ix
	ld	a, (1C19h)
	or	a
	jr	z, zloc_644
	pop	hl
	push	iy
	
zloc_644:
	pop	de
	pop	hl
	ldi
	ld	a, (de)
	cp	2
	call	z, ResetSpcFM3Mode
	ldi
	ld	a, (1C3Bh)
	ld	(de), a
	inc	de
	ldi
	ldi
	ldi
	ldi
	call	FinishFMTrkInit
	bit	7, (ix+0)
	jr	z, +
	ld	a, (ix+1)
	cp	(iy+1)
	jr	nz, +
	set	2, (iy+0)
+
	push	hl
	ld	hl, (1C39h)
	ld	a, (1C19h)
	or	a
	jr	z, +
	push	iy
	pop	ix
+
	ld	(ix+2Ah), l
	ld	(ix+2Bh), h
	call	DoNoteOff
	call	DisableSSGEG
	pop	hl
	pop	bc
	djnz	zloc_630
	jp	ClearSoundID
	
GetSFXChnPtrs:
	bit	7, c
	jr	nz, zloc_69C
	ld	a, c
	sub	2
	jr	zloc_6B2
	
zloc_69C:
	ld	a, 1Fh
	call	SilencePSGChn
	ld	a, 0FFh
	ld	(7F11h), a
	ld	a, c
	srl	a
	srl	a
	srl	a
	srl	a
	srl	a
	inc	a
	
zloc_6B2:
	ld	(1C32h), a
	push	af
	ld	hl, SFXChnPtrs
	rst	ReadPtrTable
	push	hl
	pop	ix		; IX - SFX Track
	pop	af
	push	af
	ld	hl, SpcSFXChnPtrs
	rst	ReadPtrTable
	push	hl
	pop	iy		; IY - Special SFX Track
	pop	af
	ld	hl, BGMChnPtrs
	rst	ReadPtrTable	; HL - Music Track
	ret
	
FinishFMTrkInit:
	ex	af, af'
	xor	a
	ld	(de), a
	inc	de
	ld	(de), a
	inc	de
	ex	af, af'
	
FinishTrkInit:
	ex	de, hl
	ld	(hl), 30h	; set GoSub Stack Pointer (30 =	track size)
	inc	hl
	ld	(hl), 0C0h	; set Pan to L/R
	inc	hl
	ld	(hl), 1		; set Note Timeout to 1	(next frame)
	ld	b, 24h

-
	inc	hl
	ld	(hl), 0		; fill rest of the track with 00s
	djnz	-
	inc	hl
	ex	de, hl
	ret

; ========================================	
SpcSFXChnPtrs:
	dw	1E20h
	dw	1E20h
	dw	1E20h
	dw	1E20h
	dw	1E50h
	dw	1E20h
	dw	1E20h
	dw	1E50h
	
SFXChnPtrs:
	dw	1E80h
	dw	1EB0h
	dw	1EB0h
	dw	1EB0h
	dw	1EE0h
	dw	1F10h
	dw	1F40h
	dw	1F70h
	
BGMChnPtrs:
	dw	1D60h
	dw	1D00h
	dw	1D00h
	dw	1D00h
	dw	1D30h
	dw	1D90h
	dw	1DC0h
	dw	1DF0h
; ========================================

SetupBank:
	ld	a, (1C01h)
	rlca
	ld	(6000h), a
	ld	b, 8
	ld	a, (1C00h)
	
-
	ld	(6000h), a
	rrca
	djnz	-
	ret
	
DoPause:
	ld	hl, 1C10h	; 1C10 = Pause Mode
	ld	a, (hl)
	or	a
	ret	z			; 00 = not paused
	jp	m, UnpauseMusic	; 80-FF	- request Unpause
	pop	de
	dec	a			; 01 - request Pause?
	ret	nz			; no, it's 02 - return
	ld	(hl), 2		; it's 01, so set it to 02 (Pause active)
	jp	SilenceAll
	
UnpauseMusic:
	xor	a
	ld	(hl), a
	ld	a, (1C0Dh)
	or	a
	jp	nz, StopAllSound
	ld	ix, 1C70h		; IX = Track of	FM 1
	ld	b, 6
	
zloc_749:
	ld	a, (1C11h)
	or	a
	jr	nz, zloc_755
	bit	7, (ix+0)
	jr	z, zloc_75B
	
zloc_755:
	ld	c, (ix+0Ah)
	ld	a, 0B4h
	rst	WriteFMMain
	
zloc_75B:
	ld	de, 30h
	add	ix, de
	djnz	zloc_749
	ld	ix, 1E20h		; IX = Special SFX Track 1
	ld	b, 8
	
zloc_768:
	bit	7, (ix+0)
	jr	z, zloc_77A
	bit	7, (ix+1)
	jr	nz, zloc_77A
	ld	c, (ix+0Ah)
	ld	a, 0B4h
	rst	WriteFMMain
	
zloc_77A:
	ld	de, 30h
	add	ix, de
	djnz	zloc_768
	ret
	
FadeOutMusic:
	ld	a, 28h		; Number of fading steps
	ld	(1C0Dh), a
	ld	a, 2		; Frames per Step
	ld	(1C0Fh), a
	ld	(1C0Eh), a
	
StopDrumPSG:
	xor	a
	ld	(1C40h), a	; stop Drum Track
	ld	(1D60h), a	; stop FM6 Track
	ld	(1DF0h), a	; stop PSG3 Track
	ld	(1D90h), a	; stop PSG1 Track
	ld	(1DC0h), a	; stop PSG2 Track
	call	SilencePSG
	jp	ClearSoundID
	
DoFading:
	ld	hl, 1C0Dh
	ld	a, (hl)		; load remaining Fading	Steps
	or	a
	ret	z			; reached 0 - return
	call	m, StopDrumPSG	; 80+ -	mute Drum and PSG channels
	res	7, (hl)
	ld	a, (1C0Fh)		; 1C0F - Timeout Counter
	dec	a
	jr	z, ApplyFading	; reached 0 - apply fading
	ld	(1C0Fh), a		; else just write back
	ret

ApplyFading:
	ld	a, (1C0Eh)
	ld	(1C0Fh), a		; 1C0F (Counter) = 1C0E	(Initial)
	ld	a, (1C0Dh)
	dec	a
	ld	(1C0Dh), a
	jr	z, StopAllSound
	ld	ix, 1C40h		; 1C40 - Music Track RAM
	ld	b, 6
	
zloc_7CF:
	inc	(ix+6)
	jp	p, zloc_7DA
	dec	(ix+6)
	jr	zloc_7E9
	
zloc_7DA:
	bit	7, (ix+0)
	jr	z, zloc_7E9
	bit	2, (ix+0)
	jr	nz, zloc_7E9
	call	RefreshVolume
	
zloc_7E9:
	ld	de, 30h
	add	ix, de
	djnz	zloc_7CF
	ret
	
StopAllSound:
	ld	hl, 1C09h
	ld	de, 1C0Ah
	ld	bc, 396h
	ld	(hl), 0
	ldir				; clear	complete sound RAM (music + SFX)
	ld	ix, FMInitBytes
	ld	b, 6			; 6 FM channels
	
-
	push	bc
	call	SilenceFMChn
	call	DisableSSGEG
	inc	ix
	inc	ix
	pop	bc
	djnz	-
	
	ld	b, 7		; dead instruction?
	xor	a
	ld	(1C0Dh), a	; clear	Fading Step Counter
	call	SilencePSG
	
ResetSpcFM3Mode:
	ld	a, 0Fh
	ld	(1C12h), a
	ld	c, a
	ld	a, 27h
	rst	JmpTo_WriteFMI
	jp	ClearSoundID
	
DisableSSGEG:
	ld	a, 90h
	ld	c, 0
	jp	SendAllFMOps
	
SilenceAll:
	call	SilencePSG
	push	bc
	push	af
	ld	b, 3
	ld	a, 0B4h
	ld	c, 0
	
-
	push	af
	rst	JmpTo_WriteFMI
	pop	af
	inc	a
	djnz	-

	ld	b, 3
	ld	a, 0B4h
	
-
	push	af
	call	WriteFMII
	pop	af
	inc	a
	djnz	-
	ld	c, 0
	ld	b, 7
	ld	a, 28h

-
	push	af
	rst	JmpTo_WriteFMI
	inc	c
	pop	af
	djnz	-
	
	pop	af
	pop	bc
	
SilencePSG:
	push	hl
	push	bc
	ld	hl, PSGMuteVals
	ld	b, 4
	
-
	ld	a, (hl)
	ld	(7F11h), a
	inc	hl
	djnz	-
	pop	bc
	pop	hl
	jp	ClearSoundID

; ===============================	
PSGMuteVals:
	db	9Fh, 0BFh, 0DFh, 0FFh
; ===============================

DoTempo:
	ld	hl, 1C13h	; 1C13 = Tempo Timeout
	ld	a, (hl)
	or	a
	ret	z			; Tempo	00 = never delayed
	dec	(hl)		; subtract 1
	ret	nz			; reached 00 - continue	and delay all tracks
	ld	a,(1C14h)	; load initial Tempo (1C14)
	ld	(hl), a
	ld	hl, 1C4Bh	; 1C40 (DAC Track) + 0B	(Note Timeout)
	ld	de, 30h
	ld	b, 0Ah		; 10 Music Tracks
	
-
	inc	(hl)		; delay	by 1 frame
	add	hl, de		; next track
	djnz	-
	ret
	
DoSoundQueue:
	ld	a, r
	ld	(1C17h), a
	ld	de, 1C0Ah
	call	DoOneSndQueue
	ld	de, 1C0Bh
	call	DoOneSndQueue
	ld	de, 1C0Ch
	
DoOneSndQueue:
	ld	a, (de)
	bit	7, a
	ret	z
	cp	80h
	ret	z
	sub	81h
	ld	hl, (1C02h)
	ld	c, 0
	rst	GetListOffset	; get List 0 (Sound Priorities)
	ld	c, a
	ld	b, 0
	add	hl, bc
	ld	a, (1C18h)		; 1C18 - Current Sound Priority
	cp	(hl)
	jr	z, +
	jr	nc, zloc_8C0
+
	ld	a, (de)
	ld	(1C09h), a
	ld	a, (hl)
	ld	(1C18h), a		; set new Sound	Priority
	
zloc_8C0:
	xor	a
	ld	(de), a
	ret
	
SilenceFMChn:
	call	SetMaxRelRate
	ld	a, 40h
	ld	c, 7Fh
	call	SendAllFMOps
	ld	c, (ix+1)
	jp	FMNoteOff
	
SetMaxRelRate:
	ld	a, 80h
	ld	c, 0FFh
	
SendAllFMOps:
	ld	b, 4
	
-
	push	af
	rst	WriteFMMain
	pop	af
	add	a, 4
	djnz	-
	ret

; =================================================================================	
PSGFreqs:
	dw  356h, 326h,	2F9h, 2CEh, 2A5h, 280h,	25Ch, 23Ah, 21Ah, 1FBh,	1DFh, 1C4h
	dw  1ABh, 193h,	17Dh, 167h, 153h, 140h,	12Eh, 11Dh, 10Dh, 0FEh,	0EFh, 0E2h
	dw  0D6h, 0C9h,	0BEh, 0B4h, 0A9h, 0A0h,	 97h,  8Fh,  87h,  7Fh,	 78h,  71h
	dw   6Bh,  65h,	 5Fh,  5Ah,  55h,  50h,	 4Bh,  47h,  43h,  40h,	 3Ch,  39h
	dw   36h,  33h,	 30h,  2Dh,  2Bh,  28h,	 26h,  24h,  22h,  20h,	 1Fh,  1Dh
	dw   1Bh,  1Ah,	 18h,  17h,  16h,  15h,	 13h,  12h,  11h
	
FMFreqs:
	dw  284h, 2ABh,	2D3h, 2FEh, 32Dh, 35Ch,	38Fh, 3C5h, 3FFh, 43Ch,	47Ch, 4C0h
; =================================================================================


DrumUpdateTrack:
	call	TrackTimeout
	call	z, DrumUpdate_Proc
	ret
	
DrumUpdate_Proc:
	ld	e, (ix+3)
	ld	d, (ix+4)
	
zloc_990:
	ld	a, (de)
	inc	de
	cp	0E0h
	jp	nc, cfHandler_Drum
	or	a
	jp	m, +
	dec	de
	ld	a, (ix+0Dh)
+
	ld	(ix+0Dh), a
	cp	80h
	jp	z, zloc_A21
	push	de
	ld	hl, 1D60h
	bit	2, (hl)
	jr	nz, zloc_9F3
	and	0Fh
	jr	z, zloc_9F3
	ex	af, af'
	call	DoNoteOff
	ex	af, af'
	ld	de, FMDrumInit
	ex	de, hl
	ldi
	ldi
	ldi
	dec	a
	ld	hl, FMDrumTrkList
	rst	ReadPtrTable
	ld	bc, 6
	ldir
	call	FinishTrkInit
	ld	hl, 1D65h
	ld	a, (ix+5)
	add	a, (hl)
	ld	(hl), a
	ld	a, (1D68h)
	ld	hl, FMDrumInsPtrs
	rst	ReadPtrTable
	ld	a, (1D66h)
	ld	e, (ix+6)
	push	de
	add	a, e
	ld	(ix+6), a
	call	SendFMIns
	pop	de
	ld	(ix+6), e
	call	ResetSpcFM3Mode
	
zloc_9F3:
	ld	hl, 1DF0h
	bit	2, (hl)
	jr	nz, zloc_A20
	ld	a, (ix+0Dh)
	and	70h
	jr	z, zloc_A20
	ld	de, PSGDrumInit
	ex	de, hl
	ldi
	ldi
	ldi
	srl	a
	srl	a
	srl	a
	srl	a
	dec	a
	ld	hl, PSGDrumTrkList
	rst	ReadPtrTable
	ld	bc, 6
	ldir
	call	FinishTrkInit
	
zloc_A20:
	pop	de
	
zloc_A21:
	ld	a, (de)
	inc	de
	or	a
	jp	p, SetDuration
	dec	de
	ld	a, (ix+0Ch)
	ld	(ix+0Bh), a
	jp	zloc_27C

; ===========================	
FMDrumInit:
	db	80h, 02h, 01h
	
PSGDrumInit:
	db	80h, 0C0h, 01h
; ===========================

cfHandler_Drum:
	ld	hl, cfReturn_Drum
	jp	zloc_B7C
	
cfReturn_Drum:
	inc	de
	jp	zloc_990

; ============================================	
PSGDrumTrkList:
	dw	PSGDrum90
	dw	PSGDrumA0

PSGDrum90:	
	db	4Bh, 0Ah, 00h, 04h, 00h, 01h
	db	0F3h, 0E7h, 0C2h, 08h, 0F2h
	
PSGDrumA0:
	db	56h, 0Ah, 00h, 06h, 00h, 02h
	db	0F3h, 0E7h, 0C5h, 08h, 0F2h
; ============================================

; ====================
FMDrumTrkList:
	dw	FMDrum81
	dw	FMDrum82
	dw	FMDrum83
	dw	FMDrum84
	dw	FMDrum85
	dw	FMDrum86
	dw	FMDrum87
	dw	FMDrum88
	dw	FMDrum89
	dw	FMDrum8A
; ====================

; ====================
FMDrumInsPtrs:
	dw	FMDrumIns00
	dw	FMDrumIns01
	dw	FMDrumIns02
	dw	FMDrumIns03
	dw	FMDrumIns04
	dw	FMDrumIns05
; ====================

; =======================================================================================
FMDrum81:
	db	81h, 0Ah, 00h, 0Ch, 01h
	db	00h, 0B9h, 10h, 0F2h
	
FMDrumIns00:
	db	3Eh, 60h, 30h, 30h, 30h, 19h, 1Fh, 1Fh, 1Fh, 15h, 11h, 11h
	db	0Ch, 10h, 0Ah, 06h, 09h, 4Fh, 5Fh, 0AFh, 8Fh, 00h, 82h, 83h, 80h
	
FMDrum82:
	db	0A3h, 0Ah, 00h
	db	0Ch, 01h, 00h, 0E0h, 80h, 0B6h, 0Ah, 0F2h
	
FMDrum83:
	db	0AEh, 0Ah, 00h, 0Ch, 01h, 00h, 0B3h, 0Ah
	db	0F2h
	
FMDrum84:
	db	0B7h, 0Ah, 00h, 0Ch, 01h, 00h, 0E0h, 40h, 0B0h, 0Ah, 0F2h
	
FMDrum87:
	db	0C2h, 0Ah, 00h, 0Ch
	db	01h, 00h, 0B2h, 0Ah, 0F2h
	
FMDrum85:
	db	0CBh, 0Ah, 00h, 02h, 01h, 01h, 89h, 08h, 0F2h
	
FMDrumIns01:
	db	72h, 33h
	db	30h, 32h, 31h, 1Eh, 1Bh, 1Ch, 15h, 16h, 12h, 17h, 10h, 10h, 18h, 1Eh, 14h, 4Fh
	db	5Fh, 4Fh, 4Fh, 08h, 00h, 10h, 80h
	
FMDrum86:
	db	0EDh, 0Ah, 00h, 04h, 01h, 02h, 0B0h, 16h, 0F2h
	
FMDrumIns02:
	db	72h, 9Eh, 5Bh, 42h, 22h, 96h, 96h, 9Eh, 96h, 16h, 18h, 16h, 18h, 10h, 17h, 11h
	db	18h, 4Fh, 5Fh, 4Fh, 4Fh, 00h, 00h, 10h, 80h
	
FMDrum88:
	db	0Fh, 0Bh, 00h, 0Ch, 00h, 03h, 0B4h
	db	10h, 0F2h
	
FMDrumIns03:
	db	3Ch, 0Fh, 00h, 00h, 00h, 1Fh, 1Ah, 18h, 1Ch, 17h, 11h, 1Ah, 0Eh, 00h
	db	0Fh, 14h, 10h, 1Fh, 0ECh, 0FFh, 0FFh, 07h, 80h, 16h, 80h
	
FMDrum89:
	db	31h, 0Bh, 0F7h, 0Ah, 00h
	db	04h, 0FEh, 03h, 00h, 00h, 00h, 95h, 20h, 0F2h
	
FMDrumIns04:
	db	3Ch, 0Ah, 50h, 70h, 00h, 1Fh, 17h	; $B30
	db	19h, 1Dh, 1Dh, 15h, 1Ah, 17h, 06h, 18h, 07h, 19h, 0Fh, 5Fh, 6Fh, 1Fh, 0Ch, 95h
	db	00h, 8Eh
	
FMDrum8A:
	db	58h, 0Bh, 00h, 07h, 00h, 07h, 0FEh, 00h, 03h, 00h, 03h, 0D1h, 08h, 0F2h
	
FMDrumIns05:
	db	3Dh, 00h, 0Fh, 0Fh, 0Fh, 1Fh, 9Fh, 9Fh, 9Fh, 1Fh, 1Fh, 1Fh, 1Fh, 00h, 0Eh, 10h
	db	0Fh, 0Fh, 4Fh, 4Fh, 4Fh, 00h, 90h, 90h, 85h
; =======================================================================================

	
cfHandler:
	ld	hl, cfReturn
	
zloc_B7C:
	push	hl
	sub	0E0h
	ld	hl, cfPtrTable
	rst	ReadPtrTable
	ld	a, (de)
	jp	(hl)
	
cfReturn:
	inc	de
	jp	zloc_1E4
	
cfMetaCoordFlag:
	ld	hl, cfMetaPtrTable
	rst	ReadPtrTable
	inc	de
	ld	a, (de)
	jp	(hl)

; =================================	
cfPtrTable:
	dw	cfE0_Pan
	dw	cfE1_Detune
	dw	cfE2_SetComm
	dw	cfE3_SilenceTrk
	dw	cfE4_PanAnim
	dw	cfE5_ChgPFMVol
	dw	cfE6_ChgFMVol
	dw	cfE7_Hold
	dw	cfE8_NoteStop
	dw	cfE9_SetLFO
	dw	cfEA_SetUpdRate
	dw	cfEB_ChgUpdRate
	dw	cfEC_ChgPSGVol
	dw	cfED_FMChnWrite
	dw	cfEE_FM1Write
	dw	cfEF_SetIns
	dw	cfF0_ModSetup
	dw	cfF1_ModTypePFM
	dw	cfF2_StopTrk
	dw	cfF3_PSGNoise
	dw	cfF4_ModType
	dw	cfF5_SetPSGIns
	dw	cfF6_GoTo
	dw	cfF7_Loop
	dw	cfF8_GoSub
	dw	cfF9_Return
	dw	cfFA_TickMult
	dw	cfFB_ChgTransp
	dw	cfFC_PitchSlide
	dw	cfFD_RawFrqMode
	dw	cfFE_SpcFM3Mode
	dw	cfMetaCoordFlag
; =================================

; =================================
cfMetaPtrTable:
	dw	cf00_TimingMode
	dw	cf01_SetTempo
	dw	cf02_PlaySnd
	dw	cf03_MusPause
	dw	cf04_CopyMem
	dw	cf05_TickMulAll
	dw	cf06_SSGEG
	dw	cf07_FMVolEnv
; =================================


cf06_SSGEG:
	ld	(ix+18h), 80h
	ld	(ix+19h), e
	ld	(ix+1Ah), d
	
SendSSGEG:
	ld	hl, SSGEG_Ops
	ld	b, 4
	
-
	ld	a, (de)
	inc	de
	ld	c, a
	ld	a, (hl)
	inc	hl
	rst	WriteFMMain
	djnz	-
	dec	de
	ret
	
cf05_TickMulAll:
	exx
	ld	b, 0Ah
	ld	de, 30h
	ld	hl, 1C42h
	
-
	ld	(hl), a
	add	hl, de
	djnz	-
	exx
	ret
	
cf00_TimingMode:
	ld	(1C07h), a		; set 1C07, the	Timing Mode
	ret
	
cfEA_SetUpdRate:
	ld	hl, 1C04h		; 1C04/1C05 = YM2612 Timer A value (Music Tempo)
	ex	de, hl			; (sound driver	update rate)
	ldi
	ldi
	ldi					; 1C06 = YM2612	Timer B	value (SFX Tempo)
	ex	de, hl
	dec	de
	ret
	
cfEB_ChgUpdRate:
	ex	de, hl
	ld	c, (hl)
	inc	hl
	ld	b, (hl)
	inc	hl
	ex	de, hl
	ld	hl, (1C04h)
	add	hl, bc			; add 2-byte value to 1C04/1C05	Timer A
	ld	(1C04h), hl
	ld	a, (de)
	ld	hl, 1C06h
	add	a, (hl)			; add 1-byte value to 1C06 Timer B
	ld	(hl), a
	ret
	
cf02_PlaySnd:
	push	ix
	call	PlaySnd_JumpIn		; play Sound ID	from parameter A
	pop	ix
	ret
	
cf03_MusPause:
	ld	(1C11h), a		; 1C11 - Music is paused
	or	a
	jr	z, zloc_C58		; 00 - unpause,	so jump
	push	ix			; 01-FF	- pause	music
	push	de
	ld	ix, 1C40h		; 1C40 - Music Tracks
	ld	b, 0Ah			; 10 music tracks
	ld	de, 30h
	
-
	res	7, (ix+0)		; disable channel
	call	SendNoteOff	; turn FM note off
	add	ix, de
	djnz	-
	pop	de
	pop	ix
	jp	SilencePSG
	
zloc_C58:
	push	ix
	push	de
	ld	ix, 1C40h		; 1C40 - Music Tracks
	ld	b, 0Ah			; 10 music tracks
	ld	de, 30h
	
-
	set	7, (ix+0)	; re-enable channel
	add	ix, de
	djnz	-

	pop	de
	pop	ix
	ret
	
cf04_CopyMem:
	ex	de, hl
	ld	e, (hl)
	inc	hl
	ld	d, (hl)
	inc	hl
	ld	c, (hl)
	ld	b, 0
	inc	hl
	ex	de, hl
	ldir
	dec	de
	ret
	
cfE1_Detune:
	ld	(ix+10h), a
	ret
	
cf07_FMVolEnv:
	ld	(ix+18h), a
	inc	de
	ld	a, (de)
	ld	(ix+19h), a
	ret
	
cf01_SetTempo:
	ld	hl, 1C14h		; 1C14 - Tempo Value (frame-based timing)
	add	a, (hl)
	ld	(hl), a			; set 1C14 (Initial Tempo)
	dec	hl
	ld	(hl), a			; set 1C13 (Tempo Timeout)
	ret
	
cfE2_SetComm:
	ld	(1C16h), a
	ret
	
cfEC_ChgPSGVol:
	bit	7, (ix+1)
	ret	z
	res	4, (ix+0)
	dec	(ix+17h)
	add	a, (ix+6)
	ld	(ix+6), a
	ret
	
cfED_FMChnWrite:
	call	ReadFMCommand
	rst	WriteFMMain
	ret
	
cfEE_FM1Write:
	call	ReadFMCommand
	rst	JmpTo_WriteFMI
	ret
	
ReadFMCommand:
	ex	de, hl
	ld	a, (hl)
	inc	hl
	ld	c, (hl)
	ex	de, hl
	ret
	
cfF0_ModSetup:
	ld	(ix+20h), e
	ld	(ix+21h), d
	ld	(ix+7), 80h
	inc	de
	inc	de
	inc	de
	ret
	
cfE3_SilenceTrk:
	call	SilenceFMChn
	jp	cfF2_StopTrk
	
cfE8_NoteStop:
	call	TickMultiplier
	ld	(ix+1Eh), a
	ld	(ix+1Fh), a
	ret
	
cfE4_PanAnim:
	push	ix
	pop	hl
	ld	bc, 11h
	add	hl, bc
	ex	de, hl
	ld	bc, 5
	ldir
	ld	a, 1
	ld	(de), a
	ex	de, hl
	dec	de
	ret
	
cfE7_Hold:
	set	1, (ix+0)
	dec	de
	ret
	
cfFE_SpcFM3Mode:
	ld	a, (ix+1)
	cp	2
	jr	nz, SpcFM3_skip
	set	0, (ix+0)
	exx
	call	GetFM3FreqPtr
	ld	b, 4
	
-
	push	bc
	exx
	ld	a, (de)
	inc	de
	exx
	ld	hl, FM3_FreqVals
	add	a, a
	ld	c, a
	ld	b, 0
	add	hl, bc
	ldi
	ldi
	pop	bc
	djnz	-
	exx
	dec	de
	ld	a, 4Fh	; enable Special FM3 Mode
	
SendFM3SpcMode:
	ld	(1C12h), a
	ld	c, a
	ld	a, 27h
	rst	JmpTo_WriteFMI
	ret
	
SpcFM3_skip:
	inc	de
	inc	de
	inc	de
	ret

; =================================================	
FM3_FreqVals:
	db	00h, 00h, 32h, 01h, 8Eh, 01h, 0E4h, 01h
; =================================================

cfEF_SetIns:
	bit	7, (ix+1)
	jr	nz, zloc_D6C
	call	SetMaxRelRate
	ld	a, (de)
	ld	(ix+8), a
	push	af
	inc	de
	ld	a, (de)
	ld	(ix+0Fh), a
	pop	af
	or	a
	jp	p, zloc_D61
	
SetInsFromSong:
	push	de
	ld	hl, 8000h
	ld	c, 4
	ld	a, (ix+0Fh)
	sub	81h
	call	JmpTo_GetPtrListOfs
	rst	ReadPtrTable
	rst	ReadPtrFromHL
	ld	a, (ix+8)
	and	7Fh
	ld	b, a
	call	JumpToInsData
	jr	zloc_D67
	
zloc_D61:
	dec	de
	push	de
	ld	b, a
	call	GetFMInsPtr
	
zloc_D67:
	call	SendFMIns
	pop	de
	ret
	
zloc_D6C:
	ld	a, (de)
	or	a
	ret	p
	inc	de
	ret
	
cfE0_Pan:
	ld	c, 3Fh
	
zloc_D73:
	ld	a, (ix+0Ah)
	and	c
	ex	de, hl
	or	(hl)
	ld	(ix+0Ah), a
	ld	c, a
	ld	a, 0B4h
	rst	WriteFMMain
	ex	de, hl
	ret
	
cfE9_SetLFO:
	ld	c, a
	ld	a, 22h
	rst	JmpTo_WriteFMI
	inc	de
	ld	c, 0C0h
	jr	zloc_D73
	
RefreshVolume:
	exx
	ld	de, Volume_Ops
	ld	l, (ix+1Ch)
	ld	h, (ix+1Dh)
	ld	b, 4
	
-
	ld	a, (hl)
	or	a
	jp	p, +
	add	a, (ix+6)
+
	and	7Fh
	ld	c, a
	ld	a, (de)
	rst	WriteFMMain
	inc	de
	inc	hl
	djnz	-
	exx
	ret
	
cfE5_ChgPFMVol:
	inc	de
	add	a, (ix+6)
	ld	(ix+6), a
	ld	a, (de)
	
cfE6_ChgFMVol:
	bit	7, (ix+1)
	ret	nz
	add	a, (ix+6)
	ld	(ix+6), a
	jr	RefreshVolume
	
cfFB_ChgTransp:
	add	a, (ix+5)
	ld	(ix+5), a
	ret
	
cfFA_TickMult:
	ld	(ix+2), a
	ret
	
cfF3_PSGNoise:
	bit	2, (ix+1)
	ret	nz
	ld	a, 0DFh
	ld	(7F11h), a
	ld	a, (de)
	ld	(ix+1Ah), a
	set	0, (ix+0)
	or	a
	jr	nz, zloc_DE5
	res	0, (ix+0)
	ld	a, 0FFh
	
zloc_DE5:
	ld	(7F11h), a
	ret
	
cfF5_SetPSGIns:
	bit	7, (ix+1)
	ret	z
	ld	(ix+8), a
	ret
	
cfF1_ModTypePFM:
	inc	de
	bit	7, (ix+1)
	jr	nz, cfF4_ModType
	ld	a, (de)
	
cfF4_ModType:
	ld	(ix+7), a
	ret
	
cfF6_GoTo:
	ex	de, hl
	ld	e, (hl)
	inc	hl
	ld	d, (hl)
	dec	de
	ret
	
cfFC_PitchSlide:
	cp	1
	jr	nz, zloc_E0D
	set	5, (ix+0)
	ret
	
zloc_E0D:
	res	1, (ix+0)
	res	5, (ix+0)
	xor	a
	ld	(ix+10h), a
	ret
	
cfFD_RawFrqMode:
	cp	1
	jr	nz, +
	set	3, (ix+0)
	ret
	
+
	res	3, (ix+0)
	ret
	
cfF2_StopTrk:
	res	7, (ix+0)
	ld	a, 1Fh
	ld	(1C15h), a
	call	DoNoteOff
	ld	c, (ix+1)
	push	ix
	call	GetSFXChnPtrs
	ld	a, (1C19h)
	or	a
	jr	z, zloc_EAB
	xor	a
	ld	(1C18h), a		; reset	Current	Sound Priority
	bit	7, (iy+0)
	jr	z, zloc_E5E
	ld	a, (ix+1)
	cp	(iy+1)
	jr	nz, zloc_E5E
	push	iy
	ld	l, (iy+2Ah)
	ld	h, (iy+2Bh)
	jr	zloc_E62
	
zloc_E5E:
	push	hl
	ld	hl, (1C37h)
	
zloc_E62:
	pop	ix
	res	2, (ix+0)
	bit	7, (ix+1)
	jr	nz, zloc_EB0
	bit	7, (ix+0)
	jr	z, zloc_EAB
	ld	a, 2
	cp	(ix+1)
	jr	nz, zloc_E88
	ld	a, 4Fh
	bit	0, (ix+0)
	jr	nz, zloc_E85
	and	0Fh
	
zloc_E85:
	call	SendFM3SpcMode
	
zloc_E88:
	ld	a, (ix+8)
	or	a
	jp	p, zloc_E94
	call	SetInsFromSong
	jr	zloc_EA8
	
zloc_E94:
	ld	b, a
	call	JumpToInsData
	call	SendFMIns
	ld	a, (ix+18h)
	or	a
	jp	p, zloc_EAB
	ld	e, (ix+19h)
	ld	d, (ix+1Ah)
	
zloc_EA8:
	call	SendSSGEG
	
zloc_EAB:
	pop	ix
	pop	hl
	pop	hl
	ret
	
zloc_EB0:
	bit	0, (ix+0)
	jr	z, zloc_EAB
	ld	a, (ix+1Ah)
	or	a
	jp	p, zloc_EC0
	ld	(7F11h), a
	
zloc_EC0:
	jr	zloc_EAB
	
cfF8_GoSub:
	ld	c, a
	inc	de
	ld	a, (de)
	ld	b, a
	push	bc
	push	ix
	pop	hl
	dec	(ix+9)
	ld	c, (ix+9)
	dec	(ix+9)
	ld	b, 0
	add	hl, bc
	ld	(hl), d
	dec	hl
	ld	(hl), e
	pop	de
	dec	de
	ret
	
cfF9_Return:
	push	ix
	pop	hl
	ld	c, (ix+9)
	ld	b, 0
	add	hl, bc
	ld	e, (hl)
	inc	hl
	ld	d, (hl)
	inc	(ix+9)
	inc	(ix+9)
	ret
	
cfF7_Loop:
	inc	de
	add	a, 28h
	ld	c, a
	ld	b, 0
	push	ix
	pop	hl
	add	hl, bc
	ld	a, (hl)
	or	a
	jr	nz, zloc_EFF
	ld	a, (de)
	ld	(hl), a

zloc_EFF:
	inc	de
	dec	(hl)
	jp	nz, cfF6_GoTo
	inc	de
	ret
	
UpdatePSGTrk:
	call	TrackTimeout
	jr	nz, zloc_F18
	call	TrkUpdate_Proc
	bit	4, (ix+0)
	ret	nz
	call	PrepareModulat
	jr	zloc_F24
	
zloc_F18:
	ld	a, (ix+1Eh)
	or	a
	jr	z, zloc_F24
	dec	(ix+1Eh)
	jp	z, SetRest
	
zloc_F24:
	call	DoPitchSlide
	call	DoModulation
	bit	2, (ix+0)
	ret	nz
	ld	c, (ix+1)
	ld	a, l
	and	0Fh
	or	c
	ld	(7F11h), a
	ld	a, l
	and	0F0h
	or	h
	rrca
	rrca
	rrca
	rrca
	ld	(7F11h), a
	ld	a, (ix+8)
	or	a
	ld	c, 0
	jr	z, zloc_F55
	dec	a
	ld	c, 0Ah
	rst	GetListOffset		; get List 5 (PSG envelopes)
	rst	ReadPtrTable
	call	DoPSGVolEnv
	ld	c, a
	
zloc_F55:
	bit	4, (ix+0)
	ret	nz
	ld	a, (ix+6)
	add	a, c
	bit	4, a
	jr	z, zloc_F64
	ld	a, 0Fh
	
zloc_F64:
	or	(ix+1)
	add	a, 10h
	bit	0, (ix+0)
	jr	nz, zloc_F73
	ld	(7F11h), a
	ret
	
zloc_F73:
	add	a, 20h
	ld	(7F11h), a
	ret

zloc_F79:	
	ld	(ix+17h), a
	
DoPSGVolEnv:
	push	hl
	ld	c, (ix+17h)
	call	GetEnvData	; BC = HL (base) + BC (index), A = (BC)
	pop	hl
	bit	7, a
	jr	z, VolEnv_Next
	cp	83h
	jr	z, VolEnv_Off	; 83 - stop the	tone
	cp	81h
	jr	z, VolEnv_Hold	; 81 - hold the	envelope at current level
	cp	80h
	jr	z, VolEnv_Reset	; 80 - loop back to beginning
	inc	bc
	ld	a, (bc)
	jr	zloc_F79
	
VolEnv_Off:
	set	4, (ix+0)
	pop	hl
	jp	SetRest
	
VolEnv_Reset:
	xor	a
	jr	zloc_F79
	
VolEnv_Hold:
	pop	hl
	set	4, (ix+0)
	ret
	
VolEnv_Next:
	inc	(ix+17h)
	ret
	
SetRest:
	set	4, (ix+0)
	bit	2, (ix+0)
	ret	nz
	
SilencePSGChn:
	ld	a, 1Fh
	add	a, (ix+1)
	or	a
	ret	p
	ld	(7F11h), a
	bit	0, (ix+0)
	ret	z
	ld	a, 0FFh
	ld	(7F11h), a
	ret
	

SoundDriver_End:
