; ===========================================================================
; Four save slots.
;
; Backup RAM is odd bytes at $200001: blocks of $1000 address bytes. The stock
; game keeps two saves in blocks 0-1 and a copy of each in blocks 2-3 (written
; after every save, restored at game select when a slot fails its header or
; checksum). Here blocks 0-3 are four saves and blocks 4-7 their copies, so
; the header declares 32 KB of backup RAM ($200001-$207FFF); emulators and
; flash carts size the SRAM from the header. Saves from the stock game are
; slots 1 and 2 unchanged (their copies move from blocks 2-3 to 4-5: the
; first game select in this build finds them "fine" and does not need them).
;
; The slot code takes a slot number in d0 everywhere; the stock masks (`andi
; #1` / `#3`) and the +2 of the copy become `#3` / `#7` and +4 (patched in
; place, see ps3.asm). The rest of this file is the user interface: the game
; select checks four slots in a loop instead of two unrolled ones and keeps a
; status per slot, the slot lists are four rows drawn from one string built
; here, the cursor moves over four rows (skipping empty slots where only a
; saved game can be chosen), and every message about "the chosen slot" reads
; its name and level through {NAME:00}/{NUM:00} after SaveSlots_Select copied
; them there - so the per-slot string variants of the stock game are unused.
; ===========================================================================
	if four_save_slots

SAVE_SLOTS      = 4
SAVE_CANCEL     = SAVE_SLOTS*4		; $1C(a6) value that means "backed out of the list"

; RAM equates: ext/ram.asm

; window parameters (x, y, stride, rows, cells, ?): the stock lists are 6 rows
SaveSlots_WinGS:
	dc.w	4, 6, $1C, 10, $C
	dc.b	0, 2
SaveSlots_WinChurch:
	dc.w	$C, $A, $1C, 10, $C
	dc.b	0, 2
SaveSlots_Empty:
	dc.b	"-", $FC
	even

; ---------------------------------------------------------------------------
; In place of loc_11B88: names and levels of the four slots for {NAME:nn}/{NUM:nn}
; (nn = 4*slot), and the list text "1.Name LVn{BR}2.-{BR}...".
; ---------------------------------------------------------------------------
SaveSlots_Gather:
	movem.l	d0-d7/a0-a4, -(sp)
	lea	(SaveSlots_List).w, a3
	moveq	#0, d3			; slot
SaveSlots_Gather_Slot:
	move.w	d3, d0
	ror.w	#4, d0			; slot * $1000
	lea	$00200029, a1
	adda.w	d0, a1			; name, odd bytes from offset $28
	lea	(SaveSlots_Names).w, a2
	move.w	d3, d1
	mulu.w	#10, d1
	adda.w	d1, a2
	move.w	d3, d1
	add.w	d1, d1
	add.w	d1, d1			; 4*slot
	lea	(char_name_saved).w, a4
	move.l	a2, (a4,d1.w)
	moveq	#7, d2
	jsr	(loc_149E6).l		; 8 odd bytes -> (a2)
	move.b	#$FC, (a2)
	lea	$0020007B, a1
	adda.w	d0, a1			; level, offset $7A
	moveq	#0, d2
	move.b	(a1), d2
	move.w	d3, d1
	add.w	d1, d1
	add.w	d1, d1			; 4*slot again (loc_149E6 used d1)
	lea	$FFFFD4A0.w, a4
	move.l	d2, (a4,d1.w)
	; list row: "n." then name + " LV" + number, or "-" for an empty/bad slot
	move.b	d3, d2
	addi.b	#'1', d2
	move.b	d2, (a3)+
	move.b	#'.', (a3)+
	move.w	d3, d0
	jsr	(loc_14984).l		; header check (carry set = bad)
	bcs.s	SaveSlots_Gather_Empty
	move.w	d3, d0
	jsr	(loc_149B6).l		; checksum (carry set = bad)
	bcs.s	SaveSlots_Gather_Empty
	lea	(SaveSlots_Names).w, a2
	move.w	d3, d1
	mulu.w	#10, d1
	adda.w	d1, a2
-
	move.b	(a2)+, d2
	cmpi.b	#$FC, d2
	beq.s	+
	move.b	d2, (a3)+
	bra.s	-
+
	move.b	#' ', (a3)+
	move.b	#'L', (a3)+
	move.b	#'V', (a3)+
	move.b	#$E4, (a3)+
	move.w	d3, d1
	add.w	d1, d1
	add.w	d1, d1
	move.b	d1, (a3)+		; {NUM:4*slot}
	bra.s	SaveSlots_Gather_Next
SaveSlots_Gather_Empty:
	move.b	#'-', (a3)+
SaveSlots_Gather_Next:
	move.b	#$F8, (a3)+
	addq.w	#1, d3
	cmpi.w	#SAVE_SLOTS, d3
	bcs.w	SaveSlots_Gather_Slot
	move.b	#$FC, -1(a3)		; the last {BR} becomes the terminator
	movem.l	(sp)+, d0-d7/a0-a4
	rts

; ---------------------------------------------------------------------------
; Point {NAME:00}/{NUM:00} at slot d0's name and level and put the slot number
; in {NUM:08}, for the messages about one chosen slot.
; ---------------------------------------------------------------------------
SaveSlots_Select:
	movem.l	d0-d1/a0, -(sp)
	move.w	d0, d1
	add.w	d1, d1
	add.w	d1, d1
	lea	(char_name_saved).w, a0
	move.l	(a0,d1.w), (a0)
	lea	$FFFFD4A0.w, a0
	move.l	(a0,d1.w), (a0)
	addq.w	#1, d0
	move.l	d0, $FFFFD4A8.w
	movem.l	(sp)+, d0-d1/a0
	rts

; ---------------------------------------------------------------------------
; Game select, state $40 (loc_115EA): record the slot's result, go on to the
; next slot or, after the last, to the summary state $6C.
; ---------------------------------------------------------------------------
SaveSlots_NextSlot:
	move.w	$1A(a6), d0
	add.w	d0, d0
	lea	(SaveSlots_Status).w, a0
	move.w	$60(a6), (a0,d0.w)
	addq.w	#1, $1A(a6)
	cmpi.w	#SAVE_SLOTS, $1A(a6)
	bcc.s	+
	move.w	#$18, (game_general_routine).w
	rts
+
	move.w	#$6C, (game_general_routine).w
	rts

; d0 = number of fine slots; d1 = first fine slot (or -1)
SaveSlots_Count:
	moveq	#0, d0
	moveq	#-1, d1
	moveq	#0, d2
	lea	(SaveSlots_Status).w, a0
-
	cmpi.w	#4, (a0)+
	bne.s	+
	addq.w	#1, d0
	tst.w	d1
	bpl.s	+
	move.w	d2, d1
+
	addq.w	#1, d2
	cmpi.w	#SAVE_SLOTS, d2
	bcs.s	-
	rts

; state $6C (loc_115FA): $62(a6) = 0 none / 4 one / 8 several saved games
SaveSlots_Summarize:
	bsr.w	SaveSlots_Count
	moveq	#0, d2
	tst.w	d0
	beq.s	+
	moveq	#4, d2
	cmpi.w	#1, d0
	beq.s	+
	moveq	#8, d2
+
	move.w	d2, $62(a6)
	tst.w	d2
	bne.s	+
	move.w	#$158, (game_general_routine).w	; no saved game: text speed, new game
	rts
+
	addq.w	#4, (game_general_routine).w
	rts

; states $88 (loc_1171A, erase) and $130 (loc_119AA, continue): with one saved
; game choose it; with several show the list prompt (the stock code follows).
SaveSlots_EraseEntry:
	cmpi.w	#4, $62(a6)
	bne.s	+
	bsr.w	SaveSlots_Count
	add.w	d1, d1
	add.w	d1, d1
	move.w	d1, $1C(a6)
	move.w	#$AC, (game_general_routine).w
	rts
+
	jmp	(loc_11736).l
SaveSlots_ContinueEntry:
	cmpi.w	#4, $62(a6)
	bne.s	+
	bsr.w	SaveSlots_Count
	add.w	d1, d1
	add.w	d1, d1
	move.w	d1, $1C(a6)
	move.w	#$154, (game_general_routine).w
	rts
+
	jmp	(loc_119C6).l

; state $F8 (loc_11968, new game): warn only when every slot holds a game
SaveSlots_NewGameEntry:
	bsr.w	SaveSlots_Count
	cmpi.w	#SAVE_SLOTS, d0
	beq.s	+
	clr.b	$22(a6)
	move.w	#$11C, (game_general_routine).w
	rts
+
	jmp	(loc_1197C).l

; state $AC (loc_11840): confirm erasing slot $1C(a6)/4
SaveSlots_ConfirmErase:
	cmpi.w	#SAVE_CANCEL, $1C(a6)
	bcs.s	+
	move.w	#$6C, (game_general_routine).w
	rts
+
	jsr	(SaveSlots_Gather).l
	move.w	$1C(a6), d0
	lsr.w	#2, d0
	bsr.w	SaveSlots_Select
	jsr	(loc_A804).l
	lea	(loc_3E457).l, a0	; "Do you really want {NAME:00}, LV{NUM:00} erased?"
	lea	$FFFF9AB6.w, a1
	move.w	#$8000, d0
	jmp	(loc_10038).l

; state $D0 (loc_11916): erase it (unless NO was chosen)
SaveSlots_Erase:
	tst.b	$22(a6)
	beq.s	+
	move.w	#$6C, (game_general_routine).w
	rts
+
	move.w	$1C(a6), d0
	lsr.w	#1, d0
	lea	(SaveSlots_Status).w, a0
	clr.w	(a0,d0.w)
	ror.w	#5, d0			; (slot*2) ror 5 = slot * $1000
	lea	$00200005, a0
	clr.b	(a0,d0.w)		; the header byte: the slot reads as empty
	jsr	(SaveSlots_Gather).l	; fresh levels: Select overwrote {NUM:08} with the slot number
	move.w	$1C(a6), d0
	lsr.w	#2, d0
	bsr.w	SaveSlots_Select
	jsr	(loc_A804).l
	lea	(loc_3E47C).l, a0	; "{NAME:00}, LV{NUM:00} has been erased."
	lea	$FFFF9AB6.w, a1
	move.w	#$8000, d0
	jmp	(loc_10038).l

; state $154 (loc_119DE): load slot $1C(a6)/4 and start
SaveSlots_Continue:
	cmpi.w	#SAVE_CANCEL, $1C(a6)
	bcs.s	+
	move.w	#$6C, (game_general_routine).w
	rts
+
	jmp	(loc_119EE).l

; ---------------------------------------------------------------------------
; The lists. loc_1174E draws the game-select list; SaveSlots_Gather has already
; built the text, so only the string and the window change (patched in place).
; The church list (loc_C448) drew two rows from four strings: draw the text.
; ---------------------------------------------------------------------------
SaveSlots_ChurchList:
	lea	(SaveSlots_WinChurch).l, a0
	jsr	(loc_FC9A).l
	lea	$FFFF9C80.w, a0
	jsr	(loc_FCE2).l
	jsr	(SaveSlots_Gather).l
	lea	(SaveSlots_WinChurch).l, a0
	jsr	(loc_FC9A).l
	jsr	(loc_B8BA).l
	clr.w	$C(a6)			; cursor on the first row
	addq.w	#4, (game_general_routine).w
	lea	(SaveSlots_List).w, a0
	lea	$FFFF9C9E.w, a1
	move.w	#$8000, d0
	jmp	(loc_10038).l

; ---------------------------------------------------------------------------
; Cursor over the list rows. a2 = the list's plane-buffer position (set by the
; two stock entry points), d7 = skip rows whose slot is not a saved game.
; Replaces loc_11784: B backs out ($1C = SAVE_CANCEL), C/A chooses ($1C =
; row*4), up/down move with wrap.
; ---------------------------------------------------------------------------
SaveSlots_CursorGS:				; in place of loc_1177E
	lea	$FFFF2308, a2
	moveq	#1, d7
	bra.s	SaveSlots_Cursor
SaveSlots_CursorChurch:			; in place of loc_11776
	lea	$FFFF2518, a2
	moveq	#0, d7
SaveSlots_Cursor:
	tst.b	$C(a6)
	bne.s	SaveSlots_Cursor_Input
	; first frame on the list: make sure the cursor sits on a selectable row
	tst.w	d7
	beq.s	SaveSlots_Cursor_Input
	moveq	#0, d0
	move.b	$D(a6), d0
	bsr.w	SaveSlots_RowOK
	tst.b	d5
	bne.s	SaveSlots_Cursor_Input
	bsr.w	SaveSlots_Count
	add.w	d1, d1
	add.w	d1, d1
	move.b	d1, $D(a6)
SaveSlots_Cursor_Input:
	move.b	(joypad_pressed).w, d6
	moveq	#0, d0
	move.b	$D(a6), d0
	move.w	d0, d1
	btst	#Button_B, d6
	beq.s	+
	jsr	(GetSelectionSound).l
	move.w	#SAVE_CANCEL, $1C(a6)
	addq.w	#4, (game_general_routine).w
	rts
+
	move.b	d6, d5
	andi.b	#Button_C_Mask|Button_A_Mask, d5
	beq.s	SaveSlots_Cursor_Move
	jsr	(GetSelectionSound).l
	move.w	d0, $1C(a6)
	lsr.w	#1, d0
	addq.w	#1, d0
	jsr	(loc_B7DE).l		; cursor shown steadily
	addq.w	#4, (game_general_routine).w
	lea	(a2), a0
	lea	(LoadDataInVRAMWithOffset).l, a2
	jmp	(loc_FC58).l
SaveSlots_Cursor_Move:
	move.b	d6, d5
	andi.b	#ButtonUp_Mask|ButtonDown_Mask, d5
	bne.s	+
	addq.b	#1, $C(a6)		; blink
	andi.b	#7, $C(a6)
	beq.s	SaveSlots_Cursor_Toggle
	rts
+
	moveq	#SAVE_SLOTS-1, d4	; at most this many steps to find a selectable row
-
	btst	#ButtonDown, d6
	beq.s	+
	addq.w	#4, d1
	cmpi.w	#SAVE_CANCEL, d1
	bcs.s	SaveSlots_Cursor_Check
	moveq	#0, d1
	bra.s	SaveSlots_Cursor_Check
+
	subq.w	#4, d1
	bcc.s	SaveSlots_Cursor_Check
	moveq	#SAVE_CANCEL-4, d1
SaveSlots_Cursor_Check:
	tst.w	d7
	beq.s	SaveSlots_Cursor_Set
	move.w	d0, -(sp)
	move.w	d1, d0
	bsr.w	SaveSlots_RowOK
	move.w	(sp)+, d0
	tst.b	d5
	bne.s	SaveSlots_Cursor_Set
	dbf	d4, -
	rts				; nothing else selectable: stay
SaveSlots_Cursor_Set:
	move.b	d1, $D(a6)
	lsr.w	#1, d0
	addq.w	#1, d0
	jsr	(loc_B81C).l		; clear the old row
	clr.b	$C(a6)
	moveq	#0, d0
	move.b	$D(a6), d0
SaveSlots_Cursor_Toggle:
	lsr.w	#1, d0
	addq.w	#1, d0
	jsr	(loc_B868).l		; toggle the new row
	lea	(a2), a0
	lea	(LoadDataInVRAMWithOffset).l, a2
	jmp	(loc_FC58).l

; d0 = row*4 -> d5 = 1 when that slot holds a saved game, else 0 (d0 kept)
SaveSlots_RowOK:
	move.w	d0, -(sp)
	lsr.w	#1, d0
	lea	(SaveSlots_Status).w, a0
	cmpi.w	#4, (a0,d0.w)
	seq	d5
	andi.b	#1, d5
	move.w	(sp)+, d0
	rts

; ---------------------------------------------------------------------------
; Church: "Saved {NAME:00}, LV{NUM:00} in {NUM:08}." for the chosen slot
; (in place of loc_C570)
; ---------------------------------------------------------------------------
SaveSlots_SavedMsg:
	jsr	(loc_A804).l
	jsr	(SaveSlots_Gather).l
	move.w	$1C(a6), d0
	lsr.w	#2, d0
	bsr.w	SaveSlots_Select
	lea	(loc_3E322).l, a0
	lea	$FFFF9AB6.w, a1
	move.w	#$8000, d0
	jmp	(loc_10038).l

	endif
