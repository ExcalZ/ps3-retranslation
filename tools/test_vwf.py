"""Run the dialogue VWF engine (ext/vwf.asm) under the 68000 interpreter and compare its
output - window tilemap rows and the pool tiles it uploads - with a Python reference
composer built from the same font binaries.

    python tools/test_vwf.py

Covers: plain text, {BR}, {PAGE} continuation state, {NAME} inserts, {NUM} numbers,
clipping at the right edge, the page scroll (VWFDia_ScrollUp) and the fixed-width
fallback for windows that are not the dialogue's.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import ps3text                       # noqa: E402
from ps3harness import Machine, Symbols   # noqa: E402

V = os.path.join(ROOT, 'PSIII_Disasm', 'vwf')
FONT = open(os.path.join(V, 'diafont.bin'), 'rb').read()
WIDTH = open(os.path.join(V, 'diawidth.bin'), 'rb').read()
POOL, CELLS, STRIDE = 0xC0, 24, 0x34
CTX = 0xFFFFD280
TEMPLATE_ROW0, LIVE_ROW0, LIVE_ROW1 = 0xFFFF9D26, 0xFFFF9AB6, 0xFFFF9B1E
NAMES = 0xFFFFD480         # char_name_saved: pointer table for {NAME:nn}
NUMS = 0xFFFFD4A0          # longs for {NUM:nn}
TEXT = 0x0FF000            # scratch text lives in the unused part of the 1 MB window


def compose(line_bytes):
    """Reference: 1bpp canvas rows (24 bytes each) and the pen position for one line."""
    canvas = [bytearray(26) for _ in range(8)]
    x = 0
    for b in line_bytes:
        w = WIDTH[b]
        if w == 0:
            continue
        if x + w - 1 > 192:
            continue
        for r in range(8):
            v = (FONT[b * 8 + r] << 8) >> (x & 7)
            canvas[r][x >> 3] |= (v >> 8) & 0xFF
            canvas[r][(x >> 3) + 1] |= v & 0xFF
        x += w
    return canvas, x


def expand(canvas):
    """Reference: 24 4bpp tiles (ink 1, paper 2)."""
    out = bytearray()
    for c in range(CELLS):
        for r in range(8):
            byte = canvas[r][c]
            for shift in (4, 0):
                nib = (byte >> shift) & 0xF
                v = 0
                for bit in (8, 4, 2, 1):
                    v = (v << 4) | (1 if nib & bit else 2)
                out += v.to_bytes(2, 'big')
    return bytes(out)


def rows(m, row0):
    mark = m.peek(row0, CELLS * 2)
    glyph = m.peek(row0 + STRIDE, CELLS * 2)
    return ([int.from_bytes(mark[i:i + 2], 'big') for i in range(0, CELLS * 2, 2)],
            [int.from_bytes(glyph[i:i + 2], 'big') for i in range(0, CELLS * 2, 2)])


def machine(sym):
    m = Machine()
    m.poke(CTX + 0x42, (STRIDE).to_bytes(2, 'big'))
    m.poke(CTX + 0x44, (CELLS).to_bytes(2, 'big'))
    return m


def render(m, sym, text, row0=TEMPLATE_ROW0, attr=0x8000):
    data = ps3text.encode(text, 'us') + b'\xFC'
    m.poke(TEXT, data)
    m.vram_writes = []
    m.a[6] = CTX
    m.call(sym['loc_10038'], a0=TEXT, a1=row0, d0=attr)


def check_line(m, line_bytes, row0, line, attr=0x8000, label=''):
    canvas, x = compose(line_bytes)
    cells = (x + 7) // 8
    mark, glyph = rows(m, row0)
    assert mark == [attr | 0x1F] * CELLS, (label, 'mark row', mark)
    want = [attr | (POOL + line * CELLS + i) for i in range(cells)] + [attr | 0x1F] * (CELLS - cells)
    assert glyph == want, (label, 'glyph row', [hex(v) for v in glyph], [hex(v) for v in want])
    base = (POOL + line * CELLS) * 32
    assert bytes(m.vram[base:base + CELLS * 32]) == expand(canvas), (label, 'pool tiles')
    return x


def test_plain(sym):
    m = machine(sym)
    render(m, sym, 'Nothing unusual here.')
    x = check_line(m, b'Nothing unusual here.', TEMPLATE_ROW0, 0, label='plain')
    assert x == sum(WIDTH[b] for b in b'Nothing unusual here.')
    assert m.peek(CTX + 1, 1)[0] & 0x30 == 0, 'no continuation flags'
    print('  plain line ok (%d px)' % x)


def test_br_and_page(sym):
    m = machine(sym)
    render(m, sym, 'The legends of Landen,{BR}your homeland, tell of{PAGE}world-sweeping wars{PAGE}fought.')
    check_line(m, b'The legends of Landen,', TEMPLATE_ROW0, 0, label='br line 0')
    check_line(m, b'your homeland, tell of', TEMPLATE_ROW0 + 2 * STRIDE, 1, label='br line 1')
    flags = m.peek(CTX + 1, 1)[0]
    assert flags & 0x20, 'bit 5 (more text) set after {PAGE}'
    cont = int.from_bytes(m.peek(CTX + 0x3E, 4), 'big')
    assert m.peek(cont, 5) == b'world', 'continuation pointer after the $EC'
    print('  {BR} and {PAGE} ok')
    return m, cont


def test_scroll(sym):
    m, cont = test_br_and_page(sym)
    # the game copies the template into the live window; emulate that for the two rows
    for off in (0, STRIDE, 2 * STRIDE, 3 * STRIDE):
        m.poke(LIVE_ROW0 + off, m.peek(TEMPLATE_ROW0 + off, CELLS * 2))
    # page wait done: scroll up, then render the continuation into the second line
    m.a[6] = CTX
    m.call(sym['VWFDia_ScrollUp'], a0=LIVE_ROW1, a1=LIVE_ROW0)
    check_line(m, b'your homeland, tell of', LIVE_ROW0, 0, label='scrolled line')
    m.poke(CTX + 1, bytes([m.peek(CTX + 1, 1)[0] & ~0x20]))
    m.vram_writes = []
    m.call(sym['loc_10038'], a0=cont, a1=LIVE_ROW1, d0=0x8000)
    check_line(m, b'world-sweeping wars', LIVE_ROW1, 1, label='next page')
    check_line(m, b'your homeland, tell of', LIVE_ROW0, 0, label='scrolled line kept')
    print('  page scroll ok')


def test_inserts(sym):
    m = machine(sym)
    m.poke(0x0FF800, b'Rhys\xFC')
    m.poke(NAMES, (0x0FF800).to_bytes(4, 'big'))
    m.poke(NUMS, (1234).to_bytes(4, 'big'))
    m.poke(NUMS + 4, (0).to_bytes(4, 'big'))
    render(m, sym, "{NAME:00}'s party won.{BR}Earned {NUM:00} XP and {NUM:04}.", row0=LIVE_ROW0)
    check_line(m, b"Rhys's party won.", LIVE_ROW0, 0, label='name insert')
    check_line(m, b'Earned \x02\x03\x04\x05 XP and \x01.', LIVE_ROW0 + 2 * STRIDE, 1, label='number insert')
    assert m.peek(CTX + 1, 1)[0] & 0x10 == 0, 'insert flag cleared'
    print('  {NAME} and {NUM} inserts ok')


def test_clip(sym):
    m = machine(sym)
    text = 'W' * 40
    render(m, sym, text)
    x = check_line(m, text.encode(), TEMPLATE_ROW0, 0, label='clip')
    assert x <= 192, x
    print('  right-edge clipping ok (%d px)' % x)


def test_fixed_fallback(sym):
    m = machine(sym)
    other = 0xFFFF9C9E   # a name-list window row: must take the stock path
    render(m, sym, 'Rhys', row0=other)
    mark, glyph = rows(m, other)
    assert glyph[:4] == [0x8000 | c for c in b'Rhys'], glyph[:4]
    assert not m.vram_writes, 'stock path uploads nothing'
    print('  fixed-width fallback ok')


def main():
    sym = Symbols()
    for t in (test_plain, test_br_and_page, test_scroll, test_inserts, test_clip, test_fixed_fallback):
        t(sym)
    print('test_vwf: all passed')


if __name__ == '__main__':
    main()
