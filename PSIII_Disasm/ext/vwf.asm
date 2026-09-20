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
;
; The field menu (vwf_menu): while a menu "map" ($202-$20C) is loaded, VRAM
; holds only the font and the five portrait slots at tiles $100-$23F, and the
; field's art is reloaded when the menu closes. Text written into the plane A
; buffer ($FFFF2000, 64 cells a row) whose glyph row is 1-24 and whose column
; is 4-35 is composed the same way, into a pool that shadows the screen: one
; tile per visible cell, $240 + (glyph row - 1) * 32 + (column - 4), $240-$53F.
; A redraw of a cell reuses its tile, so nothing is allocated or freed; the
; line fills $44(a6) cells with paper after the ink as the stock renderer does,
; and a $F8 that leaves the range hands the rest of the string to the stock
; renderer. The main-menu list is first rendered into its 10x12 staging buffer,
; so its five exact line addresses map to the screen-shadowing tiles they will
; occupy after loc_10C42 copies it. Item names, equipment, technique names and
; the labels all go through this path; numbers (loc_FF7E) and the row-25 name
; plate stay fixed width.
;
; The shops (vwf_shop): a store screen ($222-$230) is a map of the same kind -
; the field art is reloaded on exit and the map itself loads one picture at
; tiles $101-$131 - and its buy and sell lists are composed into a window
; buffer (buy list $FFFFA126, five lines of 16 cells, stride $48; sell list
; pages $FFFF9D30 and $FFFF9E80, five lines of 11 cells, stride $38) that the
; window animation copies to plane A. Those rows take the same path with a
; pool line per list line at $240-$2FD (VWFShop_Table); the buy list's price
; is written after the name from cell 11, so a name has 88 px on every list.
; A $F8 in a list line hands the rest to the stock renderer (the pool locate
; fails outside plane A), which no list uses.
;
; The battle box (vwf_battle): the enemy-group lines, the character names of
; the stat window and the item and technique lists, from VWFBattle_Table
; (see there for the battle screen's VRAM). PS III has no enemy targeting, so
; nothing anchors a cursor to those cells; the highlights are palette toggles
; on the copied words, and the name highlight is widened to five cells in
; ps3.asm (loc_D56C) to match the name's five-cell pool line.
; ===========================================================================
	if vwf_dialogue

VWFDIA_POOL     = $C0		; first pool tile
VWFDIA_CELLS    = 24		; cells per dialogue line
VWFDIA_LINEPX    = VWFDIA_CELLS*8	; 192 px
VWFDIA_STRIDE   = 26		; canvas row stride: 24 cells + 2 spill bytes
VWFDIA_BLANK    = $1F		; the paper tile
VWFMENU_POOL    = $240		; menu pool: 24 rows x 32 columns of the plane A buffer
VWFMENU_ROWS    = 24
VWFMENU_COLS    = 32
VWFMENU_COL0    = 4
VWFPOOL_END     = $540		; the sprite table ($A800) starts here

; RAM equates: ext/ram.asm

; ---------------------------------------------------------------------------
; Entry: registers as loc_10038 (a0 text, a1 mark-row pointer, d0 attribute,
; a6 window context). Falls through to the stock renderer for other windows.
; ---------------------------------------------------------------------------
VWFDia_Entry:
	clr.w	(VWFDia_Skew).w
	if vwf_menu
	move.w	(map_id).w, d1
	subi.w	#$202, d1
	cmpi.w	#$A, d1			; a menu screen ($202-$20C, one per generation)
	bhi.s	VWFDia_NotMenu
	bsr.w	VWFMenu_Locate		; d1 = pool tile, d2 = capacity; d1 = $FFFF if not pooled
	cmpi.w	#VWFMENU_POOL+VWFMENU_ROWS*VWFMENU_COLS, d1
	bcc.s	VWFDia_NotMenu
	bra.w	VWFMenu_Go
VWFDia_NotMenu:
	endif
	if vwf_shop
	move.w	(map_id).w, d1
	subi.w	#$222, d1
	cmpi.w	#$E, d1			; a store screen ($222-$230, one per store type)
	bhi.s	VWFDia_NotShop
	lea	VWFShop_Table(pc), a2
	bsr.w	VWFList_Find		; d1 = pool tile, d2 = capacity; d1 = $FFFF if not a list line
	cmpi.w	#$FFFF, d1
	beq.s	VWFDia_NotShop
	bra.w	VWFMenu_Go
VWFDia_NotShop:
	endif
	if vwf_battle
	cmpi.w	#$232, (map_id).w	; the battle screen
	bne.s	VWFDia_NotBattle
	lea	VWFBattle_Table(pc), a2
	bsr.w	VWFList_Find
	cmpi.w	#$FFFF, d1
	beq.s	VWFDia_NotBattle
	bra.w	VWFMenu_Go
VWFDia_NotBattle:
	endif
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
	clr.w	(VWFDia_Mode).w
	move.w	#VWFDIA_CELLS, (VWFDia_Cap).w
	move.w	#VWFDIA_LINEPX, (VWFDia_MaxPx).w
	move.w	#VWFDIA_CELLS, (VWFDia_Pad).w
	bsr.w	VWFDia_LinePool
VWFDia_Begin:
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
	movea.l	(VWFDia_Row).w, a1	; as the stock renderer leaves it: the last line's mark
	suba.w	(VWFDia_Skew).w, a1	; row (the shop list writes the price relative to it)
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
	move.w	$42(a6), d2
	add.w	d2, d2
	movea.l	(VWFDia_Row).w, a1
	adda.w	d2, a1
	move.l	a1, (VWFDia_Row).w
	if vwf_menu|vwf_shop
	tst.w	(VWFDia_Mode).w
	beq.s	VWFDia_Newline_Dia
	bsr.w	VWFMenu_Locate
	cmpi.w	#VWFMENU_POOL+VWFMENU_ROWS*VWFMENU_COLS, d1
	bcc.w	VWFMenu_Handoff
	bsr.w	VWFMenu_SetLine
	bsr.w	VWFDia_StartLine
	bra.w	VWFDia_Loop
VWFDia_Newline_Dia:
	endif
	move.w	(VWFDia_Line).w, d1
	addq.w	#1, d1
	cmpi.w	#1, d1
	bls.s	+
	moveq	#1, d1			; a third line has nowhere to go: overwrite the second
+
	move.w	d1, (VWFDia_Line).w
	bsr.w	VWFDia_LinePool
	bsr.w	VWFDia_StartLine
	bra.w	VWFDia_Loop

; pool tile of the dialogue line: $C0 for line 0, $D8 for line 1
VWFDia_LinePool:
	move.w	(VWFDia_Line).w, d2
	mulu.w	#VWFDIA_CELLS, d2
	addi.w	#VWFDIA_POOL, d2
	move.w	d2, (VWFDia_Tile).w
	rts

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
	cmp.w	(VWFDia_MaxPx).w, d5
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
	move.w	(VWFDia_X).w, d5
	addq.w	#7, d5
	lsr.w	#3, d5			; cells that hold ink
	move.w	d5, (VWFDia_Count).w
	bsr.w	VWFDia_Expand		; (clobbers d5)
	bsr.w	VWFDia_Upload
	move.w	(VWFDia_Count).w, d5
	move.w	(VWFDia_Pad).w, d6
	cmp.w	d5, d6
	bcc.s	+
	move.w	d5, d6			; cells written: the ink, or the pad width if wider
+
	subq.w	#1, d6
	bmi.s	VWFDia_Flush_Done	; nothing at all (a blank line in a zero-width window)
	movea.l	(VWFDia_Row).w, a1
	move.w	(VWFDia_Attr).w, d3
	move.w	d3, d1
	ori.w	#VWFDIA_BLANK, d1
	move.w	d6, d7
-
	move.w	d1, (a1)+		; mark row: paper
	dbf	d7, -
	movea.l	(VWFDia_Row).w, a1
	adda.w	$42(a6), a1		; glyph row
	move.w	(VWFDia_Tile).w, d2
	or.w	d3, d2			; first pool tile of this line, with attributes
	move.w	d6, d7
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
VWFDia_Flush_Done:
	rts

; canvas of the current line -> VWFDia_Scratch (24 tiles, 4bpp)
VWFDia_Expand:
	move.w	(VWFDia_Count).w, d7
	subq.w	#1, d7
	bmi.s	VWFDia_Expand_Done
	bsr.w	VWFDia_CanvasPtr
	lea	(VWFDia_Scratch).w, a5
	lea	(VWFDia_NibbleLUT).l, a4
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
VWFDia_Expand_Done:
	rts

; canvas of the current line -> VWFDia_Scratch with a transparent paper (colour 0) and,
; with vwf_scroll_shadow, a shadow in colour 2 one pixel right and down of the ink.
; Each output nibble pair is looked up by (ink nibble << 4 | shadow nibble).
VWFDia_ExpandOpen:
	bsr.w	VWFDia_CanvasPtr
	lea	(VWFDia_Scratch).w, a5
	lea	(VWFDia_ShadowLUT).l, a4
	moveq	#VWFDIA_CELLS-1, d7
VWFDia_ExpandOpen_Tile:
	moveq	#0, d3			; previous row's shadow bits for this column (16 bits: this byte and the next)
	moveq	#7, d6
-
	moveq	#0, d5
	move.b	(a2), d5		; ink, this byte
	move.w	d3, d4			; shadow = previous row shifted right by one pixel
	if vwf_scroll_shadow
	else
	moveq	#0, d4
	endif
	; high nibble: ink bits 7-4, shadow bits 7-4 of the shifted previous row
	move.w	d5, d2
	andi.w	#$F0, d2		; ink << 4 already in place
	move.w	d4, d1
	lsr.w	#4, d1
	andi.w	#$F, d1
	or.w	d1, d2
	add.w	d2, d2
	move.w	(a4,d2.w), (a5)+
	move.w	d5, d2
	andi.w	#$F, d2
	lsl.w	#4, d2
	move.w	d4, d1
	andi.w	#$F, d1
	or.w	d1, d2
	add.w	d2, d2
	move.w	(a4,d2.w), (a5)+
	; this row becomes the next row's shadow source: (byte, next byte) >> 1
	move.w	d5, d3
	lsl.w	#8, d3
	move.b	1(a2), d3
	lsr.w	#1, d3
	lsr.w	#8, d3
	andi.w	#$FF, d3
	; the bit shifted out of the previous byte's low end belongs to this byte
	move.b	-1(a2), d1
	andi.w	#1, d1
	ror.w	#1, d1			; -> bit 15
	lsr.w	#8, d1			; -> bit 7
	or.w	d1, d3
	lea	VWFDIA_STRIDE(a2), a2
	dbf	d6, -
	suba.w	#8*VWFDIA_STRIDE-1, a2	; next column
	dbf	d7, VWFDia_ExpandOpen_Tile
	lea	(VWFDia_Font).l, a4
	rts

; VWFDia_Scratch -> VRAM, the current line's pool tiles
VWFDia_Upload:
	movem.l	d0-d2/a0-a1, -(sp)
	move.w	(VWFDia_Count).w, d1
	lsl.w	#5, d1			; bytes
	beq.s	+
	lea	(VWFDia_Scratch).w, a0
	move.w	(VWFDia_Tile).w, d0
	lsl.w	#5, d0			; VRAM address of the line's first pool tile
	jsr	(LoadDataInVRAMWithOffset).l
+
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
	clr.w	(VWFDia_Mode).w
	move.w	#VWFDIA_POOL, (VWFDia_Tile).w
	move.w	#VWFDIA_CELLS, (VWFDia_Count).w
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
	move.w	#VWFDIA_LINEPX, (VWFDia_MaxPx).w
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
	bsr.w	VWFDia_ExpandOpen
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

; ---------------------------------------------------------------------------
; The field menu, the shop lists and the battle box (VWFMenu_Go is the shared
; pooled-line entry).
; ---------------------------------------------------------------------------
	if vwf_menu|vwf_shop|vwf_battle
; a1 = a mark row in the plane A buffer? Then d1 = the pool tile of its first
; cell and d2 = how many cells fit before column 36 (at most 24). d1 = $FFFF
; (past the pool's end: compare unsigned) when the row is not one the pool
; covers (mark rows 0-23, columns 4-35 of $FFFF2000).
VWFMenu_Locate:
	; The main-menu list is composed into a 10-cell-wide staging buffer, then
	; copied to plane A at column 16. Its five mark rows land at screen rows
	; 1, 3, 5, 7 and 9. Accept only that buffer's exact 8-cell text context.
	cmpi.w	#$14, $42(a6)
	bne.s	VWFMenu_Locate_Plane
	cmpi.w	#8, $44(a6)
	bne.s	VWFMenu_Locate_Plane
	move.w	a1, d1
	cmpi.w	#$9A82, d1
	beq.s	VWFMenu_Locate_MainStart
	cmpi.w	#$9B22, d1
	bne.s	VWFMenu_Locate_MainCheck
VWFMenu_Locate_MainStart:
	addq.w	#2, a1			; keep the stock full-cell left margin
	addq.w	#2, d1
	move.w	#2, (VWFDia_Skew).w	; undone at exit so a1 ends where the stock leaves it
VWFMenu_Locate_MainCheck:
	moveq	#0, d2
	cmpi.w	#$9A84, d1
	beq.s	VWFMenu_Locate_Main
	addq.w	#2, d2
	cmpi.w	#$9AAC, d1
	beq.s	VWFMenu_Locate_Main
	addq.w	#2, d2
	cmpi.w	#$9AD4, d1
	beq.s	VWFMenu_Locate_Main
	addq.w	#2, d2
	cmpi.w	#$9AFC, d1
	beq.s	VWFMenu_Locate_Main
	addq.w	#2, d2
	cmpi.w	#$9B24, d1
	bne.s	VWFMenu_Locate_Plane
VWFMenu_Locate_Main:
	cmpi.b	#' ', (a0)
	bne.s	+
	addq.w	#1, a0			; the margin is now the untouched first cell
+
	addq.w	#1, d2			; screen mark row
	lsl.w	#5, d2			; 32 pooled columns per row
	addi.w	#VWFMENU_POOL+13, d2	; screen column 17 - VWFMENU_COL0
	move.w	d2, d1
	moveq	#7, d2
	rts
VWFMenu_Locate_Plane:
	move.w	a1, d1			; low word: work RAM is $FFFFxxxx
	subi.w	#$2000, d1
	cmpi.w	#VWFMENU_ROWS*$80, d1
	bcc.s	VWFMenu_Locate_No
	move.w	d1, d2
	andi.w	#$7F, d2
	lsr.w	#1, d2			; cell column
	subq.w	#VWFMENU_COL0, d2
	bcs.s	VWFMenu_Locate_No
	cmpi.w	#VWFMENU_COLS, d2
	bcc.s	VWFMenu_Locate_No
	lsr.w	#7, d1			; mark row = glyph row - 1 = pool row
	lsl.w	#5, d1
	add.w	d2, d1
	addi.w	#VWFMENU_POOL, d1
	neg.w	d2
	addi.w	#VWFMENU_COLS, d2	; cells left on the row
	cmpi.w	#VWFDIA_CELLS, d2
	bls.s	+
	moveq	#VWFDIA_CELLS, d2
+
	rts
VWFMenu_Locate_No:
	move.w	#$FFFF, d1
	rts

; d1 = pool tile, d2 = capacity -> the line state
VWFMenu_SetLine:
	move.w	d1, (VWFDia_Tile).w
	move.w	d2, (VWFDia_Cap).w
	lsl.w	#3, d2
	move.w	d2, (VWFDia_MaxPx).w
	lsr.w	#3, d2
	move.w	$44(a6), d1
	cmp.w	d2, d1
	bls.s	+
	move.w	d2, d1			; never pad past this line's pool capacity
+
	move.w	d1, (VWFDia_Pad).w
	rts

	if vwf_shop|vwf_battle
; List windows whose lines get a pool line each. A table entry is six words:
; the low word of the first line's mark row, the stride between lines, the
; number of lines, the $44(a6) the call must carry (0: any), the capacity in
; cells, and the first pool tile; a zero row ends the table. Given a1 and a
; table in a2, VWFList_Find returns d1 = the line's first pool tile and
; d2 = its capacity, or d1 = $FFFF. d3-d7 are scratch.
VWFList_Find:
	move.w	(a2)+, d1		; first mark row (low word); 0 ends the table
	beq.s	VWFList_No
	move.w	(a2)+, d2		; stride
	move.w	(a2)+, d3		; lines
	move.w	(a2)+, d4		; $44(a6) to match, or 0
	move.w	(a2)+, d5		; capacity
	move.w	(a2)+, d6		; first pool tile
	tst.w	d4
	beq.s	+
	cmp.w	$44(a6), d4
	bne.s	VWFList_Find
+
	move.w	a1, d7
	sub.w	d1, d7			; offset from the first line
	bcs.s	VWFList_Find
	moveq	#0, d1			; line index: the offset must be a multiple of the stride
VWFList_Line:
	tst.w	d7
	beq.s	VWFList_Found
	sub.w	d2, d7
	bcs.s	VWFList_Find
	addq.w	#1, d1
	cmp.w	d3, d1
	bcs.s	VWFList_Line
	bra.s	VWFList_Find
VWFList_Found:
	mulu.w	d5, d1			; line * capacity
	add.w	d6, d1
	move.w	d5, d2
	rts
VWFList_No:
	move.w	#$FFFF, d1
	rts
	endif

	if vwf_shop
; The shop list windows: each is composed into its own buffer and copied to
; plane A by the window animation.
VWFShop_Table:
	dc.w	$A126, $48, 5, 16, 16, $240	; buy list (loc_3DB34): the price is written from cell 11
	dc.w	$9D30, $38, 5, 11, 11, $290	; sell list, page one (loc_3DB10)
	dc.w	$9E80, $38, 5, 11, 11, $2C7	; sell list, page two (loc_3DB1C)
	dc.w	0
	endif

	if vwf_battle
; The battle screen ($232). Its VRAM: background tiles $100-$27B, the box art
; and effects $280-$363, enemy art from $380, the sprite table at $A800, the
; box itself on the window plane from $B986 (rows 19-26; the window is shown
; from row 20). Free everywhere in a battle: $25C-$27F, $364-$37F, and the
; window plane's rows 0-18, $B000-$B97F = tiles $580-$5CB, which nothing
; writes or displays. The enemy-group lines ("{NAME} {NUM}", loc_DDDA) are
; composed into the box buffer; the character names of the stat window
; (Battle_WriteCharStats, $44(a6) = 4, five cells apart) and the item and
; technique lists (loc_3D8AE positions, $44(a6) = 9, nine cells) into plane A.
VWFBattle_Table:
	dc.w	$9D70, 0, 1, 0, 11, $580	; enemy group 0 (front row, left)
	dc.w	$9D86, 0, 1, 0, 11, $58B	; group 1 (front row, right)
	dc.w	$9CE8, 0, 1, 0, 11, $596	; group 2 (back row, left)
	dc.w	$9CFE, 0, 1, 0, 11, $5A1	; group 3 (back row, right)
	dc.w	$2A0C, $A, 5, 4, 5, $5AC	; character names, row 20, columns 6/11/16/21/26
	dc.w	$2A16, 0, 1, 9, 9, $25C		; item / technique list entries
	dc.w	$2A2A, 0, 1, 9, 9, $265
	dc.w	$2B16, 0, 1, 9, 9, $26E
	dc.w	$2B2A, 0, 1, 9, 9, $277
	dc.w	$2C16, 0, 1, 9, 9, $364
	dc.w	0
	endif

; d1 = pool tile, d2 = capacity: a pooled line (menu or shop)
VWFMenu_Go:
	movem.l	d1-d7/a2-a5, -(sp)
	move.w	d0, (VWFDia_Attr).w
	clr.w	(VWFDia_Line).w
	move.w	#1, (VWFDia_Mode).w
	move.l	a1, (VWFDia_Row).w
	bsr.w	VWFMenu_SetLine
	bra.w	VWFDia_Begin

; a $F8 moved the line out of the pool's rows: the stock renderer takes the
; rest of the string (a0) from the new row (a1). The insert flag is clear here
; (a $F8 inside an insert only ends the insert).
VWFMenu_Handoff:
	movem.l	(sp)+, d1-d7/a2-a5
	move.w	(VWFDia_Attr).w, d0
	jmp	(loc_10038_Fixed).l
	endif

; (ink nibble << 4 | shadow nibble) -> 4 colour nibbles: ink 1, else shadow 2, else 0
VWFDia_ShadowLUT:
	dc.w	$0000, $0002, $0020, $0022, $0200, $0202, $0220, $0222
	dc.w	$2000, $2002, $2020, $2022, $2200, $2202, $2220, $2222
	dc.w	$0001, $0001, $0021, $0021, $0201, $0201, $0221, $0221
	dc.w	$2001, $2001, $2021, $2021, $2201, $2201, $2221, $2221
	dc.w	$0010, $0012, $0010, $0012, $0210, $0212, $0210, $0212
	dc.w	$2010, $2012, $2010, $2012, $2210, $2212, $2210, $2212
	dc.w	$0011, $0011, $0011, $0011, $0211, $0211, $0211, $0211
	dc.w	$2011, $2011, $2011, $2011, $2211, $2211, $2211, $2211
	dc.w	$0100, $0102, $0120, $0122, $0100, $0102, $0120, $0122
	dc.w	$2100, $2102, $2120, $2122, $2100, $2102, $2120, $2122
	dc.w	$0101, $0101, $0121, $0121, $0101, $0101, $0121, $0121
	dc.w	$2101, $2101, $2121, $2121, $2101, $2101, $2121, $2121
	dc.w	$0110, $0112, $0110, $0112, $0110, $0112, $0110, $0112
	dc.w	$2110, $2112, $2110, $2112, $2110, $2112, $2110, $2112
	dc.w	$0111, $0111, $0111, $0111, $0111, $0111, $0111, $0111
	dc.w	$2111, $2111, $2111, $2111, $2111, $2111, $2111, $2111
	dc.w	$1000, $1002, $1020, $1022, $1200, $1202, $1220, $1222
	dc.w	$1000, $1002, $1020, $1022, $1200, $1202, $1220, $1222
	dc.w	$1001, $1001, $1021, $1021, $1201, $1201, $1221, $1221
	dc.w	$1001, $1001, $1021, $1021, $1201, $1201, $1221, $1221
	dc.w	$1010, $1012, $1010, $1012, $1210, $1212, $1210, $1212
	dc.w	$1010, $1012, $1010, $1012, $1210, $1212, $1210, $1212
	dc.w	$1011, $1011, $1011, $1011, $1211, $1211, $1211, $1211
	dc.w	$1011, $1011, $1011, $1011, $1211, $1211, $1211, $1211
	dc.w	$1100, $1102, $1120, $1122, $1100, $1102, $1120, $1122
	dc.w	$1100, $1102, $1120, $1122, $1100, $1102, $1120, $1122
	dc.w	$1101, $1101, $1121, $1121, $1101, $1101, $1121, $1121
	dc.w	$1101, $1101, $1121, $1121, $1101, $1101, $1121, $1121
	dc.w	$1110, $1112, $1110, $1112, $1110, $1112, $1110, $1112
	dc.w	$1110, $1112, $1110, $1112, $1110, $1112, $1110, $1112
	dc.w	$1111, $1111, $1111, $1111, $1111, $1111, $1111, $1111
	dc.w	$1111, $1111, $1111, $1111, $1111, $1111, $1111, $1111

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
