; Battle transition fixes.
	if fast_transitions

; The sound queue caches special commands as well as music IDs. If battle
; starts while a fade/stop command is cached, restoring that byte after the
; battle leaves the field silent. Save an actual music ID when available;
; otherwise use the map header's music ID at +6. Its +4 byte is an entrance
; command (often $00 or $FF), not a music ID.
Battle_SaveMusic:
	moveq	#0, d0
	move.b	(sound_queue).w, d0
	cmpi.b	#$81, d0
	bcs.s	Battle_SaveMapMusic
	cmpi.b	#$B0, d0
	bcs.s	Battle_SaveMusic_Done
Battle_SaveMapMusic:
	lea	(loc_3C36A).l, a0
	move.w	(map_id).w, d0
	adda.w	d0, a0
	adda.w	(a0), a0
	moveq	#0, d0
	move.b	$6(a0), d0
Battle_SaveMusic_Done:
	move.b	d0, (sound_queue_saved).w
	rts
	endif

; Left in a battle target picker steps to the previous target. The stock
; pickers add one for any direction and let the target validator (loc_107BE)
; search forward from there; Right, Up and Down still do. In: d7 = the pressed
; directions, a6 = the battle context. Out: $D(a6), which the picker then
; validates as usual (a valid index comes back unchanged).
	if battle_target_left
TechTarget_Direction:			; routine $D8, from loc_E810
	btst	#ButtonLeft, d7
	beq.s	BattleTarget_Next
	movea.w	$6C(a6), a0		; the target type, as loc_E712 finds it
	move.w	$4A(a0), d0
	lsl.w	#3, d0
	lea	(TechniqueData).l, a1
	adda.w	d0, a1
	moveq	#0, d0
	move.b	$9(a1), d0
	bra.s	BattleTarget_Prev

ItemTarget_Direction:			; routine $64, from loc_E402
	btst	#ButtonLeft, d7
	beq.s	BattleTarget_Next
	movea.w	$6C(a6), a3		; the target type, as loc_E364 finds it
	lea	$64(a3), a0
	moveq	#0, d0
	move.b	$C(a6), d0
	move.w	(a0,d0.w), d0
	jsr	(loc_107AA).l
	bra.s	BattleTarget_Prev

DefendTarget_Direction:			; routine $144, from loc_E8C0; loc_E83E
	btst	#ButtonLeft, d7		; then validates it as type 2 (one ally)
	beq.s	BattleTarget_Next
	moveq	#2, d0
	bra.s	BattleTarget_Prev

BattleTarget_Next:
	addq.b	#1, $D(a6)
	rts

; d0 = target type (even: loc_107BE's table has 4-byte entries). Types 2 and 6
; (one ally), 8 and $A (one enemy) and $C and $E (one of two groups) name a
; target by index; the others keep the stock step.
; Tries the indices below $D(a6), wrapping from 0 to 11 (the enemy slots), and
; keeps the first one the validator returns as it was given: an ally index
; past the party comes back as 0 and a missing enemy as the next live one.
; The validators use d0-d7/a0-a1 only, so a2-a4 carry the search.
BattleTarget_Prev:
	movem.l	d0-d7/a0-a4, -(sp)
	move.l	#%0101010101000100, d2
	btst	d0, d2
	beq.s	BattleTarget_PrevNone
	movea.w	d0, a2			; type
	moveq	#0, d1
	move.b	$D(a6), d1
	cmpi.w	#$B, d1
	bls.s	+
	moveq	#0, d1
+	movea.w	d1, a4			; where the search started
	movea.w	d1, a3			; candidate
BattleTarget_PrevLoop:
	move.w	a3, d1
	subq.w	#1, d1
	bpl.s	+
	moveq	#$B, d1
+	movea.w	d1, a3
	cmpa.w	a4, a3
	beq.s	BattleTarget_PrevFound	; round to the start: it is the only one
	move.w	a2, d0
	jsr	(loc_107BE).l
	cmpa.w	($FFFFD11A).w, a3
	bne.s	BattleTarget_PrevLoop
BattleTarget_PrevFound:
	move.w	a3, d1
	move.b	d1, $D(a6)
	movem.l	(sp)+, d0-d7/a0-a4
	rts
BattleTarget_PrevNone:
	movem.l	(sp)+, d0-d7/a0-a4
	addq.b	#1, $D(a6)
	rts
	endif
