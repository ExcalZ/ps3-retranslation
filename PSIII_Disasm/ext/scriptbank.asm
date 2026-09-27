; The translated GameScript exceeds $10000 bytes. Space-scene dialogue uses
; offsets beyond that boundary, but script_offset and the original scene table
; are words. Keep the original table for stock builds and use full offsets here.

ScriptBank_Resolve:
	lea	(GameScript).l, a0
	cmpi.w	#1, (ScriptBank_High).w
	bne.s	+
	adda.l	#$10000, a0
+	adda.l	d0, a0
	rts

; d0 is the original word index into loc_15F90. Do not change it: the space
; scene uses the same index for its sound and animation tables afterward.
ScriptBank_SelectSpaceScript:
	clr.w	(ScriptBank_High).w
	lea	(ScriptBank_SpaceTable).l, a0
	move.w	d0, d1
	add.w	d1, d1
	move.l	(a0,d1.w), d1
	bmi.s	+
	bset	#2, $FFFFD005.w
	move.w	d1, (script_offset).w
	swap	d1
	move.w	d1, (ScriptBank_High).w
+	jmp	loc_14DC0

; The existing script loader copies the selected text before returning. Clear
; the high word after that call so later field dialogue uses the normal base.
ScriptBank_Dialogue:
	jsr	(loc_18C1A).l
	clr.w	(ScriptBank_High).w
	rts

; The intro's closing narration is also beyond $10000 after the latest text
; edits. Its direct call uses the same loader as the late space scenes.
ScriptBank_Set307B0:
	move.l	#loc_307B0-GameScript, d0
	move.w	d0, (script_offset).w
	swap	d0
	move.w	d0, (ScriptBank_High).w
	swap	d0
	rts

; The ending event selects this script before entering MainGame_GameScript.
; Its word offset sits close to the bank boundary and must retain its high word.
ScriptBank_Set305FE:
	move.l	#loc_305FE-GameScript, d0
	move.w	d0, (script_offset).w
	swap	d0
	move.w	d0, (ScriptBank_High).w
	swap	d0
	rts

; Wren's transformation table stores offsets relative to GameScript2. Add the
; full GameScript2 delta before splitting the result into the word and bank.
; d0 remains the table's word index for the caller's animation branch.
ScriptBank_SelectWrenScript:
	lea	(loc_18CF2).l, a0
	moveq	#0, d1
	move.w	(a0,d0.w), d1
	addi.l	#GameScript2-GameScript, d1
	move.w	d1, (script_offset).w
	swap	d1
	move.w	d1, (ScriptBank_High).w
	rts

ScriptBank_Set30A3E:
	move.l	#loc_30A3E-GameScript, d0
	move.l	d0, d1
	swap	d1
	move.w	d1, (ScriptBank_High).w
	rts

	even
ScriptBank_SpaceTable:
	dc.l	loc_303C0-GameScript
	dc.l	loc_30A0A-GameScript
	dc.l	$FFFFFFFF
	dc.l	loc_3044E-GameScript
	dc.l	loc_3052C-GameScript
	dc.l	$FFFFFFFF
	dc.l	loc_305CE-GameScript
	dc.l	loc_30BE6-GameScript
	dc.l	$FFFFFFFF
	dc.l	loc_30A9E-GameScript
	dc.l	loc_307D2-GameScript
	dc.l	loc_3085C-GameScript
	dc.l	loc_3094A-GameScript
