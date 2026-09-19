"""Fight the first battle to its end, screenshotting each new battle message."""
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
    last = None; n = 0
    for i in range(400):
        em.press('C', hold=2, release=10)
        row = em.read(0xFFFF2C8A, 48)
        if row != last:
            last = row; n += 1
            em.shot('work/analysis/bw%02d.png' % n)
            print(n, 'frame', em.frame, 'map', hex(em.word(0xFFFFD022)), flush=True)
        if em.word(0xFFFFD022) != 0x232:
            break
    print('end', em.frame, hex(em.word(0xFFFFD022)), flush=True)
