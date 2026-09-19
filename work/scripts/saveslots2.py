"""Two saves (slots 3 and 1): the continue list, erase list with cursor skipping empty
rows, erase slot 3, continue slot 1."""
import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
def shot(em, name):
    em.shot('work/analysis/s2_%s.png' % name)
    print(name, 'routine', hex(em.word(0xFFFFD284)), 'D', em.byte(0xFFFFD28D), '1C', hex(em.word(0xFFFFD29C)), 'map', hex(em.word(0xFFFFD022)), flush=True)
def inn_save(em, downs):
    em.write(0xFFFFC040, (50000).to_bytes(4, 'big'))
    em.write(0xFFFFD02A, b'\x07\x00'); em.write(0xFFFFD006, bytes([em.byte(0xFFFFD006) | 0x10]))
    em.frames(150); em.press('C'); em.frames(240); em.press('C'); em.frames(90)
    for _ in range(downs): em.press('D'); em.frames(20)
    em.press('C'); em.frames(120)
    for _ in range(4): em.press('C'); em.frames(60)
def to_gamesel(em):
    soft_reset(em); em.frames(60); em.press('S')
    while em.word(0xFFFFD012) != SCREEN_GAMESEL: em.frames(1)
    em.frames(150)
    while em.word(0xFFFFD284) != 0x7C:          # the continue/new/erase menu state
        em.press('C', hold=2, release=30)
    em.frames(30)
with PS3('ps3en.bin') as em:
    boot_to_field(em)
    inn_save(em, 2)                                # slot 3
    to_gamesel(em); shot(em, 'menu1')
    em.press('C'); em.frames(120)                  # continue (one save: auto)
    while em.word(0xFFFFD012) != SCREEN_MAIN: em.press('C', hold=2, release=30)
    em.frames(60); shot(em, 'field1')
    inn_save(em, 0)                                # slot 1
    to_gamesel(em); shot(em, 'menu2')
    em.press('C'); em.frames(120); shot(em, 'cont_list')       # "which game" + list
    em.press('D'); em.frames(20); shot(em, 'cont_down')        # cursor 1 -> 3 (skips 2)
    em.press('D'); em.frames(20); shot(em, 'cont_down2')       # 3 -> 1 (wraps, skips 4)
    em.press('B'); em.frames(120); shot(em, 'back')            # back to the menu
    em.press('D'); em.frames(20); em.press('D'); em.frames(20); em.press('C'); em.frames(120); shot(em, 'erase_list')
    em.press('D'); em.frames(20); em.press('C'); em.frames(120); shot(em, 'erase_confirm')   # slot 3
    em.press('C'); em.frames(120); shot(em, 'erased')
    for _ in range(3): em.press('C'); em.frames(90)
    shot(em, 'menu3')
    em.press('C'); em.frames(120); shot(em, 'cont2')
    while em.word(0xFFFFD012) != SCREEN_MAIN: em.press('C', hold=2, release=30)
    em.frames(60); shot(em, 'field2')
    print('slot1 name', em.sram(0)[0x28:0x30], 'slot3 hdr byte', em.sram(2)[2], flush=True)
