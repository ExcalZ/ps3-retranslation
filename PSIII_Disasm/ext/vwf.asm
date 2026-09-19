; ===========================================================================
; Proportional (variable-width) text for the dialogue window.
;
; The stock renderer (loc_10038) writes one 8x8 font tile per character into a
; window buffer in RAM: a "mark" row (blank in the US game; the JP game drew
; dakuten there) and a glyph row below it, 24 cells per line. This engine
; takes over when the target is one of the dialogue window's two text lines
; and composes the text instead: glyph rows are OR-ed into a 1bpp canvas of
; 192 px, the canvas is expanded to 24 4bpp tiles (ink colour 1, paper colour
; 2, like the font), the tiles are copied into a pool of 48 otherwise unused
; font tiles ($C0-$EF, VRAM $1800-$1DFF: the font block is $100 tiles and the
; art loaders never write below $2000), and the glyph row of the window gets
; the pool indices. Everything after that - the window animation, the copy to
; VRAM, the page wait - is the stock code.
;
; Windows that are not the dialogue's (menus, name lists, the small YES/NO
; box, the enemy-name row of the battle box whose columns place the target
; cursor) still go through the stock renderer: the entry checks the window is
; 24 cells wide and the target is one of the three dialogue rows or the battle
; message row. A message is two lines at most: a third $F8 line overwrites the
; second (the proofreader flags it).
;
; Control codes are handled as the stock renderer does: $F8 newline, $EC page
; wait (the rest of the text is left in $3E(a6) and bit 5 of $1(a6) is set),
; $FC end, $E8 nn string insert (pointer at char_name_saved+nn), $E4 nn number
; (long at $FFFFD4A0+nn, printed without leading zeros, "0" when zero), and
; $F4/$F0 nn (draw glyph nn; the mark is not drawn).
;
; The page scroll (loc_A368) copies the second line's tilemap words up into
; the first line, so VWFDia_ScrollUp also moves the second line's canvas up,
; rewrites those words to the first line's pool tiles and refreshes them in
; VRAM before the next page is rendered into the second line.
; ===========================================================================
	if vwf_dialogue

VWFDIA_POOL     = $C0		; first pool tile
VWFDIA_CELLS    = 24		; cells per dialogue line
VWFDIA_LINEPX    = VWFDIA_CELLS*8	; 192 px
VWFDIA_STRIDE   = 26		; canvas row stride: 24 cells + 2 spill bytes
VWFDIA_BLANK    = $1F		; the paper tile

; RAM equates: ext/ram.asm

; ---------------------------------------------------------------------------
; Entry: registers as loc_10038 (a0 text, a1 mark-row pointer, d0 attribute,
; a6 window context). Falls through to the stock renderer for other windows.
; ---------------------------------------------------------------------------
VWFDia_Entry:
	cmpi.w	#VWFDIA_CELLS, $44(a6)
	bne.s	VWFDia_Fixed
	moveq	#0, d1
	cmpa.l	#$FFFF9D26, a1		; script text into the window template
	beq.s	VWFDia_Go
	cmpa.l	#$FFFF9AB6, a1		; message into the live window, first line
	beq.s	VWFDia_Go
	cmpa.l	#$FFFF2C0A, a1		; battle message row (plane A buffer, row 24, col 5)
	beq.s	VWFDia_Go
	moveq	#1, d1
	cmpa.l	#$FFFF9B1E, a1		; next page into the live window, second line
	beq.s	VWFDia_Go
VWFDia_Fixed:
	jmp	(loc_10038_Fixed).l

VWFDia_Go:
	movem.l	d1-d7/a2-a5, -(sp)
	move.w	d0, (VWFDia_Attr).w
	move.w	d1, (VWFDia_Line).w
	move.l	a1, (VWFDia_Row).w
	bsr.w	VWFDia_StartLine
	lea	(VWFDia_Font).l, a4
	lea	(VWFDia_Width).l, a3
VWFDia_Loop:
	moveq	#0, d1
	move.b	(a0)+, d1
	cmpi.b	#$E0, d1
	bcs.s	VWFDia_Glyph
	cmpi.b	#$FC, d1
	beq.s	VWFDia_End
	cmpi.b	#$F8, d1
	beq.w	VWFDia_Newline
	cmpi.b	#$EC, d1
	beq.w	VWFDia_Page
	cmpi.b	#$E8, d1
	beq.w	VWFDia_Insert
	cmpi.b	#$E4, d1
	beq.w	VWFDia_Number
	; $F4 / $F0: glyph with a mark above it (JP only); draw the glyph
	move.b	(a0)+, d1
VWFDia_Glyph:
	bsr.w	VWFDia_Draw
	bra.s	VWFDia_Loop

VWFDia_Insert:
	move.b	(a0)+, d1
	move.l	a0, -(sp)
	lea	(char_name_saved).w, a2
	movea.l	(a2,d1.w), a0
	bset	#4, $1(a6)
	bra.s	VWFDia_Loop

VWFDia_End:				; $FC
	bclr	#4, $1(a6)
	beq.s	+
	movea.l	(sp)+, a0		; end of an inserted string: back to the text
	bra.s	VWFDia_Loop
+
	bsr.w	VWFDia_Flush
VWFDia_Exit:
	movem.l	(sp)+, d1-d7/a2-a5
	rts

VWFDia_Page:				; $EC
	bclr	#4, $1(a6)
	beq.s	+
	movea.l	(sp)+, a0		; inside an insert it only ends the insert
	bra.s	VWFDia_Loop
+
	bset	#5, $1(a6)
	move.l	a0, $3E(a6)
	bsr.w	VWFDia_Flush
	bra.s	VWFDia_Exit

VWFDia_Newline:				; $F8
	bclr	#4, $1(a6)
	beq.s	+
	movea.l	(sp)+, a0		; inside an insert it only ends the insert
	bra.w	VWFDia_Loop
+
	bsr.w	VWFDia_Flush
	move.w	(VWFDia_Line).w, d1
	addq.w	#1, d1
	cmpi.w	#1, d1
	bls.s	+
	moveq	#1, d1			; a third line has nowhere to go: overwrite the second
+
	move.w	d1, (VWFDia_Line).w
	move.w	$42(a6), d2
	add.w	d2, d2
	movea.l	(VWFDia_Row).w, a1
	adda.w	d2, a1
	move.l	a1, (VWFDia_Row).w
	bsr.w	VWFDia_StartLine
	bra.w	VWFDia_Loop

VWFDia_Number:				; $E4 nn
	move.b	(a0)+, d1
	lea	$FFFFD4A0.w, a2
	move.l	(a2,d1.w), d0
	bne.s	+
	moveq	#1, d1			; "0"
	bsr.w	VWFDia_Draw
	bra.w	VWFDia_Loop
+
	movem.l	a0-a1, -(sp)
	jsr	(loc_FA16).l		; binary -> packed BCD in d0
	movem.l	(sp)+, a0-a1
	move.l	d0, d6
	moveq	#8, d7
-
	subq.w	#1, d7
	rol.l	#4, d6
	move.b	d6, d1
	andi.w	#$F, d1
	beq.s	-			; skip leading zeros
-
	addq.w	#1, d1			; digit tiles are $01-$0A
	bsr.w	VWFDia_Draw
	rol.l	#4, d6
	move.b	d6, d1
	andi.w	#$F, d1
	dbf	d7, -
	bra.w	VWFDia_Loop

; ---------------------------------------------------------------------------
; Clear the current line's canvas and reset the pen.
; ---------------------------------------------------------------------------
VWFDia_StartLine:
	bsr.s	VWFDia_CanvasPtr
	moveq	#0, d1
	moveq	#(8*VWFDIA_STRIDE)/4-1, d2
-
	move.l	d1, (a2)+
	dbf	d2, -
	clr.w	(VWFDia_X).w
	rts

; a2 = canvas of the current line
VWFDia_CanvasPtr:
	lea	(VWFDia_Canvas0).w, a2
	tst.w	(VWFDia_Line).w
	beq.s	+
	lea	(VWFDia_Canvas1).w, a2
+
	rts

; ---------------------------------------------------------------------------
; Draw glyph d1 (a text byte) at the pen and advance. a3 = widths, a4 = font.
; Glyphs that would cross the right edge are dropped.
; ---------------------------------------------------------------------------
VWFDia_Draw:
	movem.l	d4-d7/a2/a5, -(sp)	; the number loop keeps its digits in d6/d7
	moveq	#0, d4
	move.b	(a3,d1.w), d4		; advance
	beq.s	VWFDia_Draw_Done
	move.w	(VWFDia_X).w, d2
	move.w	d2, d5
	add.w	d4, d5
	subq.w	#1, d5			; ink right edge (advance includes the 1 px gap)
	cmpi.w	#VWFDIA_LINEPX, d5
	bhi.s	VWFDia_Draw_Done
	bsr.s	VWFDia_CanvasPtr
	move.w	d2, d5
	lsr.w	#3, d5
	adda.w	d5, a2			; byte column
	move.w	d2, d7
	andi.w	#7, d7			; bit shift
	move.w	d1, d5
	lsl.w	#3, d5
	lea	(a4,d5.w), a5		; glyph rows
	moveq	#7, d5
-
	moveq	#0, d6
	move.b	(a5)+, d6
	lsl.w	#8, d6
	lsr.w	d7, d6
	or.b	d6, $1(a2)
	lsr.w	#8, d6
	or.b	d6, (a2)
	lea	VWFDIA_STRIDE(a2), a2
	dbf	d5, -
	add.w	d4, d2
	move.w	d2, (VWFDia_X).w
VWFDia_Draw_Done:
	movem.l	(sp)+, d4-d7/a2/a5
	rts

; ---------------------------------------------------------------------------
; Finish the current line: expand its canvas into pool tiles in VRAM and write
; the window's mark row and glyph row.
; ---------------------------------------------------------------------------
VWFDia_Flush:
	bsr.w	VWFDia_Expand
	bsr.w	VWFDia_Upload
	move.w	(VWFDia_X).w, d5
	addq.w	#7, d5
	lsr.w	#3, d5			; cells that hold ink
	movea.l	(VWFDia_Row).w, a1
	move.w	(VWFDia_Attr).w, d3
	move.w	d3, d1
	ori.w	#VWFDIA_BLANK, d1
	moveq	#VWFDIA_CELLS-1, d7
-
	move.w	d1, (a1)+		; mark row: paper
	dbf	d7, -
	movea.l	(VWFDia_Row).w, a1
	adda.w	$42(a6), a1		; glyph row
	move.w	(VWFDia_Line).w, d2
	mulu.w	#VWFDIA_CELLS, d2
	addi.w	#VWFDIA_POOL, d2
	or.w	d3, d2			; first pool tile of this line, with attributes
	moveq	#VWFDIA_CELLS-1, d7
VWFDia_Flush_Cells:
	subq.w	#1, d5
	bmi.s	VWFDia_Flush_Blanks
	move.w	d2, (a1)+
	addq.w	#1, d2
	dbf	d7, VWFDia_Flush_Cells
	rts
VWFDia_Flush_Blanks:
	move.w	d1, (a1)+
	dbf	d7, VWFDia_Flush_Blanks
	rts

; canvas of the current line -> VWFDia_Scratch (24 tiles, 4bpp)
VWFDia_Expand:
	bsr.w	VWFDia_CanvasPtr
	lea	(VWFDia_Scratch).w, a5
	lea	(VWFDia_NibbleLUT).l, a4
	moveq	#VWFDIA_CELLS-1, d7
VWFDia_Expand_Tile:
	moveq	#7, d6
-
	moveq	#0, d5
	move.b	(a2), d5
	move.w	d5, d4
	lsr.w	#4, d4
	add.w	d4, d4
	move.w	(a4,d4.w), (a5)+
	andi.w	#$F, d5
	add.w	d5, d5
	move.w	(a4,d5.w), (a5)+
	lea	VWFDIA_STRIDE(a2), a2
	dbf	d6, -
	suba.w	#8*VWFDIA_STRIDE-1, a2	; next column
	dbf	d7, VWFDia_Expand_Tile
	lea	(VWFDia_Font).l, a4	; restore for the draw loop
	rts

; VWFDia_Scratch -> VRAM, the current line's pool tiles
VWFDia_Upload:
	movem.l	d0-d2/a0-a1, -(sp)
	lea	(VWFDia_Scratch).w, a0
	move.w	(VWFDia_Line).w, d0
	mulu.w	#VWFDIA_CELLS*32, d0
	addi.w	#VWFDIA_POOL*32, d0
	move.w	#VWFDIA_CELLS*32, d1
	jsr	(LoadDataInVRAMWithOffset).l
	movem.l	(sp)+, d0-d2/a0-a1
	rts

; ---------------------------------------------------------------------------
; Page scroll: called in place of loc_A3BA (a0 = second line's mark row,
; a1 = first line's). After the stock copy, move the second line's canvas to
; the first, refresh the first line's pool tiles and retarget the copied words.
; ---------------------------------------------------------------------------
VWFDia_ScrollUp:
	jsr	(loc_A3BA).l
	movem.l	d0-d7/a0-a5, -(sp)
	lea	(VWFDia_Canvas1).w, a0
	lea	(VWFDia_Canvas0).w, a1
	moveq	#(8*VWFDIA_STRIDE)/4-1, d0
-
	move.l	(a0)+, (a1)+
	dbf	d0, -
	clr.w	(VWFDia_Line).w
	bsr.w	VWFDia_Expand
	bsr.w	VWFDia_Upload
	lea	$FFFF9AEA.w, a1		; glyph row of the first line
	moveq	#VWFDIA_CELLS-1, d7
-
	move.w	(a1), d0
	andi.w	#$7FF, d0
	subi.w	#VWFDIA_POOL+VWFDIA_CELLS, d0
	cmpi.w	#VWFDIA_CELLS, d0
	bcc.s	+
	subi.w	#VWFDIA_CELLS, (a1)	; second line's tile -> first line's
+
	addq.w	#2, a1
	dbf	d7, -
	movem.l	(sp)+, d0-d7/a0-a5
	rts

; ---------------------------------------------------------------------------
; The opening scroll. loc_1A156 scrolls plane A upward and, as each line's row
; comes around, writes it straight into VRAM with loc_F7F0 (a0 text, d1 column,
; d2 plane row, d3 attribute $6000). Hooked at loc_F7F0 when the script offset
; is the new-game intro's: the line is composed like a dialogue line and its
; tiles go to a pool of 8 x 24 tiles at $200-$2BF (plane B's picture uses
; $100-$1FF and $340-$413 on that screen). Lines sit four rows apart, so the
; slot is (row/4) mod 8: a slot is reused 32 rows after it was written, and a
; line has scrolled off the 28-row screen by then. Blank cells get tile 0
; (transparent), as the stock writer's spaces do.
; ---------------------------------------------------------------------------
VWFSCROLL_POOL  = $200

VWFScroll_Entry:
	cmpi.w	#loc_304DA-GameScript2, (script_offset).w
	bne.s	VWFScroll_Fixed
	cmpi.w	#$6000, d3
	bne.s	VWFScroll_Fixed
	cmpa.l	#loc_1B8C, a0		; the 40 blank tiles that clear a row: stock path
	bne.s	VWFScroll_Go
VWFScroll_Fixed:
	jmp	(loc_F7F0_Fixed).l

VWFScroll_Go:
	movem.l	d0-d7/a0-a6, -(sp)
	lea	$FFFFD280.w, a6		; VWFDia_Draw reads nothing from it, but keep the convention
	clr.w	(VWFDia_Line).w
	bsr.w	VWFDia_StartLine
	lea	(VWFDia_Font).l, a4
	lea	(VWFDia_Width).l, a3
-
	moveq	#0, d1
	move.b	(a0)+, d1
	cmpi.b	#$FC, d1
	beq.s	+
	cmpi.b	#$F8, d1		; no line breaks here: ignore
	beq.s	-
	cmpi.b	#$E0, d1
	bcs.s	VWFScroll_Glyph
	move.b	(a0)+, d1		; $F4/$F0 nn: the glyph without its mark
VWFScroll_Glyph:
	bsr.w	VWFDia_Draw
	bra.s	-
+
	bsr.w	VWFDia_Expand
	move.w	10(sp), d2		; the entry's row, from the saved frame
	move.w	d2, d3
	lsr.w	#2, d3
	andi.w	#7, d3			; slot
	mulu.w	#VWFDIA_CELLS, d3
	addi.w	#VWFSCROLL_POOL, d3	; first pool tile of this line
	move.w	d3, d0
	lsl.w	#5, d0			; its VRAM address
	move.w	d3, d4
	ori.w	#$6000, d4		; tile word: palette 3
	lea	(VWFDia_Scratch).w, a0
	move.w	#VWFDIA_CELLS*32, d1
	move.w	d4, -(sp)
	jsr	(LoadDataInVRAMWithOffset).l
	move.w	(sp)+, d4
	move.w	6(sp), d1		; the entry's column and row
	move.w	10(sp), d2
	; plane A words at (row d2, column d1): cells that hold ink, then transparent
	lsl.w	#7, d2
	add.w	d1, d1
	add.w	d1, d2
	addi.w	#$C000, d2
	bset	#6, $FFFFD006.w
	lea	vdp_control_port, a1
	move.w	d2, d1
	swap	d1
	move.w	d2, d1
	rol.w	#2, d1
	andi.l	#$3FFF0003, d1
	ori.l	#$40000000, d1
	move.l	d1, (a1)
	move.w	(VWFDia_X).w, d5
	addq.w	#7, d5
	lsr.w	#3, d5			; cells with ink
	moveq	#VWFDIA_CELLS-1, d7
VWFScroll_Cells:
	subq.w	#1, d5
	bmi.s	VWFScroll_Blanks
	move.w	d4, vdp_data_port
	addq.w	#1, d4
	dbf	d7, VWFScroll_Cells
	bra.s	VWFScroll_Done
VWFScroll_Blanks:
	move.w	#0, vdp_data_port
	dbf	d7, VWFScroll_Blanks
VWFScroll_Done:
	bclr	#6, $FFFFD006.w
	movem.l	(sp)+, d0-d7/a0-a6
	rts

; 4 pixels (a nibble, MSB = leftmost) -> 4 colour nibbles: ink 1, paper 2
VWFDia_NibbleLUT:
	dc.w	$2222, $2221, $2212, $2211, $2122, $2121, $2112, $2111
	dc.w	$1222, $1221, $1212, $1211, $1122, $1121, $1112, $1111

	even
VWFDia_Font:
	binclude "vwf/diafont.bin"
VWFDia_Width:
	binclude "vwf/diawidth.bin"
	even

	endif
