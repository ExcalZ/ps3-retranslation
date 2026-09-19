"""Idle at the title until the attract-mode story (Screen_Intro, map $212) plays; capture
each page of its narration (loc_25F24)."""
import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
with PS3('ps3en.bin') as em:
    while em.word(0xFFFFD012) != SCREEN_TITLE: em.frames(1)
    while em.word(0xFFFFD012) != 8: em.frames(1)
    print('intro at', em.frame, flush=True)
    last = None
    for k in range(12):
        for _ in range(900):
            em.frames(1)
            row = em.read(0xFFFF9AEA, 48)
            if em.word(0xFFFFD284) == 8 and row != last: break
        last = row
        em.frames(3); em.shot('work/analysis/at%d.png' % k)
        print(k, 'frame', em.frame, 'screen', hex(em.word(0xFFFFD012)), flush=True)
        if em.word(0xFFFFD012) != 8: break
        em.press('A', hold=2, release=2)
