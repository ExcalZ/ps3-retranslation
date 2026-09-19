; ---------------------------------------------------------------------------
; Build options for the Phantasy Star III retranslation.
; 0 = assemble the stock US behaviour, 1 = the modification. With every option
; at 0 the assembled ROM is byte-identical to the US release.
; ---------------------------------------------------------------------------

; Restore the scrolling battle ground of the Japanese release (per-row scroll
; speed tables at loc_780C0).
scrolling_ground = 1

; Four save slots instead of two. The two extra slots (and their backup copies)
; live in the second 16 KB of backup RAM, so the header declares 32 KB.
four_save_slots = 1

; Keep the Technique Distributor's cost/level box inside the window when a
; character's level is high (the stock game writes past the window buffer).
fix_tech_distributor = 1

; Proportional (variable-width) text in the dialogue window.
vwf_dialogue = 0
