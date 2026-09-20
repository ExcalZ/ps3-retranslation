; ---------------------------------------------------------------------------
; Build options for the Phantasy Star III retranslation.
; 0 = assemble the stock US behaviour, 1 = the modification. With every option
; at 0 the assembled ROM is byte-identical to the US release.
; ---------------------------------------------------------------------------

; Restore the scrolling battle ground of the Japanese release (per-row scroll
; speed tables at loc_780C0).
scrolling_ground = 1

; The party walks twice as fast on foot: 2 px a frame, four frames a step
; instead of 1 px and eight (vehicles keep their speeds). The walking
; animation runs at its stock pace; the scripted walks (demo input, the dock)
; count steps, so cutscenes cover the same ground.
fast_walk = 1

; Four save slots instead of two. The two extra slots (and their backup copies)
; live in the second 16 KB of backup RAM, so the header declares 32 KB.
four_save_slots = 1

; Keep the Technique Distributor's cost/level box inside the window when a
; character's level is high (the stock game writes past the window buffer).
fix_tech_distributor = 1

; Proportional (variable-width) text in the dialogue window, the battle message
; row and the opening scroll.
vwf_dialogue = 1

; The opening scroll's letters cast a one-pixel black shadow (0: plain letters
; over the picture, as the stock scroll draws them).
vwf_scroll_shadow = 1

; Proportional text in the field menu too: item names, equipment, technique
; names and labels (needs vwf_dialogue; the pool is VRAM tiles $240-$53F,
; free while a menu screen is up).
vwf_menu = 1

; Proportional item names in the shops' buy and sell lists (needs vwf_dialogue).
vwf_shop = 1

; Proportional text in the battle box: the enemy-group row, the character
; names of the stat window and the item and technique lists (needs vwf_dialogue).
vwf_battle = 1

; A page advance in the dialogue window scrolls the text up smoothly, one
; 16-px line, at a rate set by the "message scrolling speed" option (needs
; vwf_dialogue). 0: the stock one-step page change.
smooth_scroll = 1
