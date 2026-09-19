"""Lose the first battle and capture the game-over narration pages."""
import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
with PS3('ps3en.bin') as em:
    boot_to_field(em)
    teleport(em, 0x00, 1744, 312, facing=0x3818)
    em.frames(120)
    dirs = ['U', 'L', 'D', 'R']
    for i in range(300):
        em.pad = BUTTON[dirs[i % 4]]; em.frames(24); em.pad = 0; em.frames(2)
        if em.word(0xFFFFD022) == 0x232: break
    em.frames(90)
    for i in range(400):
        em.press('C', hold=2, release=10)
        if em.word(0xFFFFD022) == 0x212: break
    print('game over at', em.frame, flush=True)
    for k in range(9):
        for _ in range(300):
            em.frames(1)
            if em.word(0xFFFFD284) == 8: break
        em.frames(5); em.shot('work/analysis/go%d.png' % k)
        em.press('A', hold=2, release=2)
