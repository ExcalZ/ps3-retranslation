"""The indented prompts of the field menu: Item's "What?" and its Use/Give/Discard list,
Technique's "What?", and the Equip screen's "What?" (stock: hand-written tile words).
Their leading spaces are whole cells on the pool, so the text sits at column 17 like the
window's header. Screenshots: work/analysis/pr_*.png."""
import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *

def shot(em, name):
    em.shot('work/analysis/pr_%s.png' % name)
    print(name, 'map', hex(em.word(0xFFFFD022)), 'routine', hex(em.word(0xFFFFD284)), '$2', hex(em.word(0xFFFFD282)), flush=True)

def back_to_field(em):
    for _ in range(6):
        em.press('B'); em.frames(60)
    while em.word(0xFFFFD022) != 0x5A:
        em.press('B'); em.frames(90)

with PS3(sys.argv[1] if len(sys.argv) > 1 else 'ps3en.bin') as em:
    boot_to_field(em); em.frames(60)
    ITEMS = [10, 11, 12, 14, 15]
    inv = (2 * len(ITEMS)).to_bytes(2, 'big') + b''.join((i << 4).to_bytes(2, 'big') for i in ITEMS)
    em.write(0xFFFFDE80, inv)
    em.write(0xFFFFDF20, b''.join(bytes([level, 0]) for level in range(1, 17)))
    # Item -> What? -> Use list
    em.press('C'); em.frames(90); em.press('C'); em.frames(90); shot(em, 'item_who')
    em.press('C'); em.frames(90); shot(em, 'item_what')
    em.press('C'); em.frames(90); shot(em, 'item_use')
    em.press('D'); em.frames(30); shot(em, 'item_use_down')
    back_to_field(em)
    # Technique -> Who? -> What?
    em.press('C'); em.frames(90); em.press('D'); em.frames(20); em.press('C'); em.frames(90)
    em.press('C'); em.frames(90); shot(em, 'tech_what')
    back_to_field(em)
    # Equip -> Whose? -> What?
    em.press('C'); em.frames(90)
    for _ in range(3):
        em.press('D'); em.frames(20)
    em.press('C'); em.frames(90); em.press('C'); em.frames(90); shot(em, 'equip_what')
    em.press('D'); em.frames(30); shot(em, 'equip_what_down')
    back_to_field(em)
    shot(em, 'field')
