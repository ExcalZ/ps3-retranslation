import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
ITEMS = [10, 11, 12, 14, 15, 16, 17, 20, 22, 60, 63, 65, 67, 70, 72]
with PS3('ps3en.bin') as em:
    boot_to_field(em)
    inv = (2 * len(ITEMS)).to_bytes(2, 'big') + b''.join((i << 4).to_bytes(2, 'big') for i in ITEMS)
    em.write(0xFFFFDE80, inv)
    em.frames(10)
    for _ in range(4):
        em.press('C'); em.frames(90)
        if em.word(0xFFFFD022) == 0x202 and em.word(0xFFFFD282) == 8: break
    print('state', hex(em.word(0xFFFFD022)), hex(em.word(0xFFFFD282)))
    d = em.read(0xFFFF2000, 0xE00)
    tiles = sorted(set(int.from_bytes(d[i:i+2], 'big') & 0x7FF for i in range(0, 0xE00, 2)))
    print('planeA tiles:', ' '.join('%X' % t for t in tiles))
    # rows of plane A as tile indices (40 visible columns)
    for r in range(28):
        row = d[r*0x80:r*0x80+80]
        print('%2d ' % r + ' '.join('%3X' % (int.from_bytes(row[i:i+2],'big') & 0x7FF) for i in range(0, 80, 2)))
    spr = em.read(0xFFFF9800, 0x280)
    print('sprites:', [(spr[i+2], hex(int.from_bytes(spr[i+4:i+6], 'big'))) for i in range(0, 0x280, 8) if spr[i+2] or spr[i+3]][:20])
    print('D006', hex(em.byte(0xFFFFD006)))
