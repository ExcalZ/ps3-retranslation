# Phantasy Star III: English Retranslation — source and tools

Repository: https://github.com/ExcalZ/ps3-retranslation (no release yet - the
translation pass is in progress; see `work/STATUS.md`).

A new English translation of *Phantasy Star III: Generations of Doom*
(*Toki no Keishousha*, Mega Drive / Genesis), made from the Japanese script,
built as a **source patch on top of the game's disassembly** rather than by
editing the ROM — the same shape as the
[Phantasy Star IV retranslation](https://github.com/ExcalZ/ps4-retranslation).
The dialogue window, the field menu, the shop lists and the battle box draw
proportional (variable-width) text, a page of dialogue scrolls up smoothly
at the rate of the message-speed option, there are four save slots (one per third-generation branch), the Japanese release's
scrolling battle ground is restored, and the Technique Distributor no longer
runs off the screen at high levels.

This repository holds everything needed to rebuild the patch and to carry the
translation work forward:

* the script, as editable JSON with the Japanese, the 1991 US text and the new
  English side by side (`work/`);
* the text engine (`PSIII_Disasm/ext/vwf.asm`) and the other patches
  (`PSIII_Disasm/ext/`), each behind a flag in `PSIII_Disasm/ps3.options.asm`;
* the toolchain that extracts the text, writes the JSON back into the
  assembly, generates the font, checks budgets and invariants, assembles the
  ROM, tests it under an interpreter and under BlastEm, and packages the
  release (`tools/`);
* a proofreading editor that draws every line with the real fonts
  (`tools/proofread.html`).

No ROM is included. The build needs the stock US ROM at
`PSIII_Disasm/ps3original.bin` (768 KB plain binary); aligning the Japanese
script needs the JP ROM beside the repository root as
`Phantasy Star III - Toki no Keishousha (Japan).md`.

## Repository map

```
README.md              this file
docs/pipeline.md       how a build works, what each stage reads and writes
docs/engine.md         the game's text engine and how the VWF sits on it
work/STATUS.md         current state, what is done, what is next - read first
work/glossary.md       naming decisions and what the Japanese calls things
work/dialogue.json     the story script: 546 entries, JP / US / EN
work/script.json       names, menus, battle and shop text: 14 tables, 648 runs
PSIII_Disasm/          lory90's disassembly with the translation applied
PSIII_Disasm/ext/      the retranslation's code: vwf.asm, techdist.asm, saveslots.asm
PSIII_Disasm/vwf/      generated font binaries (diafont.bin, diawidth.bin)
tools/                 the toolchain (Python 3.10+, standard library only)
tools/md/              generic Mega Drive utilities (BPS, SMD, 68000 interpreter, BlastEm driver)
release/               release templates: readme_template.txt, patcher_template.html
```

## Building

```bash
python tools/sourcebuild.py ps3en.bin
```

writes the JSON into `ps3.asm` (`gentext.py`), assembles with Macro
Assembler AS (`PSIII_Disasm/AS/win32/asw.exe`, Windows), fixes the header
checksum and copies the ROM. Then:

```bash
python tools/checkbuild.py
python tools/test_text.py
python tools/test_vwf.py
python tools/test_techdist.py
```

With every option in `ps3.options.asm` at 0 the assembled ROM is
byte-identical to the US release (`work/STATUS.md` records the hashes).

## Editing the translation

Edit only the `en` fields. `hex`, `jp`, `us` and the addresses describe the
original and are what the generators key on.

* **Dialogue** lives in `work/dialogue.json`. `{BR}` starts the second line
  of the window, `{PAGE}` waits for a button and scrolls the window up one
  line, `{NAME:nn}` / `{NUM:nn}` are the engine's inserts. A line may be up
  to 192 px in the dialogue face; only the text before the first `{PAGE}` may
  contain a `{BR}`.
* **Names, menus, battle and shop text** live in `work/script.json`, one
  segment per table. Item and technique names use the proportional face with
  a 72 px budget (the battle lists; the menu allows 80 px and the shops 88),
  enemy names 75 px and party names 40 px. The five field main-menu labels
  use it too, with a 56 px budget after their fixed one-cell margin. Other
  non-dialogue windows remain fixed-width 8x8 cells unless the proofreader
  identifies them as proportional; the widest stock line is their budget.
* `tools/proofread.html` shows every line in the real fonts with live pixel
  widths and flags what does not fit. Open it in a browser and load a JSON
  (or serve the repository with `python -m http.server 8765` and open
  `http://localhost:8765/tools/proofread.html?file=work/dialogue.json`).

## Packaging a release

```bash
python tools/release.py 1.0
```

writes `release/PS3_Retranslation_v1.0/` (BPS, offline `Patcher.html` that
also accepts `.smd`, readme with every hash filled in) and zips it.

## Credits and legal

Translation, hacking and testing by **Excalibur_Z**, with Claude (Anthropic)
for translation and technical work. Built on lory90's Phantasy Star III
disassembly. Tooling, engines and documentation are MIT licensed (`LICENSE`);
third-party components and their terms are listed in `NOTICE.md`. Phantasy
Star III is copyright SEGA; this repository contains no ROM image and no right
to one.
