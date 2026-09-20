"""Enter the three shop types from Landen, step to the buy list, screenshot each step and
dump which tiles plane A/B reference on the store map."""
import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
def shot(em, name):
    em.shot('work/analysis/sh_%s.png' % name)
    print(name, 'map', hex(em.word(0xFFFFD022)), 'routine', hex(em.word(0xFFFFD284)), '$2', hex(em.word(0xFFFFD282)), flush=True)
def usage(em, label):
    for name, base in (('planeA', 0xFFFF2000), ('planeB', 0xFFFF3200)):
        d = em.read(base, 0xE00)
        tiles = sorted(set(int.from_bytes(d[i:i+2], 'big') & 0x7FF for i in range(0, 0xE00, 2)))
        hi = [t for t in tiles if t > 0xFF]
        print(label, name, 'distinct %d' % len(tiles), 'above $FF: %d, min $%X max $%X' % (len(hi), min(hi) if hi else 0, max(hi) if hi else 0), flush=True)
def enter(em, kind):
    em.write(0xFFFFC040, (50000).to_bytes(4, 'big'))
    em.write(0xFFFFD02A, bytes([kind, 0])); em.write(0xFFFFD006, bytes([em.byte(0xFFFFD006) | 0x10]))
    while em.word(0xFFFFD022) != 0x222 + kind * 2: em.frames(1)
    em.frames(60)
with PS3(sys.argv[1] if len(sys.argv) > 1 else 'ps3en.bin') as em:
    boot_to_field(em)
    for kind, name in ((0, 'weapon'), (1, 'armor'), (2, 'item')):
        enter(em, kind); shot(em, name + '0'); usage(em, name)
        for i in range(1, 6):
            em.press('C'); em.frames(120); shot(em, '%s%d' % (name, i))
        usage(em, name + '_list')
        for _ in range(4): em.press('B'); em.frames(90)
        shot(em, name + '_out')
        while em.word(0xFFFFD022) != 0x5A: em.press('B', hold=2, release=60)
        em.frames(60)
