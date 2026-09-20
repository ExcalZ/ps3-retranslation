"""VRAM audit from a BlastEm .state: which tiles the nametables and the sprite table
reference, which tiles hold data, and the free runs.

    python tools/vramaudit.py path.state [label]
"""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
ROM = os.path.join(os.path.dirname(HERE), 'PSIII_Disasm', 'ps3original.bin')


def read_state(path):
    """VRAM, CRAM, VSRAM and the VDP registers of a BlastEm .state. The VDP block is found
    by the game's font, which sits at VRAM $0000 on every screen (loc_66000)."""
    data = open(path, 'rb').read()
    v = None
    if data[:6] == b'BLSTSZ' and data[6:8] == b'':
        v = 0xAD            # BlastEm 0.6.2: the VDP section is first, its VRAM at this offset
    ramfile = os.path.splitext(path)[0] + '.ram'
    if v is None and os.path.exists(ramfile):
        # the plane A buffer ($FFFF2000, 28 rows of $80) is copied to VRAM $C000: find a
        # distinctive row of it in the state
        ram = open(ramfile, 'rb').read()
        for row in range(28):
            win = ram[0x2000 + row * 0x80:0x2000 + row * 0x80 + 0x50]
            if len(set(win)) < 6:
                continue
            hits = []
            i = data.find(win)
            while i >= 0:
                hits.append(i); i = data.find(win, i + 1)
            hits = [h for h in hits if data[h - 1:h] != ram[0x2000 + row * 0x80 - 1:0x2000 + row * 0x80] or True]
            cands = set(h - 0xC000 - row * 0x80 for h in hits)
            cands = [c for c in cands if 0 <= c and c + 0x10000 <= len(data)]
            if len(cands) == 1:
                v = cands[0]; break
    if v is None:
        font = open(ROM, 'rb').read()[0x66000 + 0x400:0x66000 + 0x1000]     # tiles $20-$7F, at VRAM $0000 in the game
        i = data.find(font)
        assert i > 0 and data.find(font, i + 1) < 0, 'VDP block not found (no .ram beside the state, and the font is not at $0000 once)'
        v = i - 0x400
    return {'vram': data[v:v + 0x10000],
            'cram': struct.unpack('>64H', data[v + 0x10000:v + 0x10080]),
            'vsram': struct.unpack('>40H', data[v + 0x10080:v + 0x100D0]),
            'regs': data[v + 0x100D0 + 0x140:v + 0x100D0 + 0x140 + 24]}


def audit(path, label=''):
    st = read_state(path)
    vram, regs = st['vram'], st['regs']
    ntA = (regs[2] & 0x38) << 10
    ntB = (regs[4] & 7) << 13
    ntW = (regs[3] & 0x3E) << 10
    sat = (regs[5] & 0x7F) << 9
    hs = (regs[13] & 0x3F) << 10
    h40 = bool(regs[12] & 0x81)
    size = {0: 32, 1: 64, 3: 128}
    w, h = size[regs[16] & 3], size[(regs[16] >> 4) & 3]
    ref = {}
    for name, base in (('A', ntA), ('B', ntB)):
        s = set()
        for i in range(w * h):
            word = (vram[base + i * 2] << 8) | vram[base + i * 2 + 1]
            s.add(word & 0x7FF)
        ref[name] = s
    spr = set()
    for i in range(80):
        e = vram[sat + i * 8: sat + i * 8 + 8]
        sz = e[2] & 0xF
        t = ((e[4] << 8) | e[5]) & 0x7FF
        if e[0] | e[1] | e[4] | e[5]:
            spr.update(range(t, t + ((sz >> 2) + 1) * ((sz & 3) + 1)))
    ref['S'] = spr
    data = set(t for t in range(0x800) if any(vram[t * 32:t * 32 + 32]))
    tables = set()
    for base, n in ((ntA, w * h * 2), (ntB, w * h * 2), (sat, 640), (hs, 0x380)):
        tables.update(range(base // 32, (base + n + 31) // 32))
    if regs[18] or regs[17]:
        tables.update(range(ntW // 32, (ntW + w * h * 2 + 31) // 32))
    used = ref['A'] | ref['B'] | ref['S'] | tables
    print('== %s  planeA $%X planeB $%X window $%X%s sprites $%X hscroll $%X  %dx%d %s' % (
        label or path, ntA, ntB, ntW, '' if (regs[18] or regs[17]) else ' (off)', sat, hs, w, h, 'H40' if h40 else 'H32'))
    for k in 'ABS':
        s = sorted(ref[k])
        print('   %s: %d tiles, max $%X' % (k, len(s), max(s) if s else 0))
    print('   tiles holding data: %d, max $%X' % (len(data), max(data) if data else 0))
    free, start = [], 0
    for t in sorted(used) + [0x800]:
        if t - start >= 8:
            free.append((start, t - 1))
        start = max(start, t + 1)
    print('   unreferenced runs (>=8): ' + ', '.join('$%X-$%X (%d)' % (a, b, b - a + 1) for a, b in free))
    free2, start = [], 0
    for t in sorted(used | data) + [0x800]:
        if t - start >= 8:
            free2.append((start, t - 1))
        start = max(start, t + 1)
    print('   unreferenced and blank: ' + ', '.join('$%X-$%X (%d)' % (a, b, b - a + 1) for a, b in free2))
    return st


if __name__ == '__main__':
    audit(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else '')
