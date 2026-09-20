"""Show translated dialogue entries in BlastEm: point a Landen NPC's script offset at
each entry in turn, talk, and screenshot every page until the box closes.

    python work/scripts/dialogue_check.py [label ...]

Screenshots go to work/analysis/dc_<label>_<page>.png. A quick visual check that
the retranslated lines fit the box the way linecheck.py predicts.
"""
import sys, os
sys.path.insert(0, 'tools')
from ps3emu import *

DEFAULT = ['loc_261F8', 'loc_2648C', 'loc_26652', 'loc_2677A', 'loc_27430', 'loc_286B4', 'loc_2F7CC']
labels = sys.argv[1:] or DEFAULT
base = listing_address('GameScript')
with PS3('ps3en.bin') as em:
    boot_to_field(em)
    em.frames(120)
    i, nx, ny, so = npc_list(em)[-1]
    for label in labels:
        off = listing_address(label) - base
        em.write(0xFFFFC300 + i * 0x40 + 0x26, off.to_bytes(2, 'big'))
        talk(em, nx, ny)
        em.frames(90)
        page = 0
        em.shot('work/analysis/dc_%s_%d.png' % (label, page))
        for _ in range(40):
            em.press('A', hold=2, release=2)
            closed = False
            for _ in range(200):
                em.frames(1)
                if not (em.byte(0xFFFFD286) & 0x40):
                    closed = True; break
                if em.word(0xFFFFD284) == 8:
                    break
            if closed:
                break
            page += 1
            em.frames(5)
            em.shot('work/analysis/dc_%s_%d.png' % (label, page))
        print(label, 'offset', hex(off), 'pages', page + 1, 'closed', closed, flush=True)
        em.frames(30)
