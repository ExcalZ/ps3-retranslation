; ===========================================================================
; Technique Distributor: keep the distribution box on screen.
;
; The box the Technique Distributor draws (loc_C852) is (t0x+t1x) cells wide and
; (t0y+t2y) cells tall, one cell per point, and its cursor sits (t0x, t0y) cells
; from the corner. Every point is drawn, so at high levels the box runs off the
; right of the plane and below the $E00-byte plane buffer at $FFFF2000: the rows
; past it land on the scroll tables and the plane B buffer, and the game can
; crash. Both drawing routines now work from a copy of the eight values divided
; by the smallest k that fits the box into TECHDIST_MAXW x TECHDIST_MAXH cells
; (each arm at least one cell). The values themselves - what the player edits and
; what is written back - are untouched.
; ===========================================================================
	if fix_tech_distributor

TECHDIST_MAXW = 24	; columns 15..38 stay left of the screen edge
TECHDIST_MAXH = 14	; rows 6..19 stay above the message window

; a0 = the eight raw values; draws the box into the plane buffer
TechDist_Box:
	subq.w	#8, sp
	movea.l	sp, a1
	bsr.s	TechDist_Scale
	movea.l	sp, a0
	jsr	(loc_C852).l
	addq.w	#8, sp
	rts

; a0 = the eight raw values; a5 = the cursor object. Places the cursor sprite
; (loc_C828 without its `lea $30(a5), a0`) and shows it.
TechDist_Cursor:
	subq.w	#8, sp
	movea.l	sp, a1
	bsr.s	TechDist_Scale
	movea.l	sp, a0
	move.w	$8(a5), d0
	moveq	#0, d1
	move.b	(a0), d1
	lsl.w	#3, d1
	add.w	d1, d0
	move.w	d0, $1A(a5)
	move.w	$A(a5), d0
	moveq	#0, d1
	move.b	$1(a0), d1
	lsl.w	#3, d1
	add.w	d1, d0
	move.w	d0, $1C(a5)
	addq.w	#8, sp
	jmp	(DisplaySprite).l

; a0 = raw values -> (a1) = scaled copy. Trashes d0-d4.
TechDist_Scale:
	moveq	#0, d0
	move.b	(a0), d0
	add.b	$2(a0), d0		; width in cells
	moveq	#0, d1
	move.b	$1(a0), d1
	add.b	$5(a0), d1		; height in cells
	moveq	#1, d2			; divisor k
	move.w	#TECHDIST_MAXW, d3
	move.w	#TECHDIST_MAXH, d4
-
	cmp.w	d3, d0
	bhi.s	+
	cmp.w	d4, d1
	bls.s	TechDist_Fits
+
	addq.w	#1, d2
	add.w	#TECHDIST_MAXW, d3
	add.w	#TECHDIST_MAXH, d4
	bra.s	-
TechDist_Fits:
	moveq	#7, d3
-
	moveq	#0, d0
	move.b	(a0)+, d0
	divu.w	d2, d0
	tst.w	d0
	bne.s	+
	moveq	#1, d0			; an arm of zero cells would hide the axis
+
	move.b	d0, (a1)+
	dbf	d3, -
	rts

	endif
