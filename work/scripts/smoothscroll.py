"""The smooth page scroll in BlastEm: the multi-page legend text from a Landen NPC, frames
captured during the scroll at speed 5 (1 px/frame) and speed 1 (1 px per 4 frames), and
the settled pages after. Screenshots ss2_*.png."""
import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
def scroll_frames(em, tag, every):
    em.press('A', hold=2, release=2)
    shots = 0
    for f in range(400):
        em.frames(1)
        if em.word(0xFFFFFA14) == 1 and f % every == 0 and shots < 6:      # VWFSmooth_Active
            em.shot('work/analysis/ss2_%s_%d.png' % (tag, shots)); shots += 1
        if em.word(0xFFFFD284) == 8 and em.word(0xFFFFFA14) == 0 and shots:
            break
    em.frames(5); em.shot('work/analysis/ss2_%s_done.png' % tag)
    print(tag, 'shots', shots, 'routine', hex(em.word(0xFFFFD284)), flush=True)
with PS3(sys.argv[1] if len(sys.argv) > 1 else 'ps3en.bin') as em:
    boot_to_field(em)
    em.frames(60)
    i, nx, ny, so = npc_list(em)[-1]
    em.write(0xFFFFC300 + i * 0x40 + 0x26, (0x1A).to_bytes(2, 'big'))   # loc_25F24: the multi-page legend
    em.write(0xFFFFD11C, bytes([0x48]))                                  # speed 5
    talk(em, nx, ny)
    em.frames(90); em.shot('work/analysis/ss2_open.png')
    scroll_frames(em, 'speed5', 3)
    scroll_frames(em, 'speed5b', 3)
    em.write(0xFFFFD11C, bytes([0x88]))                                  # speed 1
    scroll_frames(em, 'speed1', 10)
    em.write(0xFFFFD11C, bytes([0x08]))                                  # speed 9
    scroll_frames(em, 'speed9', 1)
    for _ in range(30):
        em.press('A', hold=2, release=10)
        if em.word(0xFFFFD284) not in (8, 0xC, 0x10): break
    em.frames(30); em.shot('work/analysis/ss2_closed.png'); print('routine', hex(em.word(0xFFFFD284)))
    em.press('C')
    while em.word(0xFFFFD022) != 0x202: em.frames(1)
    em.frames(40); em.shot('work/analysis/ss2_menu.png')
