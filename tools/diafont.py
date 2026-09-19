"""Generate the proportional dialogue face for the PS3 text engine.

Emits into PSIII_Disasm/vwf/:
    diafont.bin    256 glyphs x 8 bytes, 1bpp rows, indexed by the game's text byte
    diawidth.bin   256 bytes, advance in pixels (ink + 1 px gap; space = 3)

The text bytes are the US font layout (ASCII at $20-$7E) plus the tiles the engine
inserts itself: digits at $01-$0A (numbers printed through $E4), '-' $10, '.' $13,
',' $14, space $1F and $20, and the "III" pair $BE/$BF (drawn as one glyph at $BE, zero
width at $BF). Anything else keeps a blank glyph of advance 8 so a stray byte still
takes a cell instead of vanishing.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import vwfmixed

GAP = 1
SPACE = 3
OUT = os.path.join(ROOT, 'PSIII_Disasm', 'vwf')

code = {}
for b in range(0x20, 0x7F):
    code[b] = chr(b)
for i in range(10):
    code[0x01 + i] = str(i)
code[0x10] = '-'; code[0x13] = '.'; code[0x14] = ','


def glyph_rows(ch):
    g = vwfmixed.G.get(ch)
    if g is None:
        return None
    top, rows = g
    out = [0] * 8
    for dy, r in enumerate(rows):
        b = 0
        for dx, p in enumerate(r):
            if p == '#':
                b |= 1 << (7 - dx)
        out[top + dy] = b
    return out, max(len(r) for r in rows)


def build():
    font = bytearray(256 * 8)
    width = bytearray([8] * 256)
    missing = []
    for b, ch in sorted(code.items()):
        if ch == ' ':
            width[b] = SPACE
            continue
        g = glyph_rows(ch)
        if g is None:
            missing.append(ch)
            continue
        rows, iw = g
        font[b * 8:b * 8 + 8] = bytes(rows)
        width[b] = iw + GAP
    width[0x1F] = SPACE
    # "III" of Alisa III: three 1-px stems at 2 px pitch, 7 rows, in one glyph
    font[0xBE * 8:0xBE * 8 + 8] = bytes([0b10101000] * 7 + [0])
    width[0xBE] = 5 + GAP
    width[0xBF] = 0
    return bytes(font), bytes(width), missing


def measure(text_bytes, width=None):
    """Pixel width of a byte string (no control codes)."""
    if width is None:
        width = build()[1]
    return sum(width[b] for b in text_bytes)


if __name__ == '__main__':
    font, width, missing = build()
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'diafont.bin'), 'wb').write(font)
    open(os.path.join(OUT, 'diawidth.bin'), 'wb').write(width)
    print('wrote diafont.bin / diawidth.bin; no glyph for: %s' % ''.join(missing))
