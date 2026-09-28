# PS3 Retranslation — Current Handoff

Updated: 2026-09-27

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

Canonical experimental ROM `ps3en.bin` (every option on): 827,664 bytes,
SHA-256 `0EDA75F7C976E372AEA2A2ABE7B1DDA6A6BCBD924C82F54940967DDEADC26D8A`;
`tools/checkbuild.py` prints its SHA-256 after each build.
Stock US ROM (every option 0 and every `en` equal to `us` reproduces it -
verified 2026-09-20 after the translation pass): 786,432 bytes, SHA-256
`CB837A2B10B8D219D844A55D8EC25581A57152F5EE8361AB62389354170A21D5`, CRC32
`C6B42B0F`, internal checksum `3A33`.

## Done

* **Maia kidnapping escort (2026-09-27).** The 2x walk modifier shortened
  Rhys's demo input while Maia and the guards followed one-pixel, eight-frame
  paths. Scripted demo walks now keep that stock cadence through the final tile
  step, then restore 2x field movement. The pre-wedding BlastEm slot reaches
  the Landen prison cell entrance at `(752, 432)`; the old build stopped at
  `(912, 528)`. `work/scripts/kidnapping.py` checks the route and speed reset.

* **Full dialogue pointer audit (2026-09-25).** All 546 compiled dialogue
  entries match `work/dialogue.json`, all 144 conditional redirects land on
  entry boundaries in the same script bank, and all 513 active script word
  pointers match their assembled values. The ending event at `loc_305FE` now
  selects a full offset and `MainGame_GameScript` clears the bank on exit.
  `checkbuild.py` scans word-sized source references for future overflow;
  `test_scriptbank.py` checks the emitted ROM. The largest raw NPC pointer is
  `loc_30330` at `$F9D0` from `GameScript` ($630 bytes below the limit).
  The unbanked event at `loc_304DA` is `$FC46` ($3BA below the limit).

* **Wren transformation dialogue (2026-09-25).** The translated script put
  `loc_3075A` and `loc_30780` beyond the 16-bit offset range. The word
  addition in the transformation scene wrapped `loc_30780` to `$0040`, whose
  text bytes redirected to Yaata's old man. The scene now computes the full
  offset and clears the bank after loading each message. The user's slot 8
  shows the wrapped offset; `test_scriptbank.py` checks all six choices.

* **Ending transmission (2026-09-24).** The animation could cue the final
  transmission while translated dialogue was still running; the dialogue
  loader then cleared that cue on return. A pending flag now carries the cue
  into the transmission phase. Luin's six lines were observed in BlastEm in
  three pairs, followed by the normal scene exit; the first pair of each of
  the other three endings also appeared. `namestrings` now uses the proportional
  face and has per-line JP attribution from the source ROM.

* **Late sage dialogue offsets (2026-09-23).** The translated script passes
  64 KB from `GameScript` in the space scenes. The New Mota sages' scene table
  stored word offsets, so the second sage wrapped to the opening text and the
  fourth could read invalid script data. `extended_script` uses a full-offset
  table for those scenes and a high-word-aware script resolver. The user's
  BlastEm slot 3 reaches the correct Palma history text; all five scene
  indices, including the fourth, reached their intended text pointers without
  crashing. `tools/test_scriptbank.py` and `checkbuild.py` guard the boundary.

* **Fixed Technique records and cast names (2026-09-20–21).** The translation had expanded the
  24 fixed 16-byte `TechniqueData` records. Molmos's hard-coded enemy Foie ID
  (`$48`) consequently landed one byte before `Tech_Megido`, displayed Megid,
  and dispatched invalid effect data into a hard reset. The stock gameplay
  records are fixed-width again; translated names now live in the parallel
  `TechniqueNameData` table and are remapped only for rendering, including
  the `$E8` inserts used by enemy/party "used" messages. Build invariants
  cover both table strides, and the interpreter regression checks all six
  enemy Technique IDs (`$48`-`$5C`), including Molmos's Foie lookup and
  Rappy's Gra-to-Gravt announcement.

* **Extraction.** `work/dialogue.json`: 546 script entries (14 header-only
  redirects), 542 paired with the JP script - 365 through NPC-table anchors
  and flag-branch targets, the rest by order between anchors; 4 US entries
  have no separate JP entry (two share the preceding JP source), and 4 JP
  entries are unpaired (`jp_unmatched` in the JSON). Four JP script entries
  carry an unheadered continuation after `{END}`; the following ending table
  is separate. `work/script.json`: 14 tables,
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
  the box and cursor are drawn with a common fractional scale that fills up
  to 24x14 cells. Opposing displayed arms sum to a fixed width or height, so
  the border does not jump when a point moves; the old outline is cleared
  before redraw. In the user's 2026-09-27
  slot 0, Laia's raw 17x16 graph used to shrink to 8x7; it is now 14x14,
  with no leftover tiles after Up/Down.
  That exact stock state would overlap the lower window but stay inside the
  plane buffer. Verified in BlastEm with 20/20/20/20 (a 40x40 box in
  the stock game, which runs off the plane buffer into the scroll tables and
  plane B) and under the interpreter (`tools/test_techdist.py`). Its four
  technique-name rows are also in `VWFShop_Table` at tiles `$352-$371`;
  without that mapping, Mieu's translated `Sun Force` exceeded the stock
  eight-character row and deliberately entered the renderer's bounds trap.
  `VWFList_Find` preserves `d7`, as stock `loc_10038` does: `loc_C8F4` keeps
  its four-name loop counter there, so clobbering it made only the first row
  (for example Sun Force or Law) render. Verified with the user's copied
  battery save/state and a full four-row interpreter test (`test_techdist.py`).
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
  get a pool line each at `$240-$2FD` (`VWFShop_Table`). The same table now
  gives the five-row vendor party list four-cell lines at `$300-$313`, the
  four-row game-select/church list proportional pool lines at `$322-$351`,
  and the Technique Distributor four eight-cell lines at `$352-$371`. Found
  on the way:
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
  from `$B986`): the pools use `$364-$37F`, the inactive sprite-table tail
  `$554-$55F`, the window plane's never-shown rows 0-18 (`$580-$5CB`), and
  its offscreen rows 28-31 (`$5F0-$5FF`). The earlier `$25C-$27F` list pool
  overlapped background art used in Lune's battle. The enemy-group lines, the stat
  window's character names (four cells each, spaced five cells apart; the
  fifth position is the right border), the item / technique lists and `loc_CFCC`'s centre equipped-
  weapon slot at `$FFFF2A20` get pool lines there (`VWFBattle_Table`). The
  missing centre row made `Knight's Sword` enter the fixed renderer's bounds
  trap when manual Attack was confirmed. Targeting does not touch those cells (the earlier
  note that the enemy row's columns place a cursor was wrong): an enemy
  target is the enemy's own sprite lit up, an ally target the character's
  name in the stat window. Verified under the interpreter and in BlastEm
  (`work/scripts/battlevwf.py`, `work/analysis/bv2_*.png`): the enemy row,
  the stat window's name through the command grids, attack targeting over
  three Chirpers with the weapon name shown, the item list with its
  highlight, a round of combat. The user's Lune slot 1 captures ally
  targeting; the name highlight covers four cells after the border fix.
  Consequence for the translation: item and technique names are budgeted
  at **72 px** (the battle lists' nine cells), enemy names 75 px, party
  names 32 px in battle (40 px on menu plates). The current party names fit
  the battle width; `proofread.html` also checks the menu budget.

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
* **Faster transitions** (`fast_transitions`): the seven-level palette ramps
  used by map and menu changes now dwell two frames per level instead of four,
  reducing ordinary fades from 29 to 15 frames without skipping loading work.
* **Stale input** (`fix_stale_input`): a frame whose VBlank skips the pad
  read carries no new presses, so a slow redraw cannot replay a tap.
* **Left targets back** (`battle_target_left`): in a battle target picker
  (Technique, item, Defend) Left steps to the previous target; the other directions step forward as before.
* **Technique confirm guard** (`fix_technique_confirm`): A/C is ignored for
  the first eight frames after the character-to-list handoff, preventing a
  rapid double-tap on Mieu from immediately selecting Sun Force. B and the
  directional buttons remain responsive.
* **Fast walk** (`fast_walk`): steady 2x on foot; every intact 8-px
  collision step takes four frames of 2 px. Followers share the live delta,
  the animation keeps its pace and scripted walks count the same steps
  (`docs/engine.md`). The cadence is asserted in BlastEm and the harness can
  compare endpoints against a `fast_walk = 0` build (`work/scripts/walkspeed.py`).
* **Harness.** RAM snapshots resume Landen in five seconds
  (`boot_to_field`); `save_state` presses BlastEm's save-state key for
  VRAM audits; the interpreter's `jsr (An)` mask was wrong (never matched).

## Not done

* **Proofreading in play.** The translation has been checked against the
  budgets (`tools/linecheck.py`: 0 problems) and the user has started
  playing it; `work/scripts/dialogue_check.py` points a Landen NPC at any
  entry and screenshots every page for reading a scene at a time.
* Three restored header-only lines (`loc_261F8`, `loc_261FC`, `loc_26200`)
  are reached only through flag `$16` (the Nial branch); seen in BlastEm with
  the flag forced (`work/analysis/f16_*.png`). On the wedding day the Landen
  townspeople repeat two lines (`us_2619E`, `us_261CA` and their copies at
  `loc_26F9C`...`loc_27330`): that is the JP script - the US localization
  varied them.
* The ending transmission (`namestrings`) keeps the US line counts (14/14/
  14/6 per ending) with the JP text re-flowed; the JP's shorter blocks are
  padded with blank lines. Every displayed line now carries its JP source.
* **Fixed-width leftovers** (`work/scripts/fixedaudit.py` lists them): the
  message-speed prompt, the numbers everywhere, and the staff roll (by design).
  The ending transmission is proportional. The four-row game-select/church save list now
  has four proportional 12-cell pool lines at `$322-$351`.
* **Fonts for other languages**: only ASCII plus `" ; & %` and `Ä ä` glyphs
  exist (the umlauts on the stock font's unused kana tiles `$80`/`$81`,
  `ps3text.US_ENCODE`; the fixed 8x8 face has no glyph for them).

## Verification checklist

```
python tools/sourcebuild.py ps3en.bin      # 0 errors, 0 warnings
python tools/checkbuild.py                 # build, placement and option invariants
python tools/test_text.py                  # 1180 US + 523 JP strings round-trip
python tools/test_vwf.py                   # 11 engine cases under the interpreter
python tools/test_battle.py                # battle music restore and enemy Star Force result setup
python tools/test_techdist.py
python tools/linecheck.py                  # every en string against its budget
python work/scripts/pagescroll.py          # BlastEm: 6 screenshots of the legend text scrolling
python work/scripts/narration.py           # BlastEm: the opening
python work/scripts/battle.py              # BlastEm: first encounter, scrolling ground, VWF messages
python work/scripts/saveslots.py           # BlastEm: inn save into slot 3, reset, continue
python work/scripts/saveslots2.py          # BlastEm: two saves, continue/erase lists
python work/scripts/menuvwf.py             # BlastEm: Item, Stats, Equip, Techs, Switch, generation 2
python work/scripts/prompts.py             # BlastEm: the indented What?/Use prompts, Equip's What?
python work/scripts/menuinput.py            # BlastEm: Technique double-tap confirm guard
python work/scripts/victory.py             # BlastEm: a won battle, the victory and level-up messages
python work/scripts/walkspeed.py ps3en.bin [slow.bin]  # BlastEm: the fast walk vs a fast_walk = 0 build
```

To reproduce the stock ROM: set every option in `ps3.options.asm` to 0,
every `en` to its `us` and drop the credits' `hdr_en` fields (a script that
does so in both JSON files, builds and restores them; the JSON files are
CRLF),
`python tools/sourcebuild.py stock.bin`, compare with `PSIII_Disasm/ps3original.bin`.

`work/scripts/battle.py` leaves Landen through its real exit (`teleport`
with the door's own parameters, `$3818` - a bare teleport onto a world map
does not spawn the walking sprite) and wanders into the first encounter;
`battle_win.py` plays it out with C. The church save list has now been
exercised with the user's copied SRAM (`user-save-church-vwf.png`).

## Log

* 2026-09-24 (Technique target cursor) - In the user's slot 6 one Right or
  Left tap moved the ally-target cursor up to three names (0 -> 3 -> 1 -> 4).
  Each step redraws the battle box proportionally, and that redraw writes
  VRAM across a VBlank. VBlank skips the pad read while `$FFFFD006` bit 6
  is set but still releases the main loop, so routine `$D8` saw the same
  pressed byte again and stepped again. `fix_stale_input` clears both pads'
  pressed bytes when VBlank skips the read; the held bytes stay, so a press
  begun during a skipped frame still registers later. Replaying slot 6 on the
  13:50 build (`work/scripts/techtarget.py`, which must run that ROM: the state
  holds its layout) moves one name per tap with the fix emulated at the
  VBlank branch; `test_battle.py` runs the new VBlank for both skip causes.
  The stock pickers also stepped forward for any direction; with
  `battle_target_left` Left steps back (`BattleTarget_Prev`, `ext/battlefix.asm`,
  hooked into the Technique picker `$D8`, the item picker `$64` and Defend's
  ally picker `$144`): it tries
  the indices below the current one and keeps the first that the stock
  validator `loc_107BE` returns unchanged. Target types are even (the jump
  table has 4-byte entries); 2/6 one ally, 8/`$A` one enemy, `$C`/`$E` one of
  two groups; the rest keep the stock step. `test_battle.py` runs routine
  `$D8` on slot 6's RAM (Left 0-4-3-2-1-0, Right/Up/Down forward) and the
  enemy search over missing slots, and Defend's `$144`/`$148` pair the same
  way. The user confirmed the fix in play (2026-09-24).
  `emu68k.py`'s `tst.w (xxx).w` now sets N. Build SHA-256:
  `28260D3AD0644DBD0D78D0DFB9F11EE17022B606BE65FBA830C75649FE054A1E`.

* 2026-09-24 (Dark Falz battle crash) - The boss battle uses map `$3B2`,
  but the proportional battle renderer recognized only `$232`. Its fixed
  fallback exhausted the four-cell stat slot while drawing Searren and hit
  the stock overflow trap. The boss map now uses the battle font pools; its
  graphics and UI layout leave those VRAM ranges free. Forcing the special
  encounter from the user's sage field state reproduced the trap at frame
  592 before the change, then ran through 1,200 frames of battle without an
  exception afterward. `test_vwf.py` covers the `$3B2` stat-name path;
  `gentext.py --check` and `checkbuild.py` pass. Build SHA-256:
  `386360AA83E878D0D9E94230E76A235AE84CA00323965CE810224830D7F0A843`.

* 2026-09-24 (Neo Madder art) - BlastEm slot 4 captured a broken Neo Madder
  in battle. Extension code and the translated Technique-name table had been
  inserted inside its compressed art stream at `loc_8D57C`. They now live
  with the other extension code after the stock ROM's `$C0000` boundary.
  The full `$61A0`-byte art block through `loc_9371C` matches the stock ROM
  byte for byte; `checkbuild.py` enforces that and checks the moved labels.
  A fresh build passes `gentext.py --check`, `checkbuild.py`, the text, VWF,
  battle, script-bank, and technique-distributor tests, and `linecheck.py`.
  The captured state retains its already corrupted VRAM; a new encounter
  is needed to see the repaired art. Build SHA-256:
  `51D4DDD02689EA49FC7B568FE72250648183B506A59BF021B560529059C39B3B`.

* 2026-09-22 (Luin Party-menu crash) - The seventh-generation menu uses map
  `$20E`, but `VWFDia_Entry` recognized only `$202-$20C`. Its translated
  labels fell through to the fixed renderer and the menu transition hit
  `ErrorTrap`. The range now includes `$20E`. A BlastEm fixture reproduced
  the reset before the change, then opened the three-member Party menu and
  Switch without an exception after it (`work/scripts/luinmenu.py`).
  `test_vwf.py` checks all seven menu maps; `checkbuild.py` passes. Build
  SHA-256: `D6E4FB41C1CFCC6E0F400162D9598E869A96ED36A73EA646E2DAE42D2FC0AB40`.

* 2026-09-22 (text and walk cadence) - The latest dialogue and script JSON
  edits are generated into the assembly. Field walking now uses a steady
  2 px per frame (2x), so camera scrolling advances evenly. BlastEm confirms
  the 2 px cadence and scripted walk endpoints match a stock-speed build.

* 2026-09-22 (Satera castle music follow-up) - The latest user save state
  (`slot_9.state`, map `$3E`) has `$95` in the 68K music cache but no active
  Z80 music tracks. The fast battle exit was queuing a Z80 fade (`$E0`) and
  then `$95`; the fade can outlive or outrank the restore and eventually stop
  all tracks. In fast-transition builds, battle exit now lets the battle
  music continue through the short visual fade and directly replaces it with
  the saved field theme. Three Satera exit cycles and one full victory in
  BlastEm all returned to map `$3E` with `$95` queued, zero pending fade, and
  10 active music tracks after four more seconds. `test_battle.py` covers
  the no-fade exit. Build SHA-256:
  `19525EC1F6D98D93FF6E407926D0A8D35A2EFD3F86B467CE08242CE82A479FFC`.

* 2026-09-22 (castle battle music follow-up) - The prior fallback used the
  map header's `+$4` entrance command, which is `$00` or `$FF` in castles,
  so it could still restore silence. Battle entry now falls back to the
  header's `+$6` field theme (`$9F` in Landen Castle, `$95` in Shusoran
  Castle) whenever the cached sound queue is not a music ID. Focused tests
  cover both castles, fade/stop/SFX commands, and the post-fade cache restore.
  A full BlastEm Shusoran Castle encounter, with the pre-battle cache forced
  to `$E0`, won and returned to map `$44` with `$95` queued for playback.
  Built with `--no-gen` and 0 errors/warnings; build SHA-256:
  `7E424C04B234C4140452599E71607F583992519AEBDBD42DFFB85517B31CBB40`.
  `test_battle.py`, `test_vwf.py`, and `test_text.py` pass. `checkbuild.py`
  currently reports 9 generated-text ranges out of sync; its other checks
  pass. The generated text was left untouched during this music fix.

* 2026-09-22 (battle music and enemy Star Force) - Battle entry no longer
  treats a cached fade/stop command as the field music to restore; it saves a
  real `$81-$AF` music ID or falls back to the current map's declared track.
  Enemy Star Force now reads its allied target's name pointer from the enemy
  battle object at `+$34`, rather than parsing arbitrary object state at
  `+$27` as an inserted string (the cause of the `196A1200` execute crash).
  `test_battle.py` covers both layouts. The full suite passes and a BlastEm
  victory returned cleanly to the field. Build SHA-256:
  `194EB118F735D3F755758E792AAEA2800237C122D778E9D241C1137F0EBCDB48`.

* 2026-09-22 (Lune battle background) - The battle list font pool no longer
  uploads into `$25C-$27F`: Lune's inherited scrolling ground uses part of
  that tile range, exposing Star Force glyphs in its lower rows. All battle
  list, stat, and enemy-name pools now occupy disjoint VRAM outside the
  background art and active tilemaps. `checkbuild.py` enforces these ranges;
  `test_vwf.py` renders every list row and checks the background tiles stay
  unchanged. Build SHA-256:
  `d063fa3f6319e61ce16415ee9c3f65fd912609899510a12e8909536c8b1f43c3`.

* 2026-09-23 (Laia's battle border) - The fifth tile beside Laia is the
  battle box's right border (`$8898`), not a name cell. The previous change
  incorrectly cleared it to `$801F` and let the selection highlight alter
  its palette (`$A898` in slot 1). The stat-name renderer and highlight now
  cover only four cells. `Battle_WriteCharStats` also restores the border
  during redraw so the user's older slot 2 state can recover its blank tile.
  `test_vwf.py` seeds the fifth tile and verifies name rendering preserves it;
  a direct replay of slot 2 changed `$801F` to `$8898` at `$FFFF2ABC`.
  The ROM builds with zero errors or warnings. Build SHA-256:
  `47d4833490be16464a8c6ac2186e90c9ee83644d57a19aa6919efb97209a18c7`.

* 2026-09-21 (vendor party names) - Searren advances 33 px only because its
  final `n` includes a one-pixel trailing gap; the actual ink ends at pixel 31
  and fits the stock four cells. The renderer now bounds the ink separately
  and caps the pen at the edge, so it emits four tiles and leaves the vendor
  frame cell untouched. This removes both the stray `L` formerly borrowed
  from Lyle's pool line and the blank fifth tile that displaced part of the
  frame. Verified against the user's `slot_4.state` and in `test_vwf.py`.

* 2026-09-21 (transition/input/walk tuning) - ordinary map and menu fades now
  take 15 frames instead of 29, the Technique list has an eight-frame A/C
  guard against an accidental character-selection double-tap, "To Whom?" is
  spaced correctly, and field walking was tuned to 1.5x from 1.75x.

* 2026-09-20 (original 1.75x walk and proportional save names; walk cadence
  subsequently tuned to 1.5x) - `fast_walk` used a seven-step/32-frame cycle.
  Followers use the same live delta; demo walks
  and the dock compute their frame counts from the phase. The BlastEm harness
  asserts the exact cadence and matched scripted endpoints against a
  `fast_walk = 0` build. With the copied battery save, holding Up into map
  `$E6`'s altar wall for 80 frames left `(312,312)` unchanged. The shared
  game-select/church save list (`$FFFF9C9E`) now has four proportional pool
  lines (currently `$322-$351`); `Kein LV2` was seen in both paths
  (`user-save-gamesel-vwf.png`, `user-save-church-vwf.png`). The copied save
  loaded with intact sprites and
  tiles; its original was not modified. Stock reproduction remains
  byte-identical.

* 2026-09-20 (map `$E6` collision report) - The user's screenshot is the
  legal bottom-right boundary at player coordinates `(368,328)`: after accounting
  for its 3 px window crop, it matches the isolated replay at that boundary in
  99.1% of sampled pixels. Holding right and down for another 91 and 81 frames
  left the coordinates unchanged at x=368 / y=328, both with the save's restored
  speed 1 and the then-current fast-walk speed 2. The visible torso overlap is the
  stock feet-anchored collision perspective, not wall penetration. A real adjacent
  load issue was fixed: `$FFFFD242` is part of the saved `$D200` block, so an
  older save overwrote `fast_walk`'s speed. Save restore now raises values below 2
  to 2 while preserving the Aerojet's speed 4. Verified against the copied battery
  save; its original files were not modified (`work/analysis/user-save-fixed-collision.png`).

* 2026-09-20 (battery-save compatibility) - A save made by the previous
  translated build retained absolute ROM pointers in its character records;
  the item-name edits moved their targets 24 bytes, so the player's field
  sprite descriptor read `$FFFF` and wrapped through unrelated tiles. After
  `loc_148FA` restores a save, `VWFSave_RestorePointers` now refreshes all five
  sprite descriptors and relocates the saved EXP / technique-growth pointers.
  The user's copied battery save boots on map `$E6` with sprite attribute `$44C0`
  instead of `$FFFF` (`work/analysis/user-save-fixed.png`). Covered by the
  interpreter and verified with a byte-identical stock build.

* 2026-09-20 (latest, item names) - Fibrilla for Fiblira, the Protector
  series back to "Protector" where it fits (the user's rule for names past
  72 px: drop the space first, then an unpronounced letter -
  MaximaProtector, Laconia Protectr), Ärmel for Emel with Ä/ä added to the
  proportional face (`vwfmixed.py`, bytes `$80`/`$81` in `ps3text.py`,
  `diafont.py` and the proofreader). Seen in BlastEm (`work/analysis/
  um_items.png`).

* 2026-09-20 (later; subsequently tuned to 1.5x) - From play: the field
  walk was initially twice as fast (`fast_walk`; the animation and scripted
  walks unchanged in effect),
  the Equip screen's hand-written `What?` renders through the pool, a
  pooled line's leading spaces are whole cells (Item's `What?` and its
  Use/Give/Discard list sat one cell left of the header and left a fragment
  of the `W` behind), and the victory / level-up messages (`$FFFF2A0A`, two
  lines) are proportional. `test_vwf.py` covers the last two; BlastEm
  (`prompts.py`, `victory.py`, `walkspeed.py`, `menuvwf.py`) the rest. The
  harness runs BlastEm on a copy of the ROM with its own empty save file:
  the user's saved game had made `boot_to_field` choose Continue. The three
  flag-`$16` lines were checked with the flag forced; the repeated
  wedding-day lines are the JP's own. Stock reproduction byte-identical.

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
