"""Win the first battle and screenshot the victory and level-up messages (the box's top
row, $FFFF2A0A, on the dialogue pool). Kein gets a 200 attack and 14 XP, one short of
level 2, so the fight ends in a round and the level-up follows. Screenshots:
work/analysis/vw*.png."""
import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *

with PS3(sys.argv[1] if len(sys.argv) > 1 else 'ps3en.bin') as em:
    boot_to_field(em); em.frames(120)
    inv = (2 * 1).to_bytes(2, 'big') + (0x8000 | (10 << 4) | 2).to_bytes(2, 'big')   # Steel Swd, equipped (right hand)
    em.write(0xFFFFDE80, inv)
    em.write(0xFFFFC080 + 0x36, (200).to_bytes(2, 'big'))   # attack
    em.write(0xFFFFC080 + 0x3A, (14).to_bytes(4, 'big'))    # XP: level 2 at 15
    teleport(em, 0x00, 1744, 312, facing=0x3818)
    for _ in range(300):
        em.frames(1)
        if em.word(0xFFFFD022) == 0:
            break
    em.frames(120)
    assert em.word(0xFFFFD022) == 0, ('not on the world map', hex(em.word(0xFFFFD022)))
    dirs = ['D', 'R', 'D', 'L']          # away from the town's door (up would re-enter it)
    for i in range(300):
        em.pad = BUTTON[dirs[i % 4]]; em.frames(24); em.pad = 0; em.frames(2)
        if em.word(0xFFFFD022) == 0x232:
            break
        assert em.word(0xFFFFD022) == 0, ('left the world map', hex(em.word(0xFFFFD022)), i)
    print('battle at frame', em.frame, 'map', hex(em.word(0xFFFFD022)), flush=True)
    em.frames(90)
    last = None; n = 0; seen = set()
    for i in range(6000):
        em.frames(1)
        r = em.word(0xFFFFD284)
        if r == 0x24:                                     # the main grid: top-left (Auto), go
            em.press('U'); em.frames(20); em.press('L'); em.frames(20); em.press('C'); em.frames(30)
            continue
        if r >= 0x25C:
            rows = em.read(0xFFFF2A0A, 0x300)
            if rows != last:
                last = rows; n += 1
                em.shot('work/analysis/vw%02d.png' % n)
                print(n, 'frame', em.frame, 'routine', hex(r), 'level', em.byte(0xFFFFC080 + 0x2D), flush=True)
            if r not in seen:
                seen.add(r)
            if r in (0x25C, 0x320) and (i % 90) == 0:
                em.press('C', hold=2, release=2)
        if em.word(0xFFFFD022) != 0x232:
            break
    print('end', em.frame, hex(em.word(0xFFFFD022)), 'level', em.byte(0xFFFFC080 + 0x2D), 'xp', int.from_bytes(em.read(0xFFFFC080 + 0x3A, 4), 'big'), flush=True)
