================================================================================

  PHANTASY STAR III: GENERATIONS OF DOOM
  English Retranslation

  Version @VERSION@
  Release Date: @DATE@

  Author: Excalibur_Z
  Platform: Sega Genesis / Mega Drive

================================================================================


--------------------------------------------------------------------------------
  1. ABOUT THIS PATCH
--------------------------------------------------------------------------------

This patch is a new English translation of Phantasy Star III: Generations of
Doom (Toki no Keishousha), made from the Japanese script rather than from the
1991 US localization. It is an unofficial fan project and is not affiliated
with or endorsed by SEGA.

The dialogue window now draws proportional (variable-width) text: about a
third more words fit on each line than the original eight-pixel cells allowed,
which is what lets the Japanese script be carried over in full.

  WHAT ELSE CHANGES

  Save slots .......... four instead of two, one per third-generation branch
  Battle messages ..... attacks, damage, healing and Technique effects name
                        their targets and show the amount or outcome clearly
  Walking ............. twice as fast on foot
  Screen transitions .. ordinary menu and map fades take about half as long
  Dialogue ............ page changes scroll smoothly at the selected message
                        scrolling speed
  Battle targeting .... Left moves to the previous target for Items,
                        Techniques and Defend
  Battle background ... the scrolling ground of the Japanese release is back
  Prologue ............ narration letters have a shadow for readability
  Technique Distributor the distribution box stays on screen at high levels
                        (the original could crash there)

The Technique Distributor's graph is scaled to fit at high levels. Its shape
shows the relative allocation; the displayed numbers are the exact values,
so one graph square may represent more than one point.

--------------------------------------------------------------------------------
  2. HOW TO APPLY
--------------------------------------------------------------------------------

You need a clean dump of the US release:

  Phantasy Star III - Generations of Doom (USA, Europe)
  Size:   @SRC_SIZE@ bytes (768 KB) as a plain binary (.bin / .gen / .md)
  CRC32:  @SRC_CRC32@
  MD5:    @SRC_MD5@
  SHA-1:  @SRC_SHA1@

Open Patcher.html in any browser, drop the ROM on it, save the result. It
accepts interleaved .smd dumps too and can save the patched game as .smd.
Alternatively apply @PATCH@ with Flips, beat or any BPS patcher.

If you prefer the original US battle background without the Japanese-style
ground parallax, apply @ALT_PATCH@
to the clean US ROM with a BPS patcher.
Patcher.html applies the standard version. Apply only one of the two BPS files;
the no-parallax patch includes the full translation and all other changes.

The patched ROM:

  Size:   @OUT_SIZE@ bytes
  CRC32:  @OUT_CRC32@
  MD5:    @OUT_MD5@
  SHA-1:  @OUT_SHA1@
  Mega Drive header checksum: @OUT_CHECKSUM@

The no-parallax patched ROM:

  Size:   @ALT_SIZE@ bytes
  CRC32:  @ALT_CRC32@
  MD5:    @ALT_MD5@
  SHA-1:  @ALT_SHA1@
  Mega Drive header checksum: @ALT_CHECKSUM@

The patched ROM is slightly larger than the original: the new text engine and
its font live past the end of the original data. Every emulator and flash
cart handles this. The cartridge header now declares 32 KB of backup RAM
instead of 16 KB (four slots plus their safety copies); emulators and flash
carts size the save file from the header, and a save file from the US game
still loads - its two games are slots 1 and 2.

--------------------------------------------------------------------------------
  3. CREDITS
--------------------------------------------------------------------------------

Translation, hacking and testing by Excalibur_Z, with Claude (Anthropic) for
technical work. Built on lory90's Phantasy Star III disassembly.
Phantasy Star III is copyright SEGA.

Source and tools: https://github.com/ExcalZ/ps3-retranslation
Contact: Discord @Excalibur_Z, Twitter @ExcalZGaming
