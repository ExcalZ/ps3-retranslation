"""Item screen with a full inventory of fifteen distinct nine-cell names: screenshots and
the tile indices the menu screen references (plane A/B buffers, sprite table)."""
import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
ITEMS = [10, 11, 12, 14, 15, 16, 17, 20, 22, 60, 63, 65, 67, 70, 72]   # SteelSwd, CeramSwd, ... 9 cells each
def shot(em, name):
    em.shot('work/analysis/is_%s.png' % name)
    print(name, 'routine', hex(em.word(0xFFFFD284)), '2', hex(em.word(0xFFFFD282)), 'map', hex(em.word(0xFFFFD022)), flush=True)
def usage(em, label):
    for name, base, size in (('planeA', 0xFFFF2000, 0xE00), ('planeB', 0xFFFF3200, 0xE00)):
        d = em.read(base, size)
        tiles = sorted(set(int.from_bytes(d[i:i+2], 'big') & 0x7FF for i in range(0, size, 2)))
        print(label, name, 'distinct %d, min $%X max $%X' % (len(tiles), tiles[0], tiles[-1]),
              'above $FF:', [hex(t) for t in tiles if t > 0xFF][:40], flush=True)
    spr = em.read(0xFFFF9800, 0x280)
    st = sorted(set(int.from_bytes(spr[i+4:i+6], 'big') & 0x7FF for i in range(0, 0x280, 8) if spr[i+2]))
    print(label, 'sprites tiles', [hex(t) for t in st][:40], flush=True)
with PS3('ps3en.bin') as em:
    boot_to_field(em)
    inv = (2 * len(ITEMS)).to_bytes(2, 'big') + b''.join((i << 4).to_bytes(2, 'big') for i in ITEMS)
    em.write(0xFFFFDE80, inv)
    em.frames(10); shot(em, 'field'); usage(em, 'field')
    em.press('C'); em.frames(120); shot(em, 'menu'); usage(em, 'menu')
    em.press('C'); em.frames(60); shot(em, 'whose')
    em.press('C'); em.frames(60); shot(em, 'items'); usage(em, 'items')
    em.press('C'); em.frames(60); shot(em, 'action')
