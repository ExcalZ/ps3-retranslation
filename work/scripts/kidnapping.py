"""Regression for the wedding escort and Rhys's scripted walk to prison.

    python work/scripts/kidnapping.py ps3en.bin [pre-wedding.state]

The optional state can be a BlastEm state just before walking into the wedding
trigger, with a matching .ram file. Without it, boot a new game and teleport to
the trigger. The controller must finish its prison route at the cell entrance.
"""
import os
import sys

sys.path.insert(0, 'tools')
from ps3emu import PS3, boot_to_field, teleport


rom = sys.argv[1] if len(sys.argv) > 1 else 'ps3en.bin'
state_path = sys.argv[2] if len(sys.argv) > 2 else None
lst = os.path.splitext(rom)[0] + '.lst'
if not os.path.exists(lst):
    lst = 'PSIII_Disasm/ps3.lst'

with PS3(rom, lst=lst, state=state_path) as em:
    if state_path:
        em.pad = 1
        em.frames(8)
        em.pad = 0
    else:
        boot_to_field(em)
        teleport(em, 0x3C, 0x150, 0x1C0)
    previous = None
    for i in range(1500):
        em.press('C', hold=2, release=6)
        state = (em.word(0xFFFFD022), em.byte(0xFFFFBF02),
                 em.byte(0xFFFFBF03), em.byte(0xFFFFBF04))
        if state != previous:
            print('frame', em.frame, 'map/phase/dragon/prison', state,
                  'Rhys', (em.word(0xFFFFC008), em.word(0xFFFFC00A)), flush=True)
            previous = state
        if em.word(0xFFFFD022) == 0x78 and em.byte(0xFFFFBF04):
            em.frames(8)  # the last tile step finishes after the controller exits
            pos = (em.word(0xFFFFC008), em.word(0xFFFFC00A))
            assert pos == (0x2F0, 0x1B0), ('Rhys missed the cell entrance', pos)
            assert em.byte(0xFFFFD3C0) == 0, 'demo speed flag still set'
            assert em.word(0xFFFFD242) == 2, '2x field speed not restored'
            print('Rhys reached the cell entrance at frame', em.frame, flush=True)
            break
    else:
        raise AssertionError('prison demo did not finish within 12000 frames')
