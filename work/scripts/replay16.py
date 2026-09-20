import sys, os, socket; sys.path.insert(0, 'tools')
from ps3emu import *
with PS3('ps3en.bin', state='work/states/observe-15.state') as em:
    entry = int.from_bytes(em.read(4, 4), 'big'); em.breakpoint(entry)
    hit = []
    def hook(pc):
        if pc == entry: hit.append(em.frame)
    last = None
    try:
        for i in range(2200):
            em.step_frame(hook)
            if hit: print('EXCEPTION at', i); break
            st = (em.word(0xFFFFD022), em.word(0xFFFFD284) & 0xFF0F)
            if st != last or i % 300 == 0:
                print('f%d map %04X screen %04X routine %04X active %d' % (9007 + i, st[0], em.word(0xFFFFD012), em.word(0xFFFFD284), em.word(0xFFFFFA14)), flush=True)
                last = st
            if i in (600, 1330, 1400, 1600, 2000): em.shot('work/analysis/r16_%d.png' % i)
    except (socket.timeout, ConnectionResetError) as e:
        print('connection lost at frame', 9007 + em.frame, e)
    print('end: map', hex(em.word(0xFFFFD022)), 'screen', hex(em.word(0xFFFFD012)))
