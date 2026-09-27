; Ending animations can reach their transmission cue while the translated
; dialogue still runs. The dialogue loader temporarily sets and clears bit 7
; of $FFFFD286, so remember that cue until its call returns. Every hook below
; replaces a six-byte instruction with a six-byte JSR; existing scene code and
; saved-state ROM pointers keep their addresses.

Ending_SpaceInit:
	jsr	(loc_6EA0).l
	clr.w	(Ending_Pending).w
	rts

Ending_Queue:
	move.w	#1, (Ending_Pending).w
	bset	#7, $FFFFD286.w
	rts

Ending_AfterDialogue:
	bclr	#7, $FFFFD286.w
	tst.w	(Ending_Pending).w
	beq.s	+
	bset	#7, $FFFFD286.w
+
	rts

Ending_Complete:
	bclr	#7, $FFFFD286.w
	clr.w	(Ending_Pending).w
	rts
