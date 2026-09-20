# The text engine

What the game does with a string, and how the proportional dialogue face is
fitted onto it. Addresses are the US ROM's (`PSIII_Disasm/ps3.asm` labels).

## The stock renderer (`loc_10038`)

Every string in the game - script, shop prompts, battle messages, menu labels
- goes through one routine. It takes `a0` = text, `a1` = a row of a window
buffer in RAM, `d0` = tilemap attribute bits (`$8000` for priority), and the
window context at `a6` (`$FFFFD280`): `$42(a6)` the row stride in bytes,
`$44(a6)` the cells per line, `$1(a6)` flags (bit 4 = inside an inserted
string, bit 5 = more text waits after a page break), `$3E(a6)` the pointer to
that text.

Each character is one 8x8 tile of the font at VRAM `$0000` (`loc_66000`,
256 tiles, tile index = the text byte: ASCII at `$20-$7E`, digits also at
`$01-$0A`), written as a **word into the row below `a1`**; the row at `a1`
gets a blank tile. Two rows per line because the Japanese game drew the
dakuten and handakuten marks in the upper row (`$F4 nn` / `$F0 nn`, the
mark tiles at `$19-$1D` straddling two cells, table `loc_10226`). The
window buffers (`$FFFF9A80` the live dialogue box, `$FFFF9CF0` its
template, `$FFFF9BB8` a second box) are copied to plane A by `loc_FC58`.

Control bytes: `$F8` line break (pads the line with blanks, `a1 += 2 rows`),
`$EC` page (pads, sets bit 5 and `$3E(a6)`, returns), `$FC` end, `$E8 nn`
insert the string at `char_name_saved+nn` (recursive), `$E4 nn` print the
number at `$FFFFD4A0+nn` through `loc_FA16` (binary to BCD, no leading
zeros, `0` when zero).

The dialogue box is 26 tiles wide (24 text cells), 6 rows tall: border,
mark row, text, mark row, text, border - two lines. On `$EC` the main loop
(`loc_A368`) copies the lower line's two rows up (`loc_A3BA`) and renders
the continuation into the lower line, so a `{PAGE}` scrolls one line.

## The proportional face (`ext/vwf.asm`)

`VWFDia_Entry` is jumped to from the first instruction of `loc_10038`.
With `vwf_menu` enabled it first checks for a pooled field-menu position;
otherwise it takes over only when `$44(a6) == 24` and `a1` is one of the
dialogue's three text rows (`$FFFF9D26` template line 0, `$FFFF9AB6` live
line 0, `$FFFF9B1E` live line 1). Other calls jump back to the stock code.

For a line it ORs 1bpp glyph rows (`vwf/diafont.bin`, 8 bytes per text byte,
advance in `vwf/diawidth.bin` = ink + 1 px, space 3 px) into a 192-px canvas
(8 rows x 26 bytes, two spill bytes so a glyph at the last cell cannot run
into the next row), then at `$F8`/`$EC`/`$FC` **flushes**: expands the canvas
to 24 4bpp tiles (ink colour 1, paper 2, a 16-entry nibble table), copies
them to VRAM with the game's own `LoadDataInVRAMWithOffset` into the pool -
font tiles `$C0-$EF`, blank in the US font and never written by any art
loader (all map art loads at `$2000` and above) - and writes the window rows:
mark row all `$1F` (paper), glyph row the pool indices for the cells that
hold ink and `$1F` for the rest. Line 0 uses pool tiles `$C0-$D7`, line 1
`$D8-$EF`.

Control bytes follow the stock semantics, including the odd ones: `$F8` and
`$EC` inside an inserted string end the insert without acting. Glyphs that
would cross 192 px are dropped (the proofreader flags the line first).

The page scroll is the one place the stock copy is not enough: after
`loc_A3BA` moves line 1's words into line 0 they still point at line 1's
pool tiles, which the next page overwrites. `VWFDia_ScrollUp` (called in
place of `loc_A3BA`) also copies line 1's canvas into line 0's, re-expands
and re-uploads line 0's tiles and subtracts 24 from every copied pool index.

RAM: `$FFFFE400-$FFFFE8B7` - the SEGA-screen art buffer, used only at boot
(the Nemesis code table sits below at `$FFFFE000-$FFFFE1FF`, the stack above
`$FFFFFC00`). Two canvases, a 768-byte expansion scratch, and line state:
mode, pool tile, cell/pixel capacity, paper-padding width and ink-tile count.

Cost: one line is at most 24 glyphs of 8 OR-pairs plus a 768-byte expansion
and upload; well under a frame. The stock renderer is not otherwise touched,
and with `vwf_dialogue = 0` the hook is not assembled.

## The field menu

With `vwf_menu = 1` (and `vwf_dialogue = 1`), the same composer also handles
text drawn into the field menu's plane-A buffer. Menu maps are `$202-$20C`;
they load only five portrait slots at VRAM tiles `$100-$23F`, and leaving the
menu reloads the field map art. That leaves tiles `$240-$53F` free while the
menu is open, below the sprite table at tile `$540`.

The menu pool shadows the usable screen area instead of allocating tiles:
mark rows 0-23 and columns 4-35 map to `$240 + row*32 + (column-4)`. Redrawing
a cell therefore reuses its tile. Each call is clipped to the end of that row
and at most 24 cells, while the stock `$44(a6)` width still controls how many
cells are cleared with paper. A `{BR}` relocates the next line in the pool; if
it steps below row 24, the rest of the string is handed back to the stock
renderer.

This catches item names, equipped items, technique names, menu labels and the
"Whose?" name list. It also recognizes the five exact rows of the main menu's
10x12 staging buffer and maps them to their eventual screen positions. The
first cell stays fixed blank because the stock transition cleanup deliberately
leaves it alone; the remaining seven cells give each label 56 px, enough for
the full `Technique` (41 px) instead of the stock `Techniq`.

## The shops

A store screen is a map of the same kind (`$222-$230`, one per store type,
table `loc_BA1C`): the field art is reloaded on exit and the map itself loads
one picture at tiles `$101-$131`, so the same free range is available. With
`vwf_shop = 1` the three list windows take the pooled path: the buy list
(`loc_A9A2`, buffer `$FFFFA126`, five lines of 16 cells, stride `$48`) and the
two sell-list pages (`loc_AE86` / `loc_B1C8`, buffers `$FFFF9D30` and
`$FFFF9E80`, five lines of 11 cells, stride `$38`). `VWFShop_Table` gives each
list a pool line per list line at `$240-$2FD`, and the window animation
(`loc_FD3E`, `loc_FE3C`) copies the words to plane A as it does the stock
ones. The buy list writes the price with the digit renderer from cell 11
after the name, relative to the `a1` the name renderer returns - which is why
the engine leaves `a1` at the last line's mark row exactly as the stock
renderer does - so a name has 88 px on every list; the proofreader's item
budget stays the field menu's 80 px, the tighter of the two. The shop
prompts were already proportional (the dialogue rows).

Numeric fields still use the game's direct digit renderer, and the row-25
character name plate remains fixed width. The item window is 10 cells (80 px);
the longest translated-style names tested so far fit it. Cursor highlighting
continues to work because its palette-bit toggle changes the attributes on the
same pool-tile words.

## The opening scroll

The new-game scroll (`loc_1A156`, text `loc_1A33C`...) is a real vertical
scroller: plane A scrolls up and each line is written straight into VRAM by
`loc_F7F0` (text, column, plane row, attribute `$6000`) when its header row
comes around, four rows apart. `VWFScroll_Entry` hooks `loc_F7F0` when the
script offset is the new-game intro's (the same test the scroller uses to
pick its table) and the string is not the row-clearing blank, composes the
line with the dialogue routines and uploads it to a pool of 8 x 24 tiles at
`$200-$2BF` - on that screen plane B's picture uses `$100-$1FF` and
`$340-$413` - with slot (row/4) mod 8, which is reused 32 rows after it was
written when the line has long scrolled off the 28-row screen. Blank cells
get tile 0 (transparent) as the stock spaces did, and the tiles themselves
are expanded with a transparent paper (`VWFDia_ExpandOpen`): the stock font's
black paper is invisible on that screen, but tiles at `$200` drawn with the
same paper covered the picture with bars. With `vwf_scroll_shadow = 1` the
ink casts a one-pixel black shadow right and down (the expansion looks up
ink and shadow nibbles together in `VWFDia_ShadowLUT`), which keeps the
thinner face readable over the bright parts of the picture. The ending staff roll goes
through the same routine on another screen and keeps the bold 8x8 capitals.

## What the JP release does differently

* The JP font is kana only, 8x8, at ROM `$40000` (the US font is at
  `$66000`); the same tile layout for digits, punctuation, the frame pieces
  and the credits capitals.
* The script (`$25F0C`) and its control codes are the same. Twenty-five JP
  entries end in a text piece with no header after their `$FC`; the game
  never shows it and the US script folded it in.
* The battle background scroll tables (`loc_780C0`) give the ground rows
  (13-27) a speed that grows toward the viewer: 20/16 to 76/16 px per
  frame. The US tables zero those rows and share fewer of them. With
  `scrolling_ground = 1` the JP tables are assembled instead; the scroll
  routine (`loc_CF1E`) is identical in both games.
* The sound driver and music data (`$70343-$7711C`) and a small table at
  `$79308` differ; untouched here.
