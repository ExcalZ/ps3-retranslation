"""Reload an observe state, replay the recorded inputs, and catch the exception that
looks like a hard reset: break at the entry point (every exception vector of this game
lands there) and read the exception frame off the stack.

    python work/scripts/replay.py 19
"""
import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
n = int(sys.argv[1])
inputs = [int(x, 16) for x in open('work/states/observe-%d.inputs' % n).read().split()]
print('state', n, 'inputs', len(inputs), flush=True)
with PS3('ps3en.bin', state='work/states/observe-%d.state' % n) as em:
    entry = int.from_bytes(em.read(4, 4), 'big')
    em.breakpoint(entry)
    print('resumed at map', hex(em.word(0xFFFFD022)), 'routine', hex(em.word(0xFFFFD284)), flush=True)
    hit = None
    def hook(pc):
        global hit
        if pc == entry:
            hit = pc
    for i, pad in enumerate(inputs + [0] * 600):
        em.pad = pad
        em.step_frame(hook)
        if hit:
            r = em.regs()
            sp = r['a'][7]
            frame = em.read(sp, 16)
            print('exception -> entry at frame', i, 'map', hex(em.word(0xFFFFD022)), 'routine', hex(em.word(0xFFFFD284)),
                  'active', em.word(0xFFFFFA14), flush=True)
            print('sp', hex(sp), 'stack:', frame.hex(' '), flush=True)
            print('regs', {k: (hex(v) if isinstance(v, int) else [hex(x) for x in v]) for k, v in r.items()}, flush=True)
            break
        if i % 100 == 0:
            print(i, 'map', hex(em.word(0xFFFFD022)), 'routine', hex(em.word(0xFFFFD284)), 'active', em.word(0xFFFFFA14), flush=True)
    else:
        print('no exception; map', hex(em.word(0xFFFFD022)))
