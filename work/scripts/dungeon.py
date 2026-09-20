"""Reproduce the freeze after the king's "cool off in the dungeon" text: give a Landen NPC
that script (entry 19, loc_2648C) and talk; watch the routine, the smooth-scroll flag and
the PC each frame; when BlastEm freezes the CPU the stub still answers."""
import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
GS = listing_address('GameScript')
with PS3(sys.argv[1] if len(sys.argv) > 1 else 'ps3en.bin') as em:
    boot_to_field(em)
    em.frames(60)
    i, nx, ny, so = npc_list(em)[-1]
    em.write(0xFFFFC300 + i * 0x40 + 0x26, (0x2648C - GS).to_bytes(2, 'big'))
    em.write(0xFFFFD11C, bytes([0x48]))
    talk(em, nx, ny)
    em.frames(60); em.shot('work/analysis/dg_0.png')
    last = None; n = 0
    for k in range(8):
        em.press('A', hold=2, release=2)
        for f in range(300):
            em.frames(1)
            r = em.word(0xFFFFD284)
            if r == 8 and em.word(0xFFFFFA14) == 0: break
        n += 1; em.shot('work/analysis/dg_%d.png' % n)
        print(n, 'frame', em.frame, 'routine', hex(r), 'map', hex(em.word(0xFFFFD022)), 'pc', hex(em.regs()['pc']), flush=True)
        if em.word(0xFFFFD022) != 0x5A: break
    for f in range(600):
        em.frames(1)
        if f % 60 == 0:
            print('after', f, 'routine', hex(em.word(0xFFFFD284)), 'map', hex(em.word(0xFFFFD022)), 'pc', hex(em.regs()['pc']), 'active', em.word(0xFFFFFA14), flush=True)
    em.shot('work/analysis/dg_end.png')
