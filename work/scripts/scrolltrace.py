import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
from ps3harness import Symbols
sym = Symbols()
with PS3('ps3en.bin') as em:
    while em.word(0xFFFFD012) != SCREEN_TITLE: em.frames(1)
    em.frames(60); em.press('S')
    while em.word(0xFFFFD012) != SCREEN_GAMESEL: em.frames(1)
    new_game_intro(em)
    bp = sym['loc_F7F0']; em.breakpoint(bp)
    log = []
    def hook(pc):
        if pc == bp:
            r = em.regs()
            log.append((em.frame, r['d'][1] & 0xFFFF, r['d'][2] & 0xFFFF, hex(r['d'][3] & 0xFFFF), hex(r['a'][0]), em.word(0xFFFF2E00), em.read(r['a'][0], 12)))
    em.frames(1500, hook=hook)
    for l in log[:40]: print(l, flush=True)
    print(len(log), 'calls')
