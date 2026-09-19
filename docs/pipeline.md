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
| `fix_tech_distributor` | the distribution box is drawn from values scaled to fit 24x14 cells (`ext/techdist.asm`) |
| `vwf_dialogue` | proportional text in the dialogue window (`ext/vwf.asm`) |
| `vwf_scroll_shadow` | the opening scroll's letters cast a 1 px black shadow (0 = plain letters like the stock scroll) |
| `four_save_slots` | four save slots with safety copies in 32 KB of backup RAM (`ext/saveslots.asm`) |

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
table). The credits' `hdr` is the two position bytes the generator keeps.

## 4. Budgets

| text | limit | enforced by |
|---|---|---|
| dialogue line | 192 px in the dialogue face (24 cells); two lines, then one per `{PAGE}` | `proofread.html`; the engine clips |
| fixed-width tables | the widest line of the stock table, in cells | `proofread.html` (`budget` per segment) |
| script region | it may grow freely: everything after it is label-relative | - |

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
python tools/ps3emu.py ps3en.bin # boots the ROM in BlastEm and screenshots the title
```

`tools/ps3emu.py` drives BlastEm from Python through its GDB stub - pad
injection at `ReadJoypad`, work-RAM reads, window screenshots, a `teleport`
that fakes a door transition and store entry by the shop-type flag - so a
scenario is a deterministic pad script from power-on (`work/scripts/`).

## 6. Retargeting

The pipeline is language-agnostic up to the font. To translate into another
language: translate `en`, add glyphs to `tools/vwfmixed.py` (`_g(char, top,
rows...)`, at most 8x8), map the character in `tools/ps3text.py` (`US_ENCODE`)
and `tools/diafont.py` (`code`), rerun `diafont.py` and `proofsync.py`, build.
The dialogue engine reads glyphs by text byte, so any byte below `$E0` can be
a glyph; the stock 8x8 font (`loc_66000`) is what the fixed-width windows
draw and would need its own tile art for new letters.
