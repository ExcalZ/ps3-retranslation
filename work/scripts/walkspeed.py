"""fast_walk: the party's step on the field and the scripted walks of the opening.

    python work/scripts/walkspeed.py [ps3en.bin] [slow.bin]

From power-on through the wedding and the Landen intro to the town, logging the leader's
position (x, y of the sprite manager) whenever the demo input or the map changes, then
walking on the field for 60 frames: the px per frame, frames per step and the sprite's
animation frame per frame. With a second ROM (built with fast_walk = 0) the demo
positions are compared: the cutscenes must end each walk on the same tile."""
import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *

def trace(rom):
    """A ROM built with other options has its own listing beside it (<rom>.lst)."""
    lst = os.path.splitext(rom)[0] + '.lst'
    if not os.path.exists(lst):
        lst = LST
    log = []
    with PS3(rom, lst=lst) as em:
        em.frames(1)
        while em.word(0xFFFFD012) != SCREEN_TITLE: em.frames(1)
        em.frames(60); em.press('S')
        while em.word(0xFFFFD012) != SCREEN_GAMESEL: em.frames(1)
        new_game_intro(em)
        last = None
        n = 0
        while not (em.word(0xFFFFD012) == SCREEN_MAIN and em.word(0xFFFFD022) == 0x5A and em.read(0xFFFFC000, 1) != b'\0') and n < 20000:
            em.press('C', hold=2, release=6); n += 1
            key = (em.word(0xFFFFD022), em.byte(0xFFFFD396))
            if key != last:
                last = key
                log.append((em.frame, key[0], key[1], em.word(0xFFFFC008), em.word(0xFFFFC00A)))
                print('  frame %5d map %04X demo %02X at %d,%d' % log[-1], flush=True)
        em.frames(120)
        # the demo-script player (loc_11C16: Demo_LandenWalkToPrison - wait 4, down 10, left 32,
        # up 12 steps) run from the town: the leader's position at every change of demo input
        # and when the demo ends
        base = listing_address('loc_11C16', lst=lst)
        used = {i for i, _ in objects(em)}
        slot = 0xFFFFC300 + min(i for i in range(26) if i not in used) * 0x40
        em.write(slot, bytes([0xC0, 0, 0, 0]) + base.to_bytes(4, 'big') + bytes(0x38))
        print('  slot %X base %X' % (slot, base), flush=True)
        em.write(0xFFFFD004, bytes([em.byte(0xFFFFD004) | 4]))
        last = None
        for f in range(1200):
            em.frames(1)
            key = (em.byte(0xFFFFD004) & 4, em.byte(0xFFFFD396), em.word(0xFFFFD022), em.word(0xFFFFD012))
            if key != last:
                last = key
                log.append((em.frame, key[2], key[1], em.word(0xFFFFC008), em.word(0xFFFFC00A)))
                print('  frame %5d map %04X demo %02X at %d,%d' % log[-1], 'screen %X D004 %02X' % (key[3], em.byte(0xFFFFD004)), flush=True)
            if f % 8 == 0 and f < 200:
                print('    f%d pos %d,%d $2 %X obj %s' % (f, em.word(0xFFFFC008), em.word(0xFFFFC00A), em.word(0xFFFFC002), em.read(slot, 0x28).hex(' ')), flush=True)
            if not key[0]:
                break
        em.frames(30)
        # walk right on the field: position, step counter and the leader sprite's animation frame
        x0 = em.word(0xFFFFC008)
        em.pad = BUTTON['R']
        steps = []
        for f in range(60):
            em.frames(1)
            steps.append((em.word(0xFFFFC008) - x0, em.byte(0xFFFFC000 + 0xC), em.word(0xFFFFC080 + 0x22)))
        em.pad = 0
        em.frames(30)
        em.shot('work/analysis/ws_%s.png' % os.path.splitext(os.path.basename(rom))[0])
    return log, steps

fast = sys.argv[1] if len(sys.argv) > 1 else 'ps3en.bin'
log, steps = trace(fast)
print('field walk (dx, step counter, anim frame) per frame:')
print(' ', steps[:24])
dx = [b[0] - a[0] for a, b in zip(steps, steps[1:])]
anim = [s[2] for s in steps]
print('  px/frame', sorted(set(dx)), 'anim frames', anim[:20])
if len(sys.argv) > 2:
    slow, slow_steps = trace(sys.argv[2])
    a = [(m, d, x, y) for _, m, d, x, y in log]
    b = [(m, d, x, y) for _, m, d, x, y in slow]
    print('demo positions', 'MATCH' if a == b else 'DIFFER')
    if a != b:
        for i, (p, q) in enumerate(zip(a, b)):
            if p != q: print('  ', i, p, q)
    print('  slow walk', slow_steps[:24])
