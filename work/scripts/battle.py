"""Leave Landen for the world map through its real exit, walk until the first random
battle, and screenshot it (scrolling ground, VWF battle messages)."""
import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
with PS3('ps3en.bin') as em:
    boot_to_field(em)
    # the town's exit door is object 0 (map 0, target 1744,312, params $3818): use its params
    teleport(em, 0x00, 1744, 312, facing=0x3818)
    em.frames(120)
    print('map', hex(em.word(0xFFFFD022)), 'pos', em.word(0xFFFFC008), em.word(0xFFFFC00A),
          'D004', hex(em.byte(0xFFFFD004)), 'timer', em.byte(0xFFFFC000 + 0x80 + 0x3F), flush=True)
    em.shot('work/analysis/world.png')
    for i, o in objects(em, base=0xFFFFC000, n=6, size=0x80):
        print('primary', i, o[:16].hex(' '), flush=True)
    dirs = ['U', 'L', 'D', 'R']
    for i in range(300):
        em.pad = BUTTON[dirs[i % 4]]; em.frames(24); em.pad = 0; em.frames(2)
        if em.word(0xFFFFD022) == 0x232:
            break
        if i % 20 == 0:
            print(i, 'pos', em.word(0xFFFFC008), em.word(0xFFFFC00A), 'timer', em.byte(0xFFFFC000 + 0x80 + 0x3F), flush=True)
    print('battle at frame', em.frame, 'map', hex(em.word(0xFFFFD022)), flush=True)
    em.frames(90)
    for j in range(3):
        em.shot('work/analysis/battle%d.png' % j)
        print(j, 'hscroll', em.read(0xFFFF2E02, 4).hex(), em.read(0xFFFF2E02 + 0x20 * 20, 4).hex(), flush=True)
        em.frames(20)
    for k in range(3, 7):
        em.press('A'); em.frames(60); em.shot('work/analysis/battle%d.png' % k)
