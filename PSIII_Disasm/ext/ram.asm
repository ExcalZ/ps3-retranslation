; ---------------------------------------------------------------------------
; RAM used by the retranslation's extensions. All of it lies in $FFFFE400-
; $FFFFFBFF, the SEGA-screen art buffer that only the boot screen touches
; (the Nemesis code table ends at $FFFFE1FF, the stack starts at $FFFFFE00).
; Included at the top of ps3.asm so the equates are known to both the hooks
; and the extension files.
; ---------------------------------------------------------------------------
VWFDia_RAM      = $FFFFE400
VWFDia_Canvas0  = VWFDia_RAM		; 8 rows x 26 bytes, 1bpp
VWFDia_Canvas1  = VWFDia_RAM+$D0
VWFDia_Scratch  = VWFDia_RAM+$1A0	; 24 tiles x 32 bytes, 4bpp
VWFDia_Line     = VWFDia_RAM+$4A0	; word: 0 or 1
VWFDia_X        = VWFDia_RAM+$4A2	; word: pen position in px
VWFDia_Attr     = VWFDia_RAM+$4A4	; word: tilemap attribute bits (d0 at entry)
VWFDia_Row      = VWFDia_RAM+$4A8	; long: mark-row pointer of the current line
VWFDia_Mode     = VWFDia_RAM+$4AC	; word: 0 dialogue (two lines, pool $C0), 1 menu (pool by screen cell)
VWFDia_Tile     = VWFDia_RAM+$4AE	; word: first pool tile of the current line
VWFDia_Cap      = VWFDia_RAM+$4B0	; word: canvas capacity of the line in cells (at most 24)
VWFDia_MaxPx    = VWFDia_RAM+$4B2	; word: the same in px (glyphs past it are dropped)
VWFDia_Pad      = VWFDia_RAM+$4B4	; word: cells the line fills with paper after the ink ($44(a6) for menus)
VWFDia_Count    = VWFDia_RAM+$4B6	; word: tiles to expand and upload
VWFDia_Skew     = VWFDia_RAM+$4B8	; word: bytes the entry moved a1 by (the main list's margin cell)
VWFDia_Xs       = VWFDia_RAM+$4BA	; 3 words: ink width in px of dialogue lines 0-2 (smooth_scroll)
VWFDia_RAM_End  = VWFDia_RAM+$4C0

; The smooth page scroll (smooth_scroll): a third line canvas, the 32-px view of
; the box interior, its 96 expanded tiles, and the animation state.
VWFSmooth_RAM     = $FFFFEA00
VWFSmooth_Canvas2 = VWFSmooth_RAM		; 8 rows x 26: the page being scrolled in
VWFSmooth_View    = VWFSmooth_RAM+$D0		; 32 rows x 26: the interior at the current offset
VWFSmooth_Scratch = VWFSmooth_RAM+$410	; 96 tiles x 32 bytes
VWFSmooth_Acc     = VWFSmooth_RAM+$1010	; word: scroll position in 1/8 px (0-128)
VWFSmooth_Rate    = VWFSmooth_RAM+$1012	; word: 1/8 px per frame
VWFSmooth_Active  = VWFSmooth_RAM+$1014	; word: a scroll is running
VWFSmooth_Defer   = VWFSmooth_RAM+$1016	; word: compose into canvas 2, write nothing
VWFSmooth_RAM_End = VWFSmooth_RAM+$1018

SaveSlots_RAM    = $FFFFE900
SaveSlots_Status = SaveSlots_RAM		; 4 words: 0 empty/bad, 4 fine (the $60(a6) values)
SaveSlots_Names  = SaveSlots_RAM+$10	; 4 x 10 bytes: name copied from the slot, $FC-terminated
SaveSlots_List   = SaveSlots_RAM+$40	; the four-row list text, up to $60 bytes
SaveSlots_RAM_End = SaveSlots_RAM+$A0
