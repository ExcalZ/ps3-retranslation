"""Technique Distributor routines under the interpreter: fractional scaling fills
the available area, redraws leave no old outline, raw values are never written, and
the full distributor renderer draws all four technique names.

    python tools/test_techdist.py
"""
import os, sys
from fractions import Fraction
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from ps3harness import Machine, Symbols

RAW, OUT = 0xFFFFF000, 0xFFFFF010
CTX, MAP_ID = 0xFFFFD280, 0xFFFFD022

def scale(m, sym, vals):
    m.poke(RAW, bytes(vals)); m.poke(OUT, bytes(8))
    m.call(sym['TechDist_Scale'], a0=RAW, a1=OUT)
    assert m.peek(RAW, 8) == bytes(vals), 'raw values written'
    return list(m.peek(OUT, 8))


def expected_scale(vals):
    w, h = vals[0] + vals[2], vals[1] + vals[5]
    candidates = [(1, 1)]
    if w > 24:
        candidates.append((24, w))
    if h > 14:
        candidates.append((14, h))
    num, den = min(candidates, key=lambda pair: Fraction(*pair))
    out = [max(1, v * num // den) for v in vals]
    width = max(2, w * num // den)
    height = max(2, h * num // den)
    for first, second, total in ((0, 2, width), (4, 6, width),
                                 (1, 5, height), (3, 7, height)):
        out[first] = min(out[first], total - 1)
        out[second] = total - out[first]
    return out


def box(m):
    return m.peek(0xFFFF231E, 13 * 0x80 + 24 * 2)


def test_redraw(sym):
    # Slot 0's Laia: the old integer division made 17x16 into only 8x7.
    original = [3, 13, 14, 13, 3, 3, 14, 3]
    moved = [3, 12, 14, 12, 3, 4, 14, 4]
    assert expected_scale(original)[0] + expected_scale(original)[2] == 14
    assert expected_scale(original)[1] + expected_scale(original)[5] == 14
    m = Machine()
    m.poke(0xFFFF2218, b'\x80\x1f' * 6)
    m.poke(0xFFFF2298, b''.join((0x8000 | ord(c)).to_bytes(2, 'big')
                                    for c in 'SCALED'))
    m.poke(RAW, bytes(original))
    m.call(sym['TechDist_Box'], a0=RAW)
    assert m.peek(RAW, 8) == bytes(original)
    assert m.peek(0xFFFF2218, 12) == bytes(12)
    assert m.peek(0xFFFF2298, 12) == bytes(12)
    first = box(m)
    m.poke(RAW, bytes(moved))
    m.call(sym['TechDist_Box'], a0=RAW)
    after_move = box(m)
    m.poke(RAW, bytes(original))
    m.call(sym['TechDist_Box'], a0=RAW)
    assert box(m) == first, 'old outline survived Up/Down redraw'
    fresh = Machine()
    fresh.poke(RAW, bytes(moved))
    fresh.call(sym['TechDist_Box'], a0=RAW)
    assert after_move == box(fresh), 'redraw depends on old box'


def test_four_name_rows(sym):
    m = Machine()
    m.poke(sym['loc_FC18'], b'\x4E\x75')       # return after building the plane buffer
    m.poke(RAW, bytes([2, 3, 3, 3, 2, 2, 3, 2]))
    m.poke(MAP_ID, (0x22C).to_bytes(2, 'big'))
    m.poke(0xFFFFD068, (8).to_bytes(2, 'big'))  # Recovery: Sun/Star/Moon/Sea Force
    m.poke(CTX + 0x1C, b'\x00')
    m.call(sym['loc_C8F4'], a0=RAW, a6=CTX)
    for i in range(4):
        glyph_row = 0xFFFF270A + i * 0x100
        first_pool_tile = 0x352 + i * 8
        first_word = int.from_bytes(m.peek(glyph_row, 2), 'big')
        assert first_word == 0x8000 | first_pool_tile, (i, hex(first_word))

def main():
    sym = Symbols(); m = Machine()
    for vals in ([4, 4, 4, 4, 4, 4, 4, 4], [1, 1, 1, 1, 1, 1, 1, 1],
                 [12, 7, 12, 7, 7, 7, 17, 7]):
        assert scale(m, sym, vals) == vals, vals
    for vals in ([20] * 8, [3, 40, 30, 2, 9, 1, 7, 33], [99] * 8, [200] * 8,
                 [1, 99, 1, 1, 1, 99, 1, 1], [60, 1, 60, 1, 1, 1, 1, 1],
                 [255, 0, 0, 1, 1, 1, 1, 1], [0, 255, 1, 1, 1, 0, 1, 1],
                 [3, 13, 14, 13, 3, 3, 14, 3]):
        s = scale(m, sym, vals)
        w, h = s[0] + s[2], s[1] + s[5]
        assert w <= 24 and h <= 14, (vals, s, w, h)
        assert min(s) >= 1, (vals, s)
        assert s == expected_scale(vals), (vals, s, expected_scale(vals))
    test_redraw(sym)
    test_four_name_rows(sym)
    print('test_techdist: all passed')

if __name__ == '__main__':
    main()
