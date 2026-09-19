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
VWFDia_RAM_End  = VWFDia_RAM+$4AC

SaveSlots_RAM    = $FFFFE900
SaveSlots_Status = SaveSlots_RAM		; 4 words: 0 empty/bad, 4 fine (the $60(a6) values)
SaveSlots_Names  = SaveSlots_RAM+$10	; 4 x 10 bytes: name copied from the slot, $FC-terminated
SaveSlots_List   = SaveSlots_RAM+$40	; the four-row list text, up to $60 bytes
SaveSlots_RAM_End = SaveSlots_RAM+$A0
