; ===========================================================================
; Technique Distributor: keep the distribution box on screen.
;
; The box the Technique Distributor draws (loc_C852) is (t0x+t1x) cells wide and
; (t0y+t2y) cells tall, one cell per point, and its cursor sits (t0x, t0y) cells
; from the corner. At high levels the stock box can run past the plane buffer.
; Scale the display by the exact limiting width/height ratio, so a box only a
; little too tall does not suddenly shrink by half. Clear the previous outline
; before each redraw; loc_C852 only clears the new box's interior. The values
; the player edits and what is written back are untouched.
; ===========================================================================
	if fix_tech_distributor

TECHDIST_MAXW = 24	; columns 15..38 stay left of the screen edge
TECHDIST_MAXH = 14	; rows 6..19 stay above the message window

; a0 = the eight raw values; draws the box into the plane buffer
TechDist_Box:
	subq.w	#8, sp
	movea.l	sp, a1
	bsr.w	TechDist_Scale
	lea	$FFFF231E, a2
	moveq	#TECHDIST_MAXH-1, d0
TechDist_ClearRow:
	movea.l	a2, a3
	moveq	#TECHDIST_MAXW-1, d1
TechDist_ClearCell:
	clr.w	(a3)+
	dbf	d1, TechDist_ClearCell
	lea	$80(a2), a2
	dbf	d0, TechDist_ClearRow
	; Erase the label location in savestates made by the earlier build.
	lea	$FFFF2218, a2
	lea	$80(a2), a3
	moveq	#5, d0
TechDist_ClearOldLabel:
	clr.w	(a2)+
	clr.w	(a3)+
	dbf	d0, TechDist_ClearOldLabel
	movea.l	sp, a0
	jsr	(loc_C852).l
	addq.w	#8, sp
	rts

; a0 = the eight raw values; a5 = the cursor object. Places the cursor sprite
; (loc_C828 without its `lea $30(a5), a0`) and shows it.
TechDist_Cursor:
	subq.w	#8, sp
	movea.l	sp, a1
	bsr.w	TechDist_Scale
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

; a0 = raw values -> (a1) = scaled copy. Trashes d0-d5.
; The common scale is min(1, MAXW/width, MAXH/height), as d2/d3.
TechDist_Scale:
	moveq	#0, d0
	move.b	(a0), d0
	moveq	#0, d4
	move.b	$2(a0), d4
	add.w	d4, d0			; width in cells (no byte wrap)
	moveq	#0, d1
	move.b	$1(a0), d1
	moveq	#0, d4
	move.b	$5(a0), d4
	add.w	d4, d1			; height in cells
	moveq	#1, d2			; numerator
	moveq	#1, d3			; denominator
	cmpi.w	#TECHDIST_MAXW, d0
	bhi.s	TechDist_NeedsScale
	cmpi.w	#TECHDIST_MAXH, d1
	bls.s	TechDist_ApplyScale
TechDist_NeedsScale:
	move.w	d0, d4
	mulu.w	#TECHDIST_MAXH, d4
	move.w	d1, d5
	mulu.w	#TECHDIST_MAXW, d5
	cmp.l	d5, d4
	bhi.s	TechDist_WidthLimits
	moveq	#TECHDIST_MAXH, d2
	move.w	d1, d3
	bra.s	TechDist_ApplyScale
TechDist_WidthLimits:
	moveq	#TECHDIST_MAXW, d2
	move.w	d0, d3
TechDist_ApplyScale:
	moveq	#7, d4
-
	moveq	#0, d0
	move.b	(a0)+, d0
	mulu.w	d2, d0
	divu.w	d3, d0
	tst.w	d0
	bne.s	+
	moveq	#1, d0			; an arm of zero cells would hide the axis
+
	move.b	d0, (a1)+
	dbf	d4, -
	; Round each complete axis once, then make its two arms complementary.
	; Moving a point changes the cursor position, not the outer box dimensions.
	moveq	#0, d0
	move.b	-8(a0), d0
	moveq	#0, d4
	move.b	-6(a0), d4
	add.w	d4, d0
	mulu.w	d2, d0
	divu.w	d3, d0
	cmpi.w	#2, d0
	bhs.s	+
	moveq	#2, d0
+
	moveq	#0, d1
	move.b	-7(a0), d1
	moveq	#0, d4
	move.b	-3(a0), d4
	add.w	d4, d1
	mulu.w	d2, d1
	divu.w	d3, d1
	cmpi.w	#2, d1
	bhs.s	+
	moveq	#2, d1
+
	moveq	#0, d4
	move.b	-8(a1), d4
	cmp.w	d0, d4
	blo.s	+
	move.w	d0, d4
	subq.w	#1, d4
	move.b	d4, -8(a1)
+
	move.w	d0, d5
	sub.w	d4, d5
	move.b	d5, -6(a1)
	moveq	#0, d4
	move.b	-4(a1), d4
	cmp.w	d0, d4
	blo.s	+
	move.w	d0, d4
	subq.w	#1, d4
	move.b	d4, -4(a1)
+
	move.w	d0, d5
	sub.w	d4, d5
	move.b	d5, -2(a1)
	moveq	#0, d4
	move.b	-7(a1), d4
	cmp.w	d1, d4
	blo.s	+
	move.w	d1, d4
	subq.w	#1, d4
	move.b	d4, -7(a1)
+
	move.w	d1, d5
	sub.w	d4, d5
	move.b	d5, -3(a1)
	moveq	#0, d4
	move.b	-5(a1), d4
	cmp.w	d1, d4
	blo.s	+
	move.w	d1, d4
	subq.w	#1, d4
	move.b	d4, -5(a1)
+
	move.w	d1, d5
	sub.w	d4, d5
	move.b	d5, -1(a1)
	rts
	endif
