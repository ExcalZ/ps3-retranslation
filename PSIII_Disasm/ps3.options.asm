; ---------------------------------------------------------------------------
; Build options for the Phantasy Star III retranslation.
; 0 = assemble the stock US behaviour, 1 = the modification. With every option
; at 0 the assembled ROM is byte-identical to the US release.
; ---------------------------------------------------------------------------

; Restore the scrolling battle ground of the Japanese release (per-row scroll
; speed tables at loc_780C0).
scrolling_ground = 1

; Halve the dwell between palette levels during screen fades. All seven
; brightness levels are retained; only the duplicated frames are reduced.
fast_transitions = 1

; The party walks at a steady 2x speed on foot: 2 px per frame, with each
; 8-px step kept intact for collision (vehicles keep their speeds). The walking
; animation runs at its stock pace. Scripted demo walks retain stock speed so
; Rhys stays in step with other actors; the dock keeps its step count.
fast_walk = 1

; Ignore confirm presses for the first eight frames after a character's
; Technique list opens, so a rapid double-tap cannot select its first entry.
fix_technique_confirm = 1

; A frame whose VBlank skips the pad read (VRAM being written, as the
; proportional redraws often are) carries no new presses, instead of the
; previous frame's again: one tap moves a target cursor one step.
fix_stale_input = 1

; Left in a battle target picker (a Technique's, an item's or Defend's target)
; steps back to the previous target; the stock game steps forward for any
; direction.
battle_target_left = 1

; Four save slots instead of two. The two extra slots (and their backup copies)
; live in the second 16 KB of backup RAM, so the header declares 32 KB.
four_save_slots = 1

; Use the "Successors of Time" title subtitle art and put a space between
; STAR and III in the title-screen caption.
successors_title = 1

; Keep the Technique Distributor's cost/level box inside the window when a
; character's level is high (the stock game writes past the window buffer).
fix_tech_distributor = 1

; Let late dialogue address more than 64 KB from GameScript. The original
; 16-bit script offsets wrap after translation expands the final scenes.
extended_script = 1

; Preserve each ending transmission cue when its animation reaches that point
; before the translated dialogue has finished.
fix_ending_transmission = 1

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
