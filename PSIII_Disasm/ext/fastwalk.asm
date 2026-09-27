; ---------------------------------------------------------------------------
; Steady 2x field walk: four frames of 2 px make each 8-pixel tile step.
; Collision remains on the stock tile boundaries.
; ---------------------------------------------------------------------------

	if fast_walk

FastWalk_Init:
	move.w	#2, $FFFFD242.w
	rts

; Loading restores $D242 from the save's $D200 block. Raise an older on-foot
; value while preserving the vehicle speeds.
FastWalk_Restore:
	cmpi.w	#2, $FFFFD242.w
	bcc.s	+
	move.w	#2, $FFFFD242.w
+
	rts

; Called after loc_3036 increments the frame-within-step byte $C(a5).
; Return Z set at a tile boundary and keep the on-foot delta at 2 px.
FastWalk_UpdateStep:
	move.w	#2, $FFFFD242.w
	andi.b	#3, $C(a5)
	rts

; The manager runs before the visible party objects and leaves the current
; delta in $D242. Apply that same signed delta to every follower.
FastWalk_MoveFollowerX:
	move.b	(a0,d3.w), d1
	ext.w	d1
	muls.w	$FFFFD242.w, d1
	add.w	d1, $8(a5)
	rts
FastWalk_MoveFollowerY:
	move.b	$1(a0,d3.w), d1
	ext.w	d1
	muls.w	$FFFFD242.w, d1
	add.w	d1, $A(a5)
	rts

; d0.b = number of 8-pixel steps. Each takes four frames.
FastWalk_FramesForSteps:
	lsl.b	#2, d0
	rts

; d0.b is the demo entry's unit count and (a0) is its direction byte. Walking
; entries use four frames per step; pauses retain the stock 8-frame unit.
FastWalk_DemoFrames:
	tst.b	(a0)
	beq.s	FastWalk_DemoFrames_Pause
	bra.s	FastWalk_FramesForSteps
FastWalk_DemoFrames_Pause:
	lsl.b	#3, d0
	rts

; The dock sequence holds its direction for eight steps. $C(a5)=0 marks its
; first frame; thereafter it is a countdown. Return Z when all frames elapsed.
FastWalk_DockTick:
	tst.b	$C(a5)
	bne.s	+
	moveq	#8, d0
	bsr.s	FastWalk_FramesForSteps
	move.b	d0, $C(a5)
+
	subq.b	#1, $C(a5)
	rts

	endif
