"""Save BlastEm states on the screens where the dialogue box appears and audit their VRAM:
Landen, a shop greeting, the world map, a dungeon-like map, the game-select narration."""
import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
from vramaudit import audit
S = 'work/states'
with PS3('ps3en.bin') as em:
    boot_to_field(em)
    audit(save_state(em, S + '/landen.state'), 'Landen town')
    em.write(0xFFFFC040, (50000).to_bytes(4, 'big'))
    em.write(0xFFFFD02A, bytes([0, 0])); em.write(0xFFFFD006, bytes([em.byte(0xFFFFD006) | 0x10]))
    while em.word(0xFFFFD022) != 0x222: em.frames(1)
    em.frames(60); em.press('C'); em.frames(120)
    audit(save_state(em, S + '/shop.state'), 'weapon shop, greeting')
    while em.word(0xFFFFD022) != 0x5A: em.press('B', hold=2, release=60)
    em.frames(60)
    teleport(em, 0x00, 1744, 312, facing=0x3818); em.frames(120)
    audit(save_state(em, S + '/world.state'), 'world map')
    # a few more field maps by id, first door position: whatever the map's art needs
    for mid in (0x10, 0x40, 0x80, 0xC0):
        teleport(em, mid, 256, 256); em.frames(60)
        audit(save_state(em, S + '/map%02X.state' % mid), 'map $%X' % mid)
        em.shot('work/analysis/vs_map%02X.png' % mid)
