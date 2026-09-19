import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
with PS3('ps3en.bin') as em:
    while em.word(0xFFFFD012) != SCREEN_TITLE: em.frames(1)
    em.frames(60); em.press('S')
    while em.word(0xFFFFD012) != SCREEN_GAMESEL: em.frames(1)
    new_game_intro(em); em.frames(300)
    pal = em.read(0xFFFFDC00, 128)
    for p in range(4):
        print('pal', p, ' '.join('%04X' % int.from_bytes(pal[p*32+i*2:p*32+i*2+2], 'big') for i in range(16)), flush=True)
    # plane B word sample (priority bit?)
    d = em.read(0xFFFF4400, 64)
    print('planeB words', ' '.join('%04X' % int.from_bytes(d[i:i+2], 'big') for i in range(0, 32, 2)), flush=True)
