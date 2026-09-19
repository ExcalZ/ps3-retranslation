import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
from ps3harness import Symbols
sym = Symbols()
with PS3('ps3en.bin') as em:
    boot_to_field(em)
    em.write(0xFFFFC040, (50000).to_bytes(4, 'big'))
    em.write(0xFFFFD02A, b'\x07\x00'); em.write(0xFFFFD006, bytes([em.byte(0xFFFFD006) | 0x10]))
    em.frames(150)
    em.press('C'); em.frames(240)
    trap = sym['ErrorTrap']
    em.breakpoint(trap)
    hit = []
    def hook(pc):
        if pc == trap:
            r = em.regs(); sp = r['a'][7]
            hit.append((r, em.read(sp, 16)))
            raise SystemExit('trap')
    em.press('C', hook=hook)
    try:
        em.frames(120, hook=hook)
    except SystemExit:
        pass
    for r, frame in hit:
        print('ErrorTrap hit; sr/pc frame:', frame.hex(' '))
        print('regs a:', [hex(x) for x in r['a']], 'd:', [hex(x) for x in r['d']])
