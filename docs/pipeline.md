# The build pipeline, and how to retarget it

The working reference for anyone changing text, fonts or engine code here.
The current state and checklist are in [`../work/STATUS.md`](../work/STATUS.md);
the engine itself is described in [`engine.md`](engine.md).

## 1. Shape of the build

There is no ROM patching. The game is assembled from source
(`PSIII_Disasm/ps3.asm` and what it includes) by Macro Assembler AS, and the
translation reaches the source through one generator, `tools/gentext.py`,
which rewrites the text runs of the assembly in place from the two JSON
files. Running the build twice with unchanged JSON produces the identical
ROM, and with every option in `ps3.options.asm` at 0 the ROM is
byte-identical to the US release.

```
work/dialogue.json --gentext.py--> the GameScript region of ps3.asm (546 entries)
work/script.json   --gentext.py--> 14 labelled segments of ps3.asm (648 runs)
tools/vwfmixed.py  --diafont.py--> PSIII_Disasm/vwf/diafont.bin, diawidth.bin
tools/proofread_template.html + the font binaries --proofsync.py--> tools/proofread.html
```

`tools/sourcebuild.py` runs `gentext.py`, then the assembler (`asw.exe` and
`ps3p2bin.exe` from `PSIII_Disasm/AS/win32/`), fixes the Mega Drive header
checksum and copies the ROM to the path you name (default `ps3en.bin`).
`build.bat` still works too but its `fixheader` step needs the working
directory on PATH; `sourcebuild.py` does the checksum in Python.

The options in `ps3.options.asm`:

| flag | effect |
|---|---|
| `scrolling_ground` | the JP per-row scroll tables for the battle background (`loc_780C0`) |
| `fix_input_repeat` | when the vertical interrupt skips the joypad read (a VRAM copy in progress, `VBlank`), it clears the "pressed" bytes instead of leaving the last frame's standing, so an overrunning frame cannot act on one press twice |
| `fix_tech_distributor` | the distribution box is drawn from values scaled to fit 24x14 cells (`ext/techdist.asm`) |
| `vwf_dialogue` | proportional text in the dialogue window (`ext/vwf.asm`) |
| `vwf_scroll_shadow` | the opening scroll's letters cast a 1 px black shadow (0 = plain letters like the stock scroll) |
| `vwf_menu` | proportional item, equipment, technique and label text in the field menu; requires `vwf_dialogue` (`ext/vwf.asm`) |
| `vwf_shop` | proportional item names in the shops' buy and sell lists; requires `vwf_dialogue` (`ext/vwf.asm`) |
| `vwf_battle` | proportional enemy-group row, stat-window names and item / technique lists in the battle box; requires `vwf_dialogue` (`ext/vwf.asm`) |
| `smooth_scroll` | a page advance in the dialogue window scrolls the text up smoothly at the rate of the "message scrolling speed" option; requires `vwf_dialogue` (`ext/vwf.asm`) |
| `four_save_slots` | four save slots with safety copies in 32 KB of backup RAM (`ext/saveslots.asm`) |
| `fast_walk` | the party walks twice as fast on foot: 2 px a frame, four frames a step (`loc_2DE0`, `loc_3036`, the party sprites at `loc_4C42`); the walking animation keeps its pace, and the scripted walks (the demo-script player `loc_11CE8`, the dock's `loc_1993A`) count steps, so cutscenes end on the same tiles (`work/scripts/walkspeed.py` compares against a `fast_walk = 0` build) |

New code lives in `PSIII_Disasm/ext/*.asm`, included just before `EndOfRom`,
so it sits past the original 768 KB and nothing in the original image moves
(the hooks in `ps3.asm` are `jmp`/`jsr` into it). `checkbuild.py` asserts
this.

## 2. Extraction (done once, re-runnable)

* `tools/extract_script.py` reads the assembler listing (`ps3.lst`) for the
  US script - every entry keeps its label, its flag-branch target and its
  bytes from the ROM - walks the JP ROM's script structurally and aligns
  the two: NPC-table anchors (the level NPC tables are identical between
  regions, so each NPC's script offset pairs a US entry with a JP one),
  then flag-branch targets, then order within each gap. 542 of 546 entries
  are matched; the four unmatched on each side (the wedding sequence the US
  restructured) are listed in the JSON. JP text pieces that follow an `$FC`
  with no header - unreachable in the JP game, folded into the previous
  entry by the US script - are appended to the JP text after an `{END}`.
* `tools/extract_text.py` reads the same listing for the other tables,
  each bounded by two labels; a run is a group of consecutive `dc.b` lines
  ending in `$FC`. The credits keep their two position bytes in `hdr`.
* `tools/extract_jp.py` fills `jp` for those tables from the JP ROM (name
  tables by index, party names by their stat records, menus behind their
  position bytes, battle and shop messages through explicit maps; JP-only
  lines go to `jp_extra`).

Without `--rebuild` the extractors keep existing `en` and `note` fields.

## 3. The JSON files

Both hold the **original bytes** (`hex`), the **Japanese** (`jp`), the
**1991 US text** (`us`) and the **translation** (`en`). Only `en` is edited.

| token | meaning |
|---|---|
| `{BR}` | `$F8` - the second line of the window |
| `{PAGE}` | `$EC` - wait for a button, scroll the window up one line, continue on the lower line |
| `{END}` | `$FC` - end of string (only meaningful inside JP text that carries an orphan continuation) |
| `{NAME:nn}` | `$E8 nn` - insert the string whose pointer is at `char_name_saved+nn` |
| `{NUM:nn}` | `$E4 nn` - insert the number at `$FFFFD4A0+nn` |
| `{III}` | the two tiles that draw the "III" of Alisa III |
| `{XX}` | any other raw byte |

Dialogue entries also carry `flags` (`chk set`: the event flag that redirects
the entry and the one it sets), `target` (the label it redirects to),
`header_only` (a redirect with no text) and `anchor` (paired through an NPC
table). The credits' `hdr` is the two position bytes of a scroll entry
(column, row) as the US placed it; an optional `hdr_en` places the
translation's entry elsewhere (the generator writes it in place of `hdr`;
a stock-reproduction build drops it along with the `en` texts). The
new-game scroll's 17 lines sit five rows apart (`$82 + 5k`) so they span the
same rows as the US text's 21 lines four apart, and the scroll ends with the
last line on screen as in the stock game rather than after a blank tail; the
scroller ends when its entry table is exhausted (the last entry's row,
`$E4`), whatever the entries hold.

A header-only entry is where the US emptied a line: its four header bytes are
followed directly by the next entry's header, so had the game ever reached it
the renderer would have read that header as text (`$FF` is not a control code
it knows). The JP has text at every one of them; giving such an entry an `en`
makes the generator emit the text (and an empty `en` removes it again), so
those lines are restored rather than left as dead redirects.

The pairing with the JP is by NPC-table anchors and, between anchors, by
order. Two places break the order: the US split the Dark Falz speech into one
entry fewer than the JP (from `loc_2F8D4` to `loc_2FDEC` the JP text of an
entry is the one shown at the *previous* index) and the escapipe "press Reset"
notice sits inside an `{END}` orphan (from `loc_30330` on, likewise). The
translation follows the game's actual sequence, not the paired `jp` field,
through that stretch.

Text edits go through `tools/applybatch.py batch.json [--script]`: a JSON
object of ids to new `en` strings, merged into the file (keeping its CRLF
endings) and checked against the budgets below at once. `tools/linecheck.py`
runs the same checks over everything (`--changed` for the translated entries
only, `--widths` to print each one's widest line).

## 4. Budgets

| text | limit | enforced by |
|---|---|---|
| dialogue line | 192 px in the dialogue face (24 cells); two lines, then one per `{PAGE}` | `proofread.html`; the engine clips |
| item name | 80 px in the field-menu face (10 cells) | `proofread.html`; the engine clips |
| field main-menu label | 56 px after its fixed one-cell margin (7 cells) | `proofread.html`; the engine clips |
| item and technique names | 72 px (the battle lists' nine cells; the menu allows 80, the shops 88) | `proofread.html` |
| enemy names | 75 px (the battle box's group line beside a two-digit count) | `proofread.html` |
| party names | 40 px (the battle stat window's five cells); the record field itself is four letters, so the names live in `VWFName_Table` (`$E0 nn`, see engine.md) | `proofread.html` |
| ending transmission (`namestrings`) | 24 cells, fixed-width: `loc_F7F0` writes each pair of lines straight into VRAM in the 8x8 font | `proofread.html`, `linecheck.py` |
| other menu-map windows (`menus`, `menus2`, `equip`) | proportional inside the stock cell budget (widest US line x 8 px); a `{BR}` moves to the next pool line | `proofread.html`, `linecheck.py` |
| fixed-width tables (`marriage`, `megido`, `title`, the game-select lists and speed prompt in `shops`) | the widest line of the stock table, in cells | `proofread.html` (`budget` per segment) |
| script region | it may grow freely: everything after it is label-relative | - |

The menu pool has more physical room on the left item column, but 80 px is
the item authoring limit: it preserves the stock two-column layout and the
existing 10-cell name box. The proofreader enforces that stricter limit.

The script region has no hard address ceiling: the disassembly is fully
label-relative (assembling it with the text regenerated is bit-exact), and
`checkbuild.py` verifies the header end and the extension's placement after
each build. What does move when the script grows is every address after it,
which only matters for savestates and for the addresses quoted in these
documents.

## 5. Verification

```
python tools/checkbuild.py       # JSON/asm sync, fonts, proofreader, header, RAM and pool placement
python tools/test_text.py        # every original string round-trips through the codec (US and JP)
python tools/test_vwf.py         # the VWF engine under the 68000 interpreter vs a reference composer
python tools/test_techdist.py    # the distribution-box scaling under the interpreter
python tools/linecheck.py        # every en string against its budget (the proofreader's rules, from the shell)
python tools/ps3emu.py ps3en.bin # boots the ROM in BlastEm and screenshots the title
python work/scripts/menuvwf.py   # Item, Stats, Equip, Techs, Switch and generation-2 menus
```

`tools/ps3emu.py` drives BlastEm from Python through its GDB stub - pad
injection at `ReadJoypad`, work-RAM reads, window screenshots, a `teleport`
that fakes a door transition and store entry by the shop-type flag - so a
scenario is a deterministic pad script from power-on (`work/scripts/`).
BlastEm keeps backup RAM per ROM file name, so the harness runs a copy of the
ROM (`work/states/harness/harness-<name>`) whose save file it removes first:
a scenario never meets the user's saved games on the game-select screen (the
boot would pick "Continue") and never overwrites them. A ROM built with other
options gets its own listing beside it (`<rom>.lst`) for the label lookups.

Snapshots make that fast: `boot_to_field` takes the 64 KB of work RAM and
the registers at the pad breakpoint once it reaches Landen (`snapshot`,
`work/states/landen-<romkey>.snap`) and on later runs puts them back into a
freshly started BlastEm at its first pad read (`resume`): the CPU returns
through the snapshot's own stack, a faked map transition makes the game
rebuild VRAM and the VDP from RAM, and a trampoline in the unused part of
BlastEm's ROM copy reloads the font block that only the game's start loads.
Five seconds instead of seventy. RAM holds ROM addresses, so a snapshot is
keyed by the ROM's hash and remade after any build that moves code (a text
change does). A snapshot must be taken on a map the field loop can reload -
not in a battle, a menu or a shop.

VRAM, which the stub cannot read, comes from BlastEm's own savestates:
`save_state(em, path)` posts the save-state key to BlastEm's window and
copies the file it writes (with the work RAM beside it), and
`tools/vramaudit.py` reads the nametables, the sprite table and the tile
data out of it and prints what is referenced and what is free. That is how
the menu, shop, battle and dialogue pools were placed (`work/scripts/
vramstates.py`).

## 6. Retargeting

The pipeline is language-agnostic up to the font. To translate into another
language: translate `en`, add glyphs to `tools/vwfmixed.py` (`_g(char, top,
rows...)`, at most 8x8), map the character in `tools/ps3text.py` (`US_ENCODE`)
and `tools/diafont.py` (`code`), rerun `diafont.py` and `proofsync.py`, build.
The dialogue engine reads glyphs by text byte, so any byte below `$E0` can be
a glyph; the stock 8x8 font (`loc_66000`) is what the fixed-width windows
draw and would need its own tile art for new letters.
