"""Take the Landen snapshot the long way, then resume it in a fresh BlastEm: time both,
screenshot both, and walk Rhys a few tiles after the resume to prove the field is live."""
import sys, os, time; sys.path.insert(0, 'tools')
from ps3emu import *
t0 = time.time()
with PS3('ps3en.bin') as em:
    boot_to_field(em)
    print('long boot: %.0f s, frame %d, pos %d,%d' % (time.time() - t0, em.frame, em.word(0xFFFFC008), em.word(0xFFFFC00A)), flush=True)
    em.shot('work/analysis/snap_long.png')
t0 = time.time()
with PS3('ps3en.bin') as em:
    boot_to_field(em)
    print('resumed: %.0f s, frame %d, map %s pos %d,%d' % (time.time() - t0, em.frame, hex(em.word(0xFFFFD022)), em.word(0xFFFFC008), em.word(0xFFFFC00A)), flush=True)
    em.shot('work/analysis/snap_resume.png')
    walk_to(em, em.word(0xFFFFC008) + 32, em.word(0xFFFFC00A))
    em.frames(30); em.shot('work/analysis/snap_walk.png')
    print('after walk: pos %d,%d' % (em.word(0xFFFFC008), em.word(0xFFFFC00A)), flush=True)
    em.press('C')
    while em.word(0xFFFFD022) != 0x202: em.frames(1)
    em.frames(40); em.shot('work/analysis/snap_menu.png'); print('menu ok', flush=True)
