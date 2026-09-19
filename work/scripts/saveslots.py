"""Save in the Landen chapel into slots 3 and 1, soft-reset, and walk the game select:
the four-row lists, continue and erase. Screenshots at every step."""
import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
shots = []
def shot(em, name):
    em.shot('work/analysis/ss_%s.png' % name); shots.append(name)
    print(name, 'routine', hex(em.word(0xFFFFD284)), 'D', em.byte(0xFFFFD28D), '1C', hex(em.word(0xFFFFD29C)), flush=True)
def church(em):
    em.write(0xFFFFD02A, b'\x07\x00'); em.write(0xFFFFD006, bytes([em.byte(0xFFFFD006) | 0x10]))
    em.frames(150)
with PS3('ps3en.bin') as em:
    boot_to_field(em)
    entry = int.from_bytes(em.read(4, 4), 'big')
    em.write(0xFFFFC040, (50000).to_bytes(4, 'big'))
    church(em); shot(em, 'c0')
    em.press('C'); em.frames(240); shot(em, 'c1')         # rest -> YES; fade; "OK to save?"
    em.press('C'); em.frames(90); shot(em, 'c2')          # YES -> the list
    em.press('D'); em.frames(20); em.press('D'); em.frames(20); shot(em, 'c3')   # cursor on slot 3
    em.press('C'); em.frames(120); shot(em, 'c4')         # saved in 3
    for _ in range(4): em.press('C'); em.frames(60)
    shot(em, 'c5')
    print('slot3 hdr', em.read(0x203001, 8).hex(), 'copy', em.read(0x207001, 8).hex(), flush=True)
    soft_reset(em)
    em.frames(60); em.press('S')
    while em.word(0xFFFFD012) != SCREEN_GAMESEL: em.frames(1)
    em.frames(150)
    for k in range(8):
        shot(em, 'g%d' % k); em.press('C'); em.frames(90)
    # now at the continue/new/erase menu (hopefully): choose Continue -> list
    shot(em, 'menu'); em.press('C'); em.frames(120); shot(em, 'list')
    em.press('D'); em.frames(20); shot(em, 'list2')
    em.press('C'); em.frames(120); shot(em, 'loaded')
    for _ in range(3): em.press('C'); em.frames(90)
    shot(em, 'end'); print('map', hex(em.word(0xFFFFD022)), 'level', em.byte(0xFFFFC0AD), flush=True)
