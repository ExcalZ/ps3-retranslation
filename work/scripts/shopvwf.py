"""Shop lists in the proportional face: a weapon shop stocked with five long names (buy
list, cursor, purchase), then the sell flow. Screenshots to work/analysis/sv_*.png."""
import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
STOCK = [63, 65, 67, 14, 36]          # record numbers: five nine-cell names
def shot(em, name):
    em.shot('work/analysis/sv_%s.png' % name)
    print(name, 'map', hex(em.word(0xFFFFD022)), 'routine', hex(em.word(0xFFFFD284)), flush=True)
def enter(em, kind):
    em.write(0xFFFFC040, (50000).to_bytes(4, 'big'))
    em.write(0xFFFFD068, b''.join((i * 16).to_bytes(2, 'big') for i in STOCK) + b'\xFF\xFF')
    em.write(0xFFFFD02A, bytes([kind, 0])); em.write(0xFFFFD006, bytes([em.byte(0xFFFFD006) | 0x10]))
    while em.word(0xFFFFD022) != 0x222 + kind * 2: em.frames(1)
    em.frames(60)
with PS3(sys.argv[1] if len(sys.argv) > 1 else 'ps3en.bin') as em:
    boot_to_field(em)
    sell = (10, 11, 12, 14, 15, 16, 17, 20)
    inv = (2 * len(sell)).to_bytes(2, 'big') + b''.join((i << 4).to_bytes(2, 'big') for i in sell)
    em.write(0xFFFFDE80, inv)                       # Rhys carries eight weapons to sell: two list pages
    em.frames(10)
    enter(em, 0)
    em.press('C'); em.frames(120); shot(em, 'greet')
    em.press('C'); em.frames(120); shot(em, 'buylist')          # BUY -> the list
    em.press('D'); em.frames(30); shot(em, 'buy_down')
    em.press('C'); em.frames(90); shot(em, 'buy_who')
    em.press('C'); em.frames(120); shot(em, 'bought')
    em.press('B'); em.frames(90); em.press('B'); em.frames(90); shot(em, 'back')   # to the BUY/SEL box
    em.press('D'); em.frames(30); em.press('C'); em.frames(120); shot(em, 'sell1')   # SEL: who sells?
    em.press('C'); em.frames(120); shot(em, 'sell2')                                 # Rhys's list
    em.press('D'); em.frames(30); shot(em, 'sell_down')
    for _ in range(5): em.press('D'); em.frames(20)
    shot(em, 'sell_page2')                                                          # past the fifth: page two
    em.press('U'); em.frames(30); shot(em, 'sell_page2_up')
    em.press('C'); em.frames(120); shot(em, 'sell3')                                 # offer
    em.press('C'); em.frames(120); shot(em, 'sell4')                                 # sold
    while em.word(0xFFFFD022) != 0x5A: em.press('B', hold=2, release=60)
    em.frames(60); shot(em, 'field')
    em.press('C')
    while em.word(0xFFFFD022) != 0x202: em.frames(1)
    em.frames(40); shot(em, 'menu_after')
