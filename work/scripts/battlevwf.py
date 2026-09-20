"""Battle box in the proportional face: the enemy-group row, the stat window's names, the
command grid and the item list. Rhys carries three long-named items; Mieu is added to the
party with the two-character fixture so a second name shows. Screenshots bv2_*.png."""
import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
def shot(em, name):
    em.shot('work/analysis/bv2_%s.png' % name)
    print(name, 'map', hex(em.word(0xFFFFD022)), 'routine', hex(em.word(0xFFFFD284)), flush=True)
with PS3(sys.argv[1] if len(sys.argv) > 1 else 'ps3en.bin') as em:
    boot_to_field(em)
    inv = (2 * 4).to_bytes(2, 'big') + (0x8000 | (10 << 4) | 2).to_bytes(2, 'big') + b''.join((i << 4).to_bytes(2, 'big') for i in (0, 4, 6))   # Steel Swd equipped (right hand), Monomate, Star Mist, Escapipe
    em.write(0xFFFFDE80, inv)
    teleport(em, 0x00, 1744, 312, facing=0x3818)
    em.frames(120)
    dirs = ['U', 'L', 'D', 'R']
    for i in range(400):
        em.pad = BUTTON[dirs[i % 4]]; em.frames(24); em.pad = 0; em.frames(2)
        if em.word(0xFFFFD022) == 0x232: break
    print('battle at frame', em.frame, flush=True)
    em.frames(40); shot(em, 'ambush')                      # box with the enemy row + message
    em.frames(80); shot(em, 'row')
    while em.word(0xFFFFD284) not in (0x24, 0x1E4, 0x1E8): em.frames(1)
    em.frames(30); shot(em, 'grid')                        # main grid: Auto / One round / Char actions / Escape
    em.press('U'); em.frames(20); em.press('L'); em.frames(20); shot(em, 'grid_tl')
    em.press('R'); em.frames(30); shot(em, 'grid_tr')
    em.press('C'); em.frames(90); shot(em, 'chargrid')     # "character actions" chosen
    while em.word(0xFFFFD284) != 0x54:                      # Rhys's own grid
        em.press('C'); em.frames(60)
        if em.word(0xFFFFD022) != 0x232: break
    em.frames(30); shot(em, 'rhysgrid')
    em.press('U'); em.frames(20); em.press('L'); em.frames(20); shot(em, 'rhys_tl')
    em.press('C'); em.frames(90); shot(em, 'target')        # attack: target selection
    for k, key in enumerate(('R', 'R', 'L', 'D', 'U')):
        em.press(key); em.frames(30); shot(em, 'target_%d%s' % (k, key))
    em.press('B'); em.frames(60); shot(em, 'target_back')
    em.press('R'); em.frames(30); em.press('C'); em.frames(90); shot(em, 'itemlist')
    em.press('C'); em.frames(90); shot(em, 'item_target')     # ally selection?
    em.press('R'); em.frames(30); shot(em, 'item_target_R')
    em.press('B'); em.frames(60); em.press('B'); em.frames(60)
    em.press('D'); em.frames(30); em.press('L'); em.frames(30); em.press('C'); em.frames(90); shot(em, 'techlist')
    em.press('C'); em.frames(90); shot(em, 'tech_target')
    for k in range(20):
        em.press('B', hold=2, release=30)
        em.press('C', hold=2, release=30)
        if em.word(0xFFFFD022) != 0x232: break
    shot(em, 'after')
