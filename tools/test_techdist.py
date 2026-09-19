"""TechDist_Scale (ext/techdist.asm) under the interpreter: the scaled box always fits
24 x 14 cells, every arm keeps at least one cell, small boxes are unchanged, and the raw
values are never written.

    python tools/test_techdist.py
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from ps3harness import Machine, Symbols

RAW, OUT = 0xFFFFF000, 0xFFFFF010

def scale(m, sym, vals):
    m.poke(RAW, bytes(vals)); m.poke(OUT, bytes(8))
    m.call(sym['TechDist_Scale'], a0=RAW, a1=OUT)
    assert m.peek(RAW, 8) == bytes(vals), 'raw values written'
    return list(m.peek(OUT, 8))

def main():
    sym = Symbols(); m = Machine()
    for vals in ([4, 4, 4, 4, 4, 4, 4, 4], [1, 1, 1, 1, 1, 1, 1, 1], [12, 7, 12, 7, 7, 7, 7, 7]):
        assert scale(m, sym, vals) == vals, vals
    for vals in ([20] * 8, [3, 40, 30, 2, 9, 1, 7, 33], [99] * 8, [1, 99, 1, 1, 1, 99, 1, 1], [60, 1, 60, 1, 1, 1, 1, 1]):
        s = scale(m, sym, vals)
        w, h = s[0] + s[2], s[1] + s[5]
        assert w <= 24 and h <= 14, (vals, s, w, h)
        assert min(s) >= 1, (vals, s)
        k = max(1, -(-(vals[0] + vals[2]) // 24), -(-(vals[1] + vals[5]) // 14))
        # k is the smallest divisor that fits; the asm loops k up from 1 the same way
        assert all(s[i] == max(1, vals[i] // k) for i in range(8)), (vals, s, k)
    print('test_techdist: all passed')

if __name__ == '__main__':
    main()
