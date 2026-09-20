"""Which windows still take the stock fixed-width renderer? Break on loc_10038_Fixed
(where VWFDia_Entry hands a call back) and on loc_F7F0_Fixed, and log each distinct
(map, a1 row, $44(a6) cells, text) while walking the game select, the field menu
screens, a shop of each kind and an NPC talk.

    python work/scripts/fixedaudit.py [ps3en.bin]
"""
import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
import ps3text

seen = {}
def text_at(em, a0, n=40):
    raw = em.read(a0, n)
    raw = raw[:raw.index(b'\xFC')] if b'\xFC' in raw else raw
    try:
        return ps3text.decode(raw, 'us')
    except Exception:
        return raw.hex()
def hook(pc):
    r = em.regs()
    a0, a1, a6 = r['a'][0], r['a'][1], r['a'][6]
    cells = em.word(a6 + 0x44) if a6 & 0xFFFFFF >= 0xFF0000 else -1
    which = 'F7F0' if pc == bp_scroll else '10038'
    key = (which, em.word(0xFFFFD022), a1 & 0xFFFFFF, cells, text_at(em, a0)[:28])
    if key not in seen:
        seen[key] = em.frame
        print('%s map %04X a1 %06X cells %2d  %r' % key, flush=True)

orig = PS3.step_frame
PS3.step_frame = lambda self, h=None: orig(self, hook)

with PS3(sys.argv[1] if len(sys.argv) > 1 else 'ps3en.bin') as em:
    bp_fixed = listing_address('loc_10038_Fixed'); em.breakpoint(bp_fixed)
    bp_scroll = listing_address('loc_F7F0_Fixed'); em.breakpoint(bp_scroll)
    # the long boot: title, game select (slot checks, text speed), the opening, Landen
    em.frames(1)
    while em.word(0xFFFFD012) != SCREEN_TITLE: em.frames(1)
    em.frames(60); em.press('S')
    while em.word(0xFFFFD012) != SCREEN_GAMESEL: em.frames(1)
    new_game_intro(em)
    n = 0
    while not (em.word(0xFFFFD012) == SCREEN_MAIN and em.word(0xFFFFD022) == 0x5A and em.read(0xFFFFC000, 1) != b'\0') and n < 700:
        em.press('C', hold=2, release=6); n += 1
    em.frames(120)
    print('--- field', flush=True)
    # an NPC talk (dialogue path) and the field menu screens
    i, nx, ny, so = npc_list(em)[-1]
    talk(em, nx, ny); em.frames(90); em.press('A'); em.frames(60); em.press('A'); em.frames(60)
    ITEMS = [10, 11, 12, 14, 15, 16, 17, 20, 22, 60, 63, 65, 67, 70, 72]
    inv = (2 * len(ITEMS)).to_bytes(2, 'big') + b''.join((i << 4).to_bytes(2, 'big') for i in ITEMS)
    em.write(0xFFFFDE80, inv)
    em.write(0xFFFFDF20, b''.join(bytes([level, 0]) for level in range(1, 17)))
    em.write(0xFFFFD026, (1).to_bytes(2, 'big')); em.write(0xFFFFC100, b'\xC0'); em.frames(10)   # Mieu active
    def menu(downs, extra=()):
        em.press('C'); em.frames(90)
        for _ in range(downs): em.press('D'); em.frames(20)
        em.press('C'); em.frames(60)
        for k in extra:
            em.press(k); em.frames(60)
        for _ in range(6):
            em.press('B'); em.frames(60)
        while em.word(0xFFFFD022) != 0x5A:
            em.press('B'); em.frames(90)
    print('--- menu: item, item action, give (whose?)', flush=True)
    menu(0, ('C', 'C', 'D', 'C'))
    print('--- menu: techs', flush=True); menu(1, ('C', 'C'))
    print('--- menu: stats', flush=True); menu(2, ('C', 'C'))
    print('--- menu: equip', flush=True); menu(3, ('C', 'C'))
    print('--- menu: switch', flush=True); menu(4, ('R',))
    # shops of each kind (map $222 + 2*kind), through the store-entry flag
    em.write(0xFFFFC040, (50000).to_bytes(4, 'big'))
    em.write(0xFFFFD068, b''.join((i * 16).to_bytes(2, 'big') for i in (10, 11, 12, 14, 15)) + b'\xFF\xFF')
    for kind in range(8):
        print('--- shop kind', kind, flush=True)
        em.write(0xFFFFD02A, bytes([kind, 0])); em.write(0xFFFFD006, bytes([em.byte(0xFFFFD006) | 0x10]))
        for _ in range(300):
            em.frames(1)
            if em.word(0xFFFFD022) == 0x222 + kind * 2: break
        else:
            print('   (did not open)', flush=True); continue
        em.frames(120)
        for k in ('C', 'C', 'C', 'D', 'C', 'B', 'B', 'B', 'B'):
            em.press(k); em.frames(60)
        for _ in range(400):
            if em.word(0xFFFFD022) == 0x5A: break
            em.press('B'); em.frames(30)
        em.frames(60)
    print('--- done: %d distinct fixed-width calls' % len(seen), flush=True)
