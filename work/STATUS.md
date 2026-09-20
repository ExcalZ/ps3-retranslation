# PS3 Retranslation — Current Handoff

Updated: 2026-09-19

## State

The foundation is in place: the disassembly assembles the US ROM bit-exact,
every string is extracted into JSON with its Japanese counterpart, the JSON
is written back into the assembly by a generator whose round trip is
bit-exact and idempotent, the dialogue window draws a proportional face,
the three requested extras are in and verified, and the tests, the
proofreader and the release packaging exist. **The translation pass has
started** with the opening: the new-game scroll (`credits` segment, now
proportional: 16 lines of up to 192 px, from the JP scroll's 18 lines) and the
attract-mode / game-over story narration (`loc_25F24`, 8 proportional
pages). Everything else still equals the US text.

Canonical experimental ROM `ps3en.bin` (every option on): 791,922 bytes,
SHA-256 `A6BA353B496DBD924203976671418869293E0A22704E95DB8F394B2E7FDAA248`;
`tools/checkbuild.py` prints its SHA-256 after each build.
Stock US ROM (every option 0 and every `en` equal to `us` reproduces it -
verified 2026-09-19 after the menu-VWF work): 786,432 bytes, SHA-256
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
  (`VWFBattle_Table`). PS III has no enemy targeting - the earlier note that
  the enemy row's columns place a cursor was wrong. Verified under the
  interpreter and in BlastEm (`work/scripts/battlevwf.py`,
  `work/analysis/bv2_*.png`): the enemy row, the stat window's name through
  the command grids, the item list with its highlight, a round of combat.
  Consequence for the translation: item and technique names are budgeted
  at **72 px** (the battle lists' nine cells), enemy names 75 px, party
  names 40 px - `proofread.html` enforces it.

## Not done

* **Fixed-width leftovers.** The field menu's row-25 name plate, the
  "Whose?" name lists and the numbers; the game-select save list.
* **The translation itself**, and the glossary decisions
  (`work/glossary.md`).
* **Fonts for other languages**: only ASCII plus `" ; & %` glyphs exist.

## Verification checklist

```
python tools/sourcebuild.py ps3en.bin      # 0 errors, 0 warnings
python tools/checkbuild.py                 # build, placement and option invariants
python tools/test_text.py                  # 1180 US + 523 JP strings round-trip
python tools/test_vwf.py                   # 11 engine cases under the interpreter
python tools/test_techdist.py
python work/scripts/pagescroll.py          # BlastEm: 6 screenshots of the legend text scrolling
python work/scripts/narration.py           # BlastEm: the opening
python work/scripts/battle.py              # BlastEm: first encounter, scrolling ground, VWF messages
python work/scripts/saveslots.py           # BlastEm: inn save into slot 3, reset, continue
python work/scripts/saveslots2.py          # BlastEm: two saves, continue/erase lists
python work/scripts/menuvwf.py             # BlastEm: Item, Stats, Equip, Techs, Switch, generation 2
```

To reproduce the stock ROM: set every option in `ps3.options.asm` to 0 and
every `en` to its `us` (three `en` fields differ today: the two re-flowed
battle "won" messages and the save-position prompt),
`python tools/sourcebuild.py stock.bin`, compare with `PSIII_Disasm/ps3original.bin`.

`work/scripts/battle.py` leaves Landen through its real exit (`teleport`
with the door's own parameters, `$3818` - a bare teleport onto a world map
does not spawn the walking sprite) and wanders into the first encounter;
`battle_win.py` plays it out with C. Still to do in BlastEm: the church save.

## Log

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
