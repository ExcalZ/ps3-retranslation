# PS3 Retranslation — Current Handoff

Updated: 2026-09-19

## State

The foundation is in place: the disassembly assembles the US ROM bit-exact,
every string is extracted into JSON with its Japanese counterpart, the JSON
is written back into the assembly by a generator whose round trip is
bit-exact and idempotent, the dialogue window draws a proportional face,
the three requested extras are in and verified, and the tests, the
proofreader and the release packaging exist. **The translation pass has
started** with the opening: the title/new-game scroll (`credits` segment,
21 fixed-width lines of 24 cells, from the JP scroll's 18 lines) and the
attract-mode / game-over story narration (`loc_25F24`, 8 proportional
pages). Everything else still equals the US text.

Canonical experimental ROM `ps3en.bin` (every option on): 790,666 bytes;
`tools/checkbuild.py` prints its SHA-256 after each build.
Stock US ROM (every option 0 and every `en` equal to `us` reproduces it -
verified 2026-09-19 after the save-slot work): 786,432 bytes, SHA-256
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
  "Damage 2", "You have been defeated."). The enemy-name row stays fixed
  width: its columns place the target cursor. A battle message is two lines
  at most; the two three-line "won" messages are re-flowed in `en`. Not yet
  seen in BlastEm: shop prompts (same path as the dialogue's `$FFFF9AB6`).
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

## Not done

* **Menu / battle-list VWF.** Item, technique, enemy and status windows
  stay fixed-width. The PS4 project's pool-with-marks engine is the model;
  the PS3 VRAM has only the 64 blank font tiles free (`$C0-$FF`, 48 used by
  the dialogue), so a menu VWF would need to reclaim VRAM (the kana remnants
  at `$80-$95` are unused by US text but referenced from tilemap data would
  need checking) or draw names into the mark rows.
* **The translation itself**, and the glossary decisions
  (`work/glossary.md`).
* **Fonts for other languages**: only ASCII plus `" ; & %` glyphs exist.

## Verification checklist

```
python tools/sourcebuild.py ps3en.bin      # 0 errors, 0 warnings
python tools/checkbuild.py                 # 12 invariants
python tools/test_text.py                  # 1180 US + 523 JP strings round-trip
python tools/test_vwf.py                   # 6 engine cases under the interpreter
python tools/test_techdist.py
python work/scripts/pagescroll.py          # BlastEm: 6 screenshots of the legend text scrolling
python work/scripts/narration.py           # BlastEm: the opening
python work/scripts/battle.py              # BlastEm: first encounter, scrolling ground, VWF messages
python work/scripts/saveslots.py           # BlastEm: inn save into slot 3, reset, continue
python work/scripts/saveslots2.py          # BlastEm: two saves, continue/erase lists
```

To reproduce the stock ROM: set every option in `ps3.options.asm` to 0 and
every `en` to its `us` (three `en` fields differ today: the two re-flowed
battle "won" messages and the save-position prompt),
`python tools/sourcebuild.py stock.bin`, compare with `PSIII_Disasm/ps3original.bin`.

`work/scripts/battle.py` leaves Landen through its real exit (`teleport`
with the door's own parameters, `$3818` - a bare teleport onto a world map
does not spawn the walking sprite) and wanders into the first encounter;
`battle_win.py` plays it out with C. Still to do in BlastEm: a shop purchase
and the church save.

## Log

* 2026-09-19 (later) - Translation started: opening scroll and attract
  narration, both seen in BlastEm (`work/scripts/narration.py`, `attract.py`).
  The scroll keeps the US line count because each line carries its own
  position header; the JP has 18 lines plus a "1000 years ago" heading.

* 2026-09-19 - Project started from the PS4 retranslation's shape. Read the
  text engine, found the JP script at `$25F0C` with the same structure,
  aligned it through the NPC tables. Built the generator and proved the
  round trip. Found the JP scroll tables, the Technique Distributor overflow
  mechanism (one cell per point, rows written past the `$E00` plane buffer),
  and free VRAM/RAM for the VWF. Wrote the engine; the interpreter test
  caught the `{NUM}` truncation. BlastEm harness runs scenarios from
  power-on (no savestates), which the `four_save_slots` work can reuse.
