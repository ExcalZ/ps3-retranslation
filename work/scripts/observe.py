"""Observe a hand-played BlastEm: the stub stays attached at the pad read but the pad is
passed through, so the player uses the keyboard (BlastEm defaults: arrows, A/S/D = A/B/C,
Enter = Start). Every frame logs map, dialogue routine, scroll state and the pad; every
600 frames saves a BlastEm state (work/states/observe-N.state) so the run can be replayed
from the last one with the recorded inputs. On a freeze (BlastEm stops the CPU) it tries
to interrupt the stub and read the registers.

    python work/scripts/observe.py [rom]
"""
import sys, os, socket, time; sys.path.insert(0, 'tools')
from ps3emu import *

rom = sys.argv[1] if len(sys.argv) > 1 else 'ps3en.bin'
log = open('work/analysis/observe.log', 'w')
inputs = []
with PS3(rom) as em:
    em.sock.settimeout(8)
    n_state = 0
    print('BlastEm is up: play in its window. Ctrl+C here to stop.', flush=True)
    try:
        while True:
            try:
                pc = em.cont()
            except socket.timeout:
                print('no pad read for 8 s: the CPU has stopped', flush=True)
                try:
                    em.sock.sendall(b'\x03')
                    r = em.regs()
                    print('regs after interrupt:', {k: (hex(v) if isinstance(v, int) else [hex(x) for x in v]) for k, v in r.items()}, flush=True)
                    pcv = r['pc']
                    print('code at pc:', em.read(pcv - 16, 32).hex(' '), flush=True)
                except Exception as e:
                    print('stub did not answer after the freeze:', e, flush=True)
                break
            if pc != em.pad_bp:
                continue
            a1 = em.regs()['a'][1]
            if a1 != 0xFFFFD000:
                continue
            em.frame += 1
            pad = em.regs()['d'][0] & 0xFF
            inputs.append(pad)
            if em.frame % 4 == 0 or pad:
                rec = (em.frame, pad, em.word(0xFFFFD022), em.word(0xFFFFD012), em.word(0xFFFFD284), em.word(0xFFFFFA14), em.word(0xFFFFFA10))
                log.write('%d pad %02X map %04X screen %04X routine %04X active %d acc %d\n' % rec)
            if em.frame % 600 == 0:
                log.flush()
                n_state += 1
                path = 'work/states/observe-%d.state' % n_state
                save_state(em, path)
                open('work/states/observe-%d.inputs' % n_state, 'w').write('')   # inputs from here on
                inputs = []
                print('state %d saved at frame %d' % (n_state, em.frame), flush=True)
    except KeyboardInterrupt:
        print('stopped by hand', flush=True)
    finally:
        log.flush()
        if n_state:
            open('work/states/observe-%d.inputs' % n_state, 'w').write(' '.join('%02X' % p for p in inputs))
        print('last state %d, %d inputs since' % (n_state, len(inputs)), flush=True)
