"""The small windows that still draw fixed-width: the Technique "Who?" prompt over the
main menu, the Item "Whose?" list, the shop's BUY/SEL/MES labels and its name list.
Two-member party (Kein + Mieu). Screenshots: work/analysis/sw_*.png."""
import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *

def shot(em, name):
    em.shot('work/analysis/sw_%s.png' % name)
    print(name, 'map', hex(em.word(0xFFFFD022)), 'routine', hex(em.word(0xFFFFD284)), '$2', hex(em.word(0xFFFFD282)), flush=True)

with PS3(sys.argv[1] if len(sys.argv) > 1 else 'ps3en.bin') as em:
    boot_to_field(em); em.frames(60)
    ITEMS = [10, 11, 12, 14, 15, 16, 17, 20, 22, 60, 63, 65, 67, 70, 72]
    inv = (2 * len(ITEMS)).to_bytes(2, 'big') + b''.join((i << 4).to_bytes(2, 'big') for i in ITEMS)
    em.write(0xFFFFDE80, inv)
    em.write(0xFFFFDF20, b''.join(bytes([level, 0]) for level in range(1, 17)))
    em.write(0xFFFFD026, (1).to_bytes(2, 'big')); em.write(0xFFFFC100, b'\xC0'); em.frames(10)   # Mieu active
    # Technique -> "Who?"
    em.press('C'); em.frames(90); shot(em, 'main')
    em.press('D'); em.frames(20); em.press('C'); em.frames(90); shot(em, 'tech_who')
    em.press('D'); em.frames(30); shot(em, 'tech_who_down')
    for _ in range(4): em.press('B'); em.frames(60)
    while em.word(0xFFFFD022) != 0x5A: em.press('B'); em.frames(90)
    # Item -> first item -> Use -> "Whose?"
    em.press('C'); em.frames(90); em.press('C'); em.frames(90); em.press('C'); em.frames(90); shot(em, 'item_action')
    em.press('C'); em.frames(90); shot(em, 'item_whose')
    em.press('D'); em.frames(30); shot(em, 'item_whose_down')
    for _ in range(5): em.press('B'); em.frames(60)
    while em.word(0xFFFFD022) != 0x5A: em.press('B'); em.frames(90)
    # a weapon shop: list, buy, "who carries it?"
    em.write(0xFFFFC040, (50000).to_bytes(4, 'big'))
    em.write(0xFFFFD068, b''.join((i * 16).to_bytes(2, 'big') for i in (10, 11, 12, 14, 15)) + b'\xFF\xFF')
    em.write(0xFFFFD02A, bytes([1, 0])); em.write(0xFFFFD006, bytes([em.byte(0xFFFFD006) | 0x10]))
    while em.word(0xFFFFD022) != 0x224: em.frames(1)
    em.frames(150); shot(em, 'shop')
    em.press('C'); em.frames(90); shot(em, 'shop_buy')
    em.press('C'); em.frames(90); shot(em, 'shop_list')
    em.press('C'); em.frames(90); shot(em, 'shop_who')
    em.press('D'); em.frames(30); shot(em, 'shop_who_down')
