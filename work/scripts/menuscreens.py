"""Stats and Equip screens with a full inventory: screenshots and plane-A dumps."""
import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
ITEMS = [10, 11, 12, 14, 15, 16, 17, 20, 22, 60, 63, 65, 67, 70, 72]
def dump(em, label):
    d = em.read(0xFFFF2000, 0xE00)
    print('==', label, 'routine', hex(em.word(0xFFFFD284)), '$2', hex(em.word(0xFFFFD282)))
    for r in range(28):
        row = d[r*0x80:r*0x80+80]
        print('%2d ' % r + ' '.join('%3X' % (int.from_bytes(row[i:i+2],'big') & 0x7FF) for i in range(0, 80, 2)))
def shot(em, name):
    em.shot('work/analysis/ms_%s.png' % name)
with PS3('ps3en.bin') as em:
    boot_to_field(em)
    inv = (2 * len(ITEMS)).to_bytes(2, 'big') + b''.join((i << 4).to_bytes(2, 'big') for i in ITEMS)
    # equip a few: bit 15 + slot nibble
    em.write(0xFFFFDE80, inv)
    em.frames(10)
    em.press('C')
    while em.word(0xFFFFD022) != 0x202: em.frames(1)
    em.frames(30); print('menu', hex(em.word(0xFFFFD284)), hex(em.word(0xFFFFD282)))
    em.press('D'); em.frames(20); em.press('D'); em.frames(20)   # Stats
    em.press('C'); em.frames(60); em.press('C'); em.frames(90)
    shot(em, 'stats'); dump(em, 'stats')
    em.press('B'); em.frames(60); em.press('B'); em.frames(60)
    print('back', hex(em.word(0xFFFFD284)), hex(em.word(0xFFFFD282)))
    em.press('D'); em.frames(20)               # Equip
    em.press('C'); em.frames(60); em.press('C'); em.frames(90)
    shot(em, 'equip'); dump(em, 'equip')
    em.press('C'); em.frames(60); shot(em, 'equip2'); dump(em, 'equip2')
