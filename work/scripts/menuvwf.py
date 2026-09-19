"""Field menu with the proportional face: item screen (15 distinct names), Stats pages,
Equip screen. Screenshots to work/analysis/mv_*.png."""
import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
ITEMS = [10, 11, 12, 14, 15, 16, 17, 20, 22, 60, 63, 65, 67, 70, 72]
def shot(em, name):
    em.shot('work/analysis/mv_%s.png' % name)
    print(name, 'routine', hex(em.word(0xFFFFD284)), '$2', hex(em.word(0xFFFFD282)), 'map', hex(em.word(0xFFFFD022)), flush=True)
def in_menu(em):
    return 0x202 <= em.word(0xFFFFD022) <= 0x20C
def to_menu(em):
    for attempt in range(4):
        if in_menu(em):
            break
        print('open menu attempt', attempt + 1, 'map', hex(em.word(0xFFFFD022)), flush=True)
        em.press('C'); em.frames(90)
    else:
        raise RuntimeError('menu did not open: map %04X routine %04X substate %04X' % (
            em.word(0xFFFFD022), em.word(0xFFFFD284), em.word(0xFFFFD282)))
    em.frames(40)
def to_field(em):
    for attempt in range(4):
        if em.word(0xFFFFD022) == 0x5A:
            return
        print('close menu attempt', attempt + 1, 'map', hex(em.word(0xFFFFD022)), flush=True)
        em.press('B'); em.frames(90)
    raise RuntimeError('menu did not close: map %04X routine %04X substate %04X' % (
        em.word(0xFFFFD022), em.word(0xFFFFD284), em.word(0xFFFFD282)))
def pick(em, downs, routine):
    for _ in range(downs): em.press('D'); em.frames(20)
    em.press('C'); em.frames(60); em.press('C'); em.frames(90)
    if not in_menu(em) or em.word(0xFFFFD284) != routine:
        raise RuntimeError('wrong menu: wanted routine %04X, got map %04X routine %04X substate %04X' % (
            routine, em.word(0xFFFFD022), em.word(0xFFFFD284), em.word(0xFFFFD282)))
with PS3(sys.argv[1] if len(sys.argv) > 1 else 'ps3en.bin') as em:
    print('booting', flush=True)
    boot_to_field(em)
    print('field map', hex(em.word(0xFFFFD022)), 'screen', hex(em.word(0xFFFFD012)), flush=True)
    inv = (2 * len(ITEMS)).to_bytes(2, 'big') + b''.join((i << 4).to_bytes(2, 'big') for i in ITEMS)
    inv = inv[:2] + (0x8000 | (10 << 4) | 2).to_bytes(2, 'big') + inv[4:]      # first item equipped (R hand)
    em.write(0xFFFFDE80, inv)
    em.write(0xFFFFDF20, b''.join(bytes([level, 0]) for level in range(1, 17)))
    em.frames(10)
    to_menu(em); shot(em, 'main')
    pick(em, 0, 4); shot(em, 'items')
    em.press('C'); em.frames(60); shot(em, 'items_action')          # Use/Give/Discard
    em.press('B'); em.frames(60); em.press('B'); em.frames(60); em.press('B'); em.frames(90)
    to_field(em)
    shot(em, 'back')
    to_menu(em)
    pick(em, 2, 0xC); shot(em, 'stats1')
    em.press('C'); em.frames(90); shot(em, 'stats2')
    em.press('C'); em.frames(90); shot(em, 'stats3')
    em.press('B'); em.frames(60); em.press('B'); em.frames(60); em.press('B'); em.frames(60); em.press('B'); em.frames(90)
    to_field(em)
    shot(em, 'back2')
    to_menu(em)
    pick(em, 3, 0x10); shot(em, 'equip')
    em.press('D'); em.frames(30); shot(em, 'equip_down')
    em.press('B'); em.frames(90); to_field(em)
    to_menu(em)
    pick(em, 1, 8); shot(em, 'techs')
    em.press('B'); em.frames(90); to_field(em)
    em.write(0xFFFFD01E, (1).to_bytes(2, 'big'))
    to_menu(em); shot(em, 'gen2_main')
    pick(em, 0, 4); shot(em, 'gen2_items')
