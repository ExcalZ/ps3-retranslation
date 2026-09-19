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

  Battle background ... the scrolling ground of the Japanese release is back
  Technique Distributor the distribution box stays on screen at high levels
                        (the original could crash there)

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

The patched ROM:

  Size:   @OUT_SIZE@ bytes
  CRC32:  @OUT_CRC32@
  MD5:    @OUT_MD5@
  SHA-1:  @OUT_SHA1@
  Mega Drive header checksum: @OUT_CHECKSUM@

The patched ROM is slightly larger than the original: the new text engine and
its font live past the end of the original data. Every emulator and flash
cart handles this; the save data (16 KB of backup RAM) is unchanged, so saves
from the US game keep working.

--------------------------------------------------------------------------------
  3. CREDITS
--------------------------------------------------------------------------------

Translation, hacking and testing by Excalibur_Z, with Claude (Anthropic) for
translation and technical work. Built on lory90's Phantasy Star III
disassembly. Phantasy Star III is copyright SEGA.

Source and tools: https://github.com/ExcalZ/ps3-retranslation
Contact: Discord @Excalibur_Z, Twitter @ExcalZGaming
