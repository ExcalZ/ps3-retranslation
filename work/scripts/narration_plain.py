import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
with PS3('work/analysis/plain.bin') as em:
    while em.word(0xFFFFD012) != 4: em.frames(1)
    em.frames(60); em.press('S')
    while em.word(0xFFFFD012) != 0xC: em.frames(1)
    new_game_intro(em)
    print('at 3AE frame', em.frame, flush=True)
    for k in range(8):
        for i in range(600):
            em.frames(1)
            if em.word(0xFFFFD284) == 8: break
        em.frames(3); em.shot('work/analysis/plain%d.png' % k)
        print(k, 'frame', em.frame, 'routine', hex(em.word(0xFFFFD284)), flush=True)
        em.press('A', hold=2, release=2)
