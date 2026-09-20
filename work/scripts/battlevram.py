"""Reach the first random battle and record which tiles plane A, plane B and the sprites
reference on the battle screen (map $232), at the box, during the command grid and
during a character's stat window."""
import sys, os; sys.path.insert(0, 'tools')
from ps3emu import *
def usage(em, label):
    out = {}
    for name, base in (('planeA', 0xFFFF2000), ('planeB', 0xFFFF3200)):
        d = em.read(base, 0xE00)
        tiles = sorted(set(int.from_bytes(d[i:i+2], 'big') & 0x7FF for i in range(0, 0xE00, 2)))
        out[name] = tiles
    spr = em.read(0xFFFFD400, 0x280)
    st = set()
    for i in range(0, 0x280, 8):
        size = spr[i+2] & 0xF
        if spr[i] == 0 and spr[i+1] == 0 and spr[i+4] == 0 and spr[i+5] == 0: continue
        w, h = ((size >> 2) & 3) + 1, (size & 3) + 1
        t = int.from_bytes(spr[i+4:i+6], 'big') & 0x7FF
        st.update(range(t, t + w * h))
    out['sprites'] = sorted(st)
    used = sorted(set(out['planeA']) | set(out['planeB']) | st)
    print('==', label, 'planeA %d tiles (max $%X)  planeB %d (max $%X)  sprites %d' % (
        len(out['planeA']), max(out['planeA']), len(out['planeB']), max(out['planeB']), len(st)), flush=True)
    # free runs above the font
    free, start = [], 0x100
    for t in used + [0x540]:
        if t >= 0x100 and t - start >= 16:
            free.append((start, t - 1))
        start = max(start, t + 1)
    print('   free runs (>=16) up to $540:', ['$%X-$%X (%d)' % (a, b, b - a + 1) for a, b in free], flush=True)
    print('   planeA >$FF:', ' '.join('%X' % t for t in out['planeA'] if t > 0xFF)[:400], flush=True)
    return out
with PS3(sys.argv[1] if len(sys.argv) > 1 else 'ps3en.bin') as em:
    boot_to_field(em)
    teleport(em, 0x00, 1744, 312, facing=0x3818)
    em.frames(120)
    dirs = ['U', 'L', 'D', 'R']
    for i in range(400):
        em.pad = BUTTON[dirs[i % 4]]; em.frames(24); em.pad = 0; em.frames(2)
        if em.word(0xFFFFD022) == 0x232: break
    print('battle at frame', em.frame, flush=True)
    em.frames(150); em.shot('work/analysis/bv_box.png'); usage(em, 'box (ambush message)')
    em.press('A'); em.frames(60); em.shot('work/analysis/bv_1.png'); usage(em, 'after A')
    em.press('A'); em.frames(60); em.shot('work/analysis/bv_2.png'); usage(em, 'after A again')
    em.press('C'); em.frames(60); em.shot('work/analysis/bv_3.png'); usage(em, 'after C')
    em.press('C'); em.frames(60); em.shot('work/analysis/bv_4.png'); usage(em, 'after C again')
