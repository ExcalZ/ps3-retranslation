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

This catches item names, equipped items, technique names and menu labels. On
a pooled line the spaces before the first ink are whole 8-px cells: the stock
prompts indent with spaces (`"  What?"` at column 15, `" Use"` at 16) so that
the text lines up with the window's header at column 17, and a 3-px space
would pull it left and leave ink in a cell the later redraws (which start one
cell to the right) never clear. The Equip screen's `What?` was six tile words
written by hand at `$FFFF2322`; it now renders the same `"  What?"` string
as the Item screen. It also recognizes the five exact rows of the main menu's 10x12 staging buffer
and maps them to their eventual screen positions. The first cell stays fixed
blank because the stock transition cleanup deliberately leaves it alone; the
remaining seven cells give each label 56 px, enough for the full `Technique`
(41 px) instead of the stock `Techniq`.

The party status boxes are window buffers too (six 10x13-cell buffers at
`loc_1F592`, copied to the plane at `loc_1F5AA`); the name plate is the only
text the renderer draws in them. `VWFMenu_Locate_Box` maps a buffer cell to
its screen cell. A box in the lower row (plane row 14) puts its plate's mark
row at 24, just below the pool, so that row maps to `$580 + column` - the
window plane's first nametable row, which no menu screen shows (the smooth
scroll uses the same tiles on dialogue screens). A plate gets five cells
(40 px, the party-name budget) so its level digits stay untouched; the
cursor's palette toggle already spans the plate's eight words.

A submenu's header used to be five words *copied* from the selected label's
rows (`loc_9E74`). Copied pool words point at the label row's shadow tiles,
which the next prompt drawn over that row rewrites - "Who?" left the header
reading "Who? ique". `VWFMenu_Header` renders the label's text into the
header instead (seven cells, the window's interior). The Stats screen's
`MES` was three tile words written by hand at `$FFFF2520`; it now renders the
shops' "Meseta" string through the pool.

## The smooth page scroll

The stock page advance (`loc_A368`) copies line 1's words into line 0 and
draws the new line whole; the "message scrolling speed" option (1-9,
`TextScrollSpeedValues`: 136 down to 8 frames) is only a dwell time - how
long a battle message or an unattended cutscene page stays before the next.
With `smooth_scroll = 1` the advance is animated. `VWFSmooth_Begin` composes
the next page into a third canvas without drawing it (the renderer is told
to defer: it still updates the continuation state), reads the option and,
over the following frames (`VWFSmooth_Tick`, hooked at the top of
`loc_A368`, where it freezes the page counter), shows the box's 32-px
interior as a window sliding down a 48-px stack of blank, line 0, blank,
line 1, blank, line 2: each frame the view is rebuilt from the canvases at
the pixel offset, expanded to 96 tiles and uploaded to `$580-$5DF`, with the
four interior rows of the window pointing at those tiles. At 16 px the
canvases are promoted and both lines are drawn the ordinary way on the
dialogue pool, pixel-identical to the last frame, and the window is copied
as the stock code copies it. Rates: 1/4, 3/8, 1/2, 3/4, 1, 1.5, 2, 3 and
4 px per frame for speeds 1-9 (64 down to 4 frames a line).

A button press pays out two lines: `loc_A368` counts them in `$D(a6)` at
every wrap of its 8-frame counter `$C(a6)`, and in the stock game that
counter was the whole pacing. With the animation it would leave the box
still for 8 frames between the two scrolls, so `VWFSmooth_Finish` checks
`$D(a6)` and the more-text flag itself and starts the second line the frame
the first completes (the counter still runs its 8 frames after the last
line before the button is read again, as stock).

The dwell of an unattended page (bit 7 of `$FFFFD286`: the attract-mode and
game-over narration, cutscene pages, battle messages) was `$20(a6)` frames
on the byte `$21(a6)` whatever the page held, and the translation's lines
carry nearly twice the text of the US lines. `VWFDwell_Tick` (hooked at
`loc_A30E`) counts on a word instead and scales the dwell by the ink of the
two lines on show (`VWFDia_Xs`): `$20(a6)` frames up to 240 px, a US-density
page, proportionally more beyond it - a battle message or a short page keeps
the stock timing, a full two-line page waits about half as long again.

## Party names longer than four letters

The initial stats records (`MieuInitStatsData`...) hold each name in a
four-letter field that `InitCharStats` copies verbatim into the character
record (`$27(a0)`, `$03` + four letters + `$FC`) - every US name has four
letters for that reason, and "Searren" or "Shiin" would shift the words after
the field and crash `SetMainCharStatsPtr` on an odd address. With
`vwf_dialogue` a record holds `$E0 nn, $FC` instead, and `VWFName_Table` in
`ps3.asm` (the `charnames` segment) holds the names at any length. Both
renderers expand `$E0 nn`: the proportional one inline, glyph by glyph
(`VWFDia_LongName`; not as a nested insert, since a name is normally reached
through `{NAME:nn}` already and the insert flag is one bit deep), and the
stock one through `VWFName_Fixed`, jumped to from its control table (`$E0`
lands right after the table, where the stock code fell through into the
`{NAME}` handler), which restores the insert flag afterwards. Saved games
carry the `$E0 nn` bytes in the record, so a save made with the option on
shows the long names too. The battle stat window's five cells (40 px)
remain the budget.

The 96 tiles are the window plane's nametable rows 0-18 (`$B000-$B97F`):
the window plane is off on every screen with the dialogue box (the field,
the world map, the shops, the narration screens - `work/scripts/
vramstates.py` audited them), so nothing reads or writes them there; in
battle the box lives on that plane, and battle messages are one line and
do not page. The state words live in the SEGA-screen art buffer, which is
not zero after boot, so a message's first line clears them.

## The shops

A store screen is a map of the same kind (`$222-$230`, one per store type,
table `loc_BA1C`): the field art is reloaded on exit and the map itself loads
one picture at tiles `$101-$131`, so the same free range is available. With
`vwf_shop = 1` the three list windows take the pooled path: the buy list
(`loc_A9A2`, buffer `$FFFFA126`, five lines of 16 cells, stride `$48`) and the
two sell-list pages (`loc_AE86` / `loc_B1C8`, buffers `$FFFF9D30` and
`$FFFF9E80`, five lines of 11 cells, stride `$38`). `VWFShop_Table` gives each
list a pool line per list line at `$240-$2FD` - and, since the party names
grew past four letters, the "Who will carry it?" name list (`$FFFF9C8E`,
four cells: Searren's ink ends exactly at 32 px), the Buy/Sell - Yes/No
window (`$FFFF9BC6`, one string whose `{BR}` line is found through the same
table: `VWFDia_List` remembers the table a line came from) and the Meseta
label (`$FFFF9C22`, six cells of pool ahead of the amount at cell 6) at
`$300-$321` - and the window animation
(`loc_FD3E`, `loc_FE3C`) copies the words to plane A as it does the stock
ones. The buy list writes the price with the digit renderer from cell 11
after the name, relative to the `a1` the name renderer returns - which is why
the engine leaves `a1` at the last line's mark row exactly as the stock
renderer does - so a name has 88 px on every list; the proofreader's item
budget stays the field menu's 80 px, the tighter of the two. The shop
prompts were already proportional (the dialogue rows).

## The battle box

The battle screen (`map_id` `$232`) loads its art itself: the shared
background tileset at `$2000-$4B7F` (380 tiles, every terrain draws from it),
the box art and effects from the map descriptor at `$5000-$6C7F`, enemy art
into slots at `$7000`, `$7400`, `$7800` and `$9000` (an enemy is up to 115
tiles, so the whole of `$7000-$A7FF` is theirs), the sprite table at `$A800`
and a per-line scroll table at `$AC00`. The box is drawn on the **window
plane** at `$B000`, but only from its row 19 (`loc_FC4E` copies to `$B986`)
and the window is shown from row 20, so the plane's rows 0-18 - `$B000-$B97F`,
tiles `$580-$5CB` - are never written or displayed. With `vwf_battle = 1`
those 76 tiles and the two gaps `$25C-$27F` and `$364-$37F` hold the pools of
`VWFBattle_Table`: the four enemy-group lines (`{NAME} {NUM}` from
`loc_DDDA` into the box buffer, 11 cells each), the five character names of
the stat window (`Battle_WriteCharStats`, plane A row 20, five cells apart,
so a name may now be five cells rather than the stock four - the highlight
in `loc_D56C` is widened to match) and the five item / technique list
entries (`loc_3D8AE` positions, nine cells, `$44(a6) = 9`). Targeting does
not touch the enemy row's cells: an enemy target is the enemy's own sprite
lit up, an ally target the character's name in the stat window (the
`loc_D56C` palette toggle, widened to five cells); the list highlights
toggle the same way. The battle message row was already on the dialogue
pool, and the victory and level-up messages (`loc_ED2C`, `loc_EEF4`), which
`loc_CF52` clears the whole box for and draws from its top row `$FFFF2A0A`,
take the same path as two dialogue lines (the US "won" message had three;
the translation re-flows it into two).

The battle list's nine cells make **72 px the item and technique name budget
game-wide**; the enemy line leaves 75 px for a name beside a two-digit
count, and the stat window 40 px for a party member's name.

Numeric fields still use the game's direct digit renderer, and the row-25
character name plate remains fixed width. The item window is 10 cells (80 px);
the longest translated-style names tested so far fit it. Cursor highlighting
continues to work because its palette-bit toggle changes the attributes on the
same pool-tile words.

Choosing a technique's ally target costs more than choosing an item's: every
direction press re-enters `loc_E712`, which redraws the whole stat window
(`loc_CF52`, `loc_CF72`, `loc_FF30`) as the first display did, and with the
proportional names that is up to four composed lines, each uploaded to VRAM.
That frame can overrun into the next vertical interrupt. The interrupt skips
`ReadJoypads` while bit 6 of `$FFFFD006` says a VRAM copy is in progress,
but it still sets the frame flag, so the main loop runs again at once with
the old `joypad_pressed` byte and moves the target a second time - and that
frame overruns too. `fix_input_repeat` clears the pressed bytes on the
skipping path (`VBlank_NoInput`); `joypad_held` is untouched, so the next
read still reports a press made in between. The stock game has the same
hole, only its frames rarely reach it.

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

## The party's step (`fast_walk`)

On foot the sprite manager (`Obj_CharSpriteManager`) moves the party
`$FFFFD242` px a frame - 1, set at `loc_2DE0`; the vehicles set 2 or 4 for
themselves - for the eight frames its counter `$C(a5)` runs (`loc_3036`,
`andi.b #7`), one 8-px tile a step. The visible party sprites (`loc_4C42`)
move 1 px a frame from `loc_4E4A` while the manager's stepping bit is set and
pick their walking frame from their own free-running frame counter (`$22(a5)
= ($C(a5) >> 2) & 6`). With `fast_walk = 1` the step is 2 px a frame over
four frames and the sprites move 2 px too, so a step is still one tile and
the animation, counting frames, keeps its pace. Two scripted walks count
frames and are scaled to match: the demo-script player `loc_11CE8` (an
entry's count is steps; `<< 2` instead of `<< 3`, a pause keeps its 8-frame
unit) and the dock's eight steps onto the boat (`loc_1993A`, 32 frames
instead of 64). The other demo-mode objects wait on positions or on their
own timers without walking. Verified in BlastEm (`work/scripts/walkspeed.py`)
against a `fast_walk = 0` build: `Demo_LandenWalkToPrison` run from the town
ends every entry on the same tile, the field walk is 2 px a frame with the
animation frame changing every eighth frame in both.

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
