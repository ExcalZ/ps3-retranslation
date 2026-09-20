# PS3 Retranslation — Current Handoff

Updated: 2026-09-20

## State

The foundation is in place: the disassembly assembles the US ROM bit-exact,
every string is extracted into JSON with its Japanese counterpart, the JSON
is written back into the assembly by a generator whose round trip is
bit-exact and idempotent, the dialogue window draws a proportional face,
the three requested extras are in and verified, and the tests, the
proofreader and the release packaging exist. **The first full translation
pass is done** (2026-09-20): all 546 dialogue entries from the JP (the three
without a JP counterpart keep their US text), the item, technique, enemy and
party-name tables, the shop and battle messages, the marriage menus, the
ending transmission and the opening scroll and narration. Naming follows
the Japanese throughout - the user's decision of 2026-09-19, recorded in
`work/glossary.md`. What remains is proofreading in play: only a handful of
lines have been seen on the console side so far (see the log).

Canonical experimental ROM `ps3en.bin` (every option on): 826,066 bytes,
SHA-256 `D8AE62DD48708B9A231D5D817E4AA03E2F3B01FB14D92E80FD980BE479B0438A`;
`tools/checkbuild.py` prints its SHA-256 after each build.
Stock US ROM (every option 0 and every `en` equal to `us` reproduces it -
verified 2026-09-20 after the translation pass): 786,432 bytes, SHA-256
`CB837A2B10B8D219D844A55D8EC25581A57152F5EE8361AB62389354170A21D5`, CRC32
`C6B42B0F`, internal checksum `3A33`.

## Done

* **Extraction.** `work/dialogue.json`: 546 script entries (14 header-only
  redirects), 542 paired with the JP script - 365 through NPC-table anchors
  and flag-branch targets, the rest by order between anchors; 4 US entries
  and 4 JP entries unpaired (the wedding sequence the US restructured;
  `jp_unmatched` in the JSON). 25 JP entries carry an orphan continuation
  (`{END}` marker) the JP game never shows. `work/script.json`: 14 tables,
  648 runs; 526 have JP text (`tools/extract_jp.py`).
* **Generator.** `tools/gentext.py` rewrites the runs in place from the
  JSON, checks entry counts, labels and flag bytes against the source,
  handles the `charset`-mapped credits and the assembler's 20-operand line
  limit. Unchanged JSON reproduces the US ROM byte for byte.
* **VWF dialogue** (`PSIII_Disasm/ext/vwf.asm`, `docs/engine.md`). Verified
  in BlastEm: field dialogue, the 25-page legend text through the page
  scroll, game-select messages; under the interpreter: `tools/test_vwf.py`
  (which found and fixed a register clobber that truncated `{NUM}` inserts
  to one digit); battle messages (`$FFFF2C0A`, the plane-A row the battle
  box uses) - seen in BlastEm ("You've been ambushed!", "Chirper attacks!",
  "Damage 2", "You have been defeated."). A battle message is two lines
  at most; the two three-line "won" messages are re-flowed in `en`. Shop
  prompts (same path as the dialogue's `$FFFF9AB6`) seen in BlastEm with the
  shop work below.
* **Field-menu VWF** (`vwf_menu`, `ext/vwf.asm`). Menu maps use a
  screen-shadowing pool at tiles `$240-$53F`, so item/equipment/technique
  names and labels render proportionally without allocation. Verified under
  the interpreter (item columns, palette attributes, padding, redraws,
  label line breaks, out-of-range hand-off and fixed fallbacks) and in BlastEm
  (`work/scripts/menuvwf.py`, `work/analysis/mv_*.png`): Item and action
  screens, all three Stats pages, Equip with a right-hand item and cursor
  movement, Techs with seeded levels, clean returns to the field, and the
  second-generation menu map `$204`. Switch uses an active Rhys/Mieu fixture;
  both cursor states, the committed reorder, object-slot mapping, and clean
  field return are verified. The main-menu staging buffer is also mapped into
  the pool: its cursor palette works, transitions clear cleanly, and the full
  41 px `Technique` replaces the stock `Techniq` abbreviation.
* **Scrolling battle ground** (`scrolling_ground`): the JP tables at
  `loc_780C0`. Data-only; the scroll routine is identical in both games.
  Verified in BlastEm: in a Landen-plain battle the row-20 scroll value
  advances 60/16 px per frame... i.e. 3 px/frame (`work/scripts/battle.py`).
* **Technique Distributor** (`fix_tech_distributor`, `ext/techdist.asm`):
  the box and cursor are drawn from values divided by the smallest k that
  fits 24x14 cells. Verified in BlastEm with 20/20/20/20 (a 40x40 box in
  the stock game, which runs off the plane buffer into the scroll tables and
  plane B) and under the interpreter (`tools/test_techdist.py`).
* **Four save slots** (`four_save_slots`, `ext/saveslots.asm`). Backup RAM
  is odd bytes at `$200001` in `$1000`-byte blocks; the stock game keeps two
  saves in blocks 0-1 and their safety copies in 2-3. Now blocks 0-3 are
  four saves and 4-7 the copies (header: 32 KB). The slot masks and the
  copy offset are patched in place (`loc_14984`, `loc_149F2`, `loc_148A0`,
  `loc_1488C`, `loc_11580`); the game select checks four slots in a loop
  with a status word per slot, the lists are four rows built by
  `SaveSlots_Gather` from one string, the cursor moves over four rows and
  skips empty slots where only a saved game may be chosen, and the messages
  about the chosen slot go through `SaveSlots_Select` ({NAME:00}/{NUM:00}/
  {NUM:08}). Verified in BlastEm (`work/scripts/saveslots.py`,
  `saveslots2.py`): save into slot 3 at the Landen inn, soft reset, "Saved
  game 3 is fine", continue; save into slot 1, the continue list (cursor
  1 -> 3 -> 1 skipping empties), erase slot 3, continue slot 1. Not yet
  exercised: the repair-from-copy path and the "every slot full" warning
  (both are the stock code with the new slot count).
* **Tooling.** `sourcebuild.py`, `checkbuild.py`, `ps3emu.py` (BlastEm
  harness: boot script, teleport, store entry, NPC talk, screenshots),
  `ps3harness.py` (interpreter), `proofread.html`, `release.py`.

* **Shop-list VWF** (`vwf_shop`, `ext/vwf.asm`). Store maps (`$222-$230`)
  load one picture at tiles `$101-$131`, so the buy list (`$FFFFA126`, 16
  cells) and the two sell-list pages (`$FFFF9D30`, `$FFFF9E80`, 11 cells)
  get a pool line each at `$240-$2FD` (`VWFShop_Table`). Found on the way:
  the buy list writes the price relative to the `a1` the name renderer
  returns, so the engine now restores `a1` to the stock convention (the last
  line's mark row) at exit, and `test_vwf.py` asserts it on every render.
  Verified under the interpreter (all three lists, off-line rows, the
  dialogue box on the same screen, the field map) and in BlastEm
  (`work/scripts/shopvwf.py`, `work/analysis/sv_*.png`): a weapon shop
  stocked with five long names - list, cursor, "who carries it", the
  purchase - and an eight-item sell inventory: page one, the NEXT marker,
  the cascaded page two, the offer and the sale; the field and the menu are
  clean afterwards.

* **Battle-box VWF** (`vwf_battle`, `ext/vwf.asm`). The battle screen's
  VRAM was mapped from its loaders (background `$100-$27B`, box art and
  effects `$280-$363`, enemies from `$380`, the box on the window plane
  from `$B986`): free are `$25C-$27F`, `$364-$37F` and the window plane's
  never-shown rows 0-18 (`$580-$5CB`). The enemy-group lines, the stat
  window's character names (five cells now, highlight widened at
  `loc_D56C`) and the item / technique lists get pool lines there
  (`VWFBattle_Table`). Targeting does not touch those cells (the earlier
  note that the enemy row's columns place a cursor was wrong): an enemy
  target is the enemy's own sprite lit up, an ally target the character's
  name in the stat window. Verified under the interpreter and in BlastEm
  (`work/scripts/battlevwf.py`, `work/analysis/bv2_*.png`): the enemy row,
  the stat window's name through the command grids, attack targeting over
  three Chirpers with the weapon name shown, the item list with its
  highlight, a round of combat. Not yet seen: ally targeting with two
  party members (the name highlight; its widening is the stock toggle over
  one more cell).
  Consequence for the translation: item and technique names are budgeted
  at **72 px** (the battle lists' nine cells), enemy names 75 px, party
  names 40 px - `proofread.html` enforces it.

* **Smooth page scroll** (`smooth_scroll`, `ext/vwf.asm`). The message-speed
  option was only a dwell time (battle messages, unattended cutscene pages;
  ordinary dialogue ignored it). Now a page advance scrolls the text up
  16 px at 1/4 to 4 px per frame by that option, on 96 tiles of the window
  plane's never-shown rows (`$580-$5DF`; `work/scripts/vramstates.py` +
  `tools/vramaudit.py` audited every dialogue screen through BlastEm
  savestates). Verified under the interpreter (`test_smooth_scroll`: the
  view at 0, 7 and 15 px against a reference, the settled lines, the page
  counter frozen and released, 4 frames at speed 9 and 64 at speed 1) and
  in BlastEm (`work/scripts/smoothscroll.py`, `work/analysis/ss2_*.png`):
  the legend text at speeds 5, 1 and 9, the box closing, the menu after.
  Found on the way: the state words sit in the SEGA-screen art buffer and
  are not zero after boot, so a message's first line clears them. And a
  hand-played run (`work/scripts/observe.py`: the stub attached, keyboard
  passed through, a state saved every ten seconds) reset the game after
  the king's speech: the page code runs inside the object loop, which keeps
  the current object in a5, and `VWFSmooth_Begin` clobbered a3-a5/d3-d7
  (the stock tail touches only d0-d2/d5-d7/a0-a2); the loop then jumped
  through my scratch pointer - an address error into the entry point, or a
  VDP data-port read, depending on timing. Begin now saves those registers;
  the scene replays cleanly from a pre-speech state (`replay16.py`).
* **Harness.** RAM snapshots resume Landen in five seconds
  (`boot_to_field`); `save_state` presses BlastEm's save-state key for
  VRAM audits; the interpreter's `jsr (An)` mask was wrong (never matched).

## Not done

* **Proofreading in play.** The translation has been checked against the
  budgets (`tools/linecheck.py`: 0 problems) and the user has started
  playing it; `work/scripts/dialogue_check.py` points a Landen NPC at any
  entry and screenshots every page for reading a scene at a time.
* Three restored header-only lines (`loc_261F8`, `loc_261FC`, `loc_26200`)
  are reached through flag `$16`, which the game sets in later generations;
  they have not been seen in play.
* The ending transmission (`namestrings`) keeps the US line counts (14/14/
  14/6 per ending) with the JP text re-flowed; the JP's shorter blocks are
  padded with blank lines, as the JP itself does.
* **Fixed-width leftovers** (`work/scripts/fixedaudit.py` lists them):
  the game-select save list (`1.{NAME} LV{NUM}`, 12 cells - leaders are at
  most five letters), the message-speed prompt, the numbers everywhere, the
  ending transmission and the staff roll (by design).
* **Fonts for other languages**: only ASCII plus `" ; & %` glyphs exist.

## Verification checklist

```
python tools/sourcebuild.py ps3en.bin      # 0 errors, 0 warnings
python tools/checkbuild.py                 # build, placement and option invariants
python tools/test_text.py                  # 1180 US + 523 JP strings round-trip
python tools/test_vwf.py                   # 11 engine cases under the interpreter
python tools/test_techdist.py
python tools/linecheck.py                  # every en string against its budget
python work/scripts/pagescroll.py          # BlastEm: 6 screenshots of the legend text scrolling
python work/scripts/narration.py           # BlastEm: the opening
python work/scripts/battle.py              # BlastEm: first encounter, scrolling ground, VWF messages
python work/scripts/saveslots.py           # BlastEm: inn save into slot 3, reset, continue
python work/scripts/saveslots2.py          # BlastEm: two saves, continue/erase lists
python work/scripts/menuvwf.py             # BlastEm: Item, Stats, Equip, Techs, Switch, generation 2
```

To reproduce the stock ROM: set every option in `ps3.options.asm` to 0,
every `en` to its `us` and drop the credits' `hdr_en` fields (a script that
does so in both JSON files, builds and restores them; the JSON files are
CRLF),
`python tools/sourcebuild.py stock.bin`, compare with `PSIII_Disasm/ps3original.bin`.

`work/scripts/battle.py` leaves Landen through its real exit (`teleport`
with the door's own parameters, `$3818` - a bare teleport onto a world map
does not spawn the walking sprite) and wanders into the first encounter;
`battle_win.py` plays it out with C. Still to do in BlastEm: the church save.

## Log

* 2026-09-20 (late) - The new-game scroll: the user's reflow, and its 17
  lines spaced five rows apart (`hdr_en`) so the text spans the US text's
  rows and no blank tail precedes the end; the scroller ends on its table's
  last row whatever the entries hold, which is why moving the `{00}` did
  nothing. Proofreader saves keep the file's line endings. Lines are still
  capped at 192 px: the scroll composes on the dialogue canvas (24 cells).

* 2026-09-20 (night) - The attract narration read too fast: the unattended
  dwell was a fixed `$20(a6)` frames per two lines, and the lines now hold
  twice the text. `VWFDwell_Tick` scales it by the two lines' ink width
  (`docs/engine.md`); pages of the narration went from ~3.2 s to ~5 s in
  BlastEm (`work/analysis/at*.png`). The narration's trailing `{PAGE}`, a US
  addition that scrolled the last line up alone, is gone (the JP has none).
  The proofreader previews the pooled menu windows proportionally now.

* 2026-09-20 (evening) - The user's first play notes: Buy/Sell, the
  character names, "MES", "Who?nique" and a cursor highlight. A BlastEm
  audit of the stock renderer's fixed entry (`work/scripts/fixedaudit.py`)
  listed every window still on the 8x8 path; now pooled: the party name
  plates in the field menu (a mapping of the six status-box buffers, with
  the row below the pool on `$580+`), the shop's name list, Buy/Sell -
  Yes/No and Meseta (`VWFShop_Table`; a `{BR}` in a list line now finds its
  second line in the same table), and the Stats screen's Meseta. The header
  of a submenu is rendered instead of copied - copied pool words pointed at
  the label row's tiles, which "Who?" then overwrote. `loc_9E8E` and the
  Stats label are `if vwf_menu` hooks in ps3.asm. The interpreter's
  addi/subi fast paths gained their N/C flags (a `bcs` after `subi.w` had
  never worked there). Seen in BlastEm (`work/scripts/smallwindows.py`,
  `work/analysis/sw_*.png`): Technique's "Who?" over a clean header, the
  plates, Switch, the shop's list, purchase and name list with its
  highlight; menu, shop and battle scenarios still pass; stock reproduction
  byte-identical.

* 2026-09-20 (later) - Two fixes from play. The party names: the initial
  stats records hold a four-letter name field copied verbatim, so the
  translated "Searren" and "Shiin" shifted the records and the game reset on
  reaching Landen (`SetMainCharStatsPtr`, odd address). The records now hold
  `$E0 nn` and the names live in `VWFName_Table` (the `charnames` segment,
  now 18 runs: Ain's record had escaped the extractor), expanded by both
  renderers (`docs/engine.md`). And the smooth scroll's second line of a
  page no longer waits for the stock 8-frame counter: `VWFSmooth_Finish`
  starts it the frame the first completes. Both under the interpreter
  (`test_long_names`, the chained case of `test_smooth_scroll`) and in
  BlastEm by RAM trace (the window's screenshots were blank all day):
  boot to Landen with 9 NPCs, the menu and battle scenarios through, the
  page advance 16 + 16 frames back to back. Stock reproduction byte-identical.

* 2026-09-20 - The translation pass: every dialogue entry, the tables, the
  shop/battle text and the ending transmission, from the JP, with the JP
  names (`work/glossary.md`). Found on the way: `gentext.py` skipped the
  header-only entries (US redirect targets with no text; the renderer would
  have read the next header as text), so it now emits their `en`; the
  `namestrings` segment is not `{NAME}` inserts but the ending transmission,
  fixed-width 24 cells (`loc_F7F0`), and the proofreader/linecheck treat it
  so; the technique names repeated in `menus` for the Techs screen are
  proportional (72 px); the JP/US pairing is shifted by one through the Dark
  Falz speech and after the escapipe notice (`docs/pipeline.md`); "Megid"
  being one byte shorter than "Megido" misaligned the code after
  `loc_A0EB` - an `even` follows it now. New tools: `applybatch.py`,
  `linecheck.py`, `work/scripts/dialogue_check.py`. Stock reproduction
  re-verified byte-identical.

* 2026-09-19 (later) - Translation started: opening scroll and attract
  narration, both seen in BlastEm (`work/scripts/narration.py`, `attract.py`).
  The scroll keeps the US entry count (22) because each entry carries its
  own position header; unused entries hold a space. Then the scroll got the
  proportional face too (`VWFScroll_Entry`, a rotating 8-line pool at
  `$200`); a first attempt also caught the scroller's row-clearing calls and
  overwrote the pool - the blank string now takes the stock path. Laya ->
  Laia (katakana ライア); the Scenery Recalled naming notes are in the glossary.

* 2026-09-19 - Project started from the PS4 retranslation's shape. Read the
  text engine, found the JP script at `$25F0C` with the same structure,
  aligned it through the NPC tables. Built the generator and proved the
  round trip. Found the JP scroll tables, the Technique Distributor overflow
  mechanism (one cell per point, rows written past the `$E00` plane buffer),
  and free VRAM/RAM for the VWF. Wrote the engine; the interpreter test
  caught the `{NUM}` truncation. BlastEm harness runs scenarios from
  power-on (no savestates), which the `four_save_slots` work can reuse.
