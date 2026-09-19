import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
with PS3('ps3en.bin') as em:
    boot_to_field(em)
    em.frames(120)
    i, nx, ny, so = npc_list(em)[-1]
    em.write(0xFFFFC300 + i * 0x40 + 0x26, (0x1A).to_bytes(2, 'big'))   # loc_25F24: the multi-page legend
    talk(em, nx, ny)
    em.frames(90); em.shot('work/analysis/pg0.png')
    for k in range(1, 6):
        em.press('A', hold=2, release=2)
        for _ in range(200):
            em.frames(1)
            if em.word(0xFFFFD284) == 8: break
        em.frames(5); em.shot('work/analysis/pg%d.png' % k)
        print(k, 'routine', hex(em.word(0xFFFFD284)), flush=True)
