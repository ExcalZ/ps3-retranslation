import sys; sys.path.insert(0, 'tools')
from ps3emu import *
with PS3('ps3en.bin') as em:
    em.frames(5)
    print('regs', hex(em.pc()))
    print('P11 reply:', repr(em.cmd('P11=%08x' % 0x206)))
    print('pc now', hex(em.pc()))
    print('P17 reply:', repr(em.cmd('P17=%08x' % 0x206)))
    print('pc now', hex(em.pc()))
    print('g:', em.cmd('g')[:80])
