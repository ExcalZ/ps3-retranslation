import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
import collections
with PS3('ps3en.bin') as em:
    while em.word(0xFFFFD012) != SCREEN_TITLE: em.frames(1)
    em.frames(60); em.press('S')
    while em.word(0xFFFFD012) != SCREEN_GAMESEL: em.frames(1)
    new_game_intro(em); em.frames(400)
    print('map', hex(em.word(0xFFFFD022)), flush=True)
    for name, base, size in (('planeA', 0xFFFF2000, 0x1000), ('planeB', 0xFFFF3200, 0x1000), ('4400', 0xFFFF4400, 0x2000)):
        d = em.read(base, size)
        tiles = [int.from_bytes(d[i:i+2], 'big') & 0x7FF for i in range(0, size, 2)]
        used = sorted(set(t for t in tiles if t))
        print(name, 'tiles used: %d, min $%X max $%X' % (len(used), min(used) if used else 0, max(used) if used else 0),
              'ranges', [(hex(a), hex(b)) for a, b in [(used[0], used[0])] ] if used else None, flush=True)
        # print gaps
        gaps = [(used[i], used[i+1]) for i in range(len(used)-1) if used[i+1]-used[i] > 16]
        print('   gaps >16:', [(hex(a), hex(b)) for a, b in gaps], flush=True)
