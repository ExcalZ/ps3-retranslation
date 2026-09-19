# PS3 Retranslation — Current Handoff

Updated: 2026-09-19

## State

The foundation is in place: the disassembly assembles the US ROM bit-exact,
every string is extracted into JSON with its Japanese counterpart, the JSON
is written back into the assembly by a generator whose round trip is
bit-exact and idempotent, the dialogue window draws a proportional face,
two of the three requested fixes are in and verified, and the tests, the
proofreader and the release packaging exist. **No line has been translated
yet**: every `en` equals the US text. The translation pass is the next job.

Canonical experimental ROM `ps3en.bin` (all options on except
`four_save_slots`): 789,632 bytes; the SHA-256 is printed by
`tools/checkbuild.py` and recorded in the git log of each build.
Stock US ROM (every option 0 reproduces it): 786,432 bytes, SHA-256
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
* **Tooling.** `sourcebuild.py`, `checkbuild.py`, `ps3emu.py` (BlastEm
  harness: boot script, teleport, store entry, NPC talk, screenshots),
  `ps3harness.py` (interpreter), `proofread.html`, `release.py`.

## Not done

* **Four save slots** (`four_save_slots`, reserved). The analysis:
  - Backup RAM is `$200001-$203FFF` (odd bytes, 16 KB): four `$1000`-byte
    blocks. Slots 0-1 are the two saves, blocks 2-3 their backup copies
    (`loc_149F2` copies `slot -> slot+2` after every save; the game select
    repairs a slot from its copy). Each block is nearly full (`loc_14A4A`
    table: `$28-$FFF`), so four slots with copies need 32 KB of SRAM
    (header `$200001-$207FFF`; emulators and flash carts size SRAM from the
    header), or four slots without copies in 16 KB.
  - Low-level sites: `loc_14984` (`andi.w #1` -> `#3`), `loc_149F2`
    (`andi.w #3` -> `#7`, copy to `slot+4`), `loc_148A0` (`st $2002(a0)`
    -> `$4002(a0)`), `loc_11580` (repair from `slot+2` -> `+4`), the
    header's backup RAM end.
  - UI sites: the game-select state machine (`EnterGameSelect`,
    `loc_1133C` table, ~100 states) checks slots `$1A(a6)` = 0, 1 and packs
    the results into `$5E/$60/$62(a6)` with `bchg #2` arithmetic; the slot
    list window `loc_3DB64` (two rows at (12,10)) and its cursor code
    (`addq #4; andi #4` in `loc_117E8`, `loc_118E2`); `loc_11B88` reads the
    two slots' names and levels into `$64(a6)`/`$6C(a6)` (the context has no
    room for four - `$74-$7E` are in use); the church save flow
    (`loc_C448`-`loc_C5A2`) uses the same window and `$1C(a6)` = slot*4;
    the strings "position 1 or 2", "1./2." rows (`shops` segment 44-68).
  - Estimate: ~300 lines of assembly plus new strings and window params;
    test through `ps3emu.py` by entering the church (store type 6/7) with
    `four_save_slots=1`.
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
```

To reproduce the stock ROM: set every option in `ps3.options.asm` to 0,
`python tools/sourcebuild.py stock.bin`, compare with `PSIII_Disasm/ps3original.bin`.

`work/scripts/battle.py` leaves Landen through its real exit (`teleport`
with the door's own parameters, `$3818` - a bare teleport onto a world map
does not spawn the walking sprite) and wanders into the first encounter;
`battle_win.py` plays it out with C. Still to do in BlastEm: a shop purchase
and the church save.

## Log

* 2026-09-19 - Project started from the PS4 retranslation's shape. Read the
  text engine, found the JP script at `$25F0C` with the same structure,
  aligned it through the NPC tables. Built the generator and proved the
  round trip. Found the JP scroll tables, the Technique Distributor overflow
  mechanism (one cell per point, rows written past the `$E00` plane buffer),
  and free VRAM/RAM for the VWF. Wrote the engine; the interpreter test
  caught the `{NUM}` truncation. BlastEm harness runs scenarios from
  power-on (no savestates), which the `four_save_slots` work can reuse.
