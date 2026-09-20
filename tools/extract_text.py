"""Extract every text table outside the main script (names, menus, battle and shop
messages, credits, ...) from the US disassembly into work/script.json.

    python tools/extract_text.py [--rebuild]

Each segment is bounded by two labels of ps3.asm; every text run (see asmlist.py) whose
address lies between them belongs to the segment, in ROM order. A run's id is its label
when it has one, else `<segment>#<index>`. Without --rebuild an existing script.json
keeps its `en` fields and notes.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import asmlist   # noqa: E402
import ps3text   # noqa: E402

US_ROM = os.path.join(asmlist.DISASM, 'ps3original.bin')
OUT = os.path.join(ROOT, 'work', 'script.json')

# name, start label, end label (exclusive), notes[, options]
#   options: hdr=N  every entry starts at a label and carries N bytes of non-text header
SEGMENTS = [
    ('title',       'loc_1B5C',          'loc_1B8C',            'title screen: (c)SEGA 1991, TM, PRESS START BUTTON'),
    ('equip',       'loc_5F86',          'loc_5F9A',            'equipment slot labels in the Equip window'),
    ('megido',      'loc_A0E4',          'MainGame_GameScript', 'the two story techniques named in cutscenes'),
    ('marriage',    'loc_17EAC',         'Obj_EventTreasureChest', 'marriage choice menus, two lines each'),
    ('credits',     'loc_1A33C',         'loc_1A7C4',           'ending credits: each labelled entry is 2 position bytes (kept in `hdr`), text, $FC; bold capitals are written as fullwidth letters', {'hdr': 2}),
    ('charnames',   'VWFName_00',        'VWFName_End',         'party member names: VWFName_Table, referred to by the initial stats records ($E0 nn; the record field holds four letters)'),
    ('menus',       'loc_1F6CE',         'loc_1F920',           'field menu labels and prompts'),
    ('menus2',      'loc_1F9C4',         'loc_1F9D2',           'field menu: Can\'t etc.'),
    ('namestrings', 'loc_30CD8',         'loc_31136',           'the ending transmission: pairs of lines drawn straight into VRAM by loc_F7F0 (fixed-width, 24 cells)'),
    ('items',       'InventoryNameData', 'TechniqueData',       'item names'),
    ('techs',       'TechniqueData',     'loc_39A30',           'technique names (inside the technique records)'),
    ('enemies',     'EnemyNameData',     'loc_3C36A',           'enemy names'),
    ('battle',      'loc_3D8E6',         'loc_3DAE0',           'battle messages'),
    ('shops',       'loc_3DD8A',         'loc_3E690',           'shop, inn, church and game-select text'),
]


def label_addrs(records):
    d = {}
    for ln, addr, src in records:
        lab, body = asmlist.split_label(src)
        if lab and lab not in d:
            d[lab] = addr
    return d


def charset_regions(records):
    """Address ranges assembled under a `charset 'x', ...` directive."""
    out = []
    start = None
    for ln, addr, src in records:
        s = src.strip()
        if re.match(r'^charset\s+\S', s):
            if start is None:
                start = addr
        elif re.match(r'^charset\s*(;.*)?$', s) and start is not None:
            out.append((start, addr)); start = None
    return out


def extract(rom, records=None):
    records = records or asmlist.listing()
    labels = label_addrs(records)
    csr = charset_regions(records)
    runs = asmlist.text_runs(records)
    out = {}
    for spec in SEGMENTS:
        name, l0, l1, note = spec[:4]
        opts = spec[4] if len(spec) > 4 else {}
        a0, a1 = labels[l0], labels[l1]
        seg = []
        if 'hdr' in opts:
            hdr = opts['hdr']
            labs = sorted((addr, lab) for lab, addr in labels.items() if a0 <= addr < a1)
            for addr, lab in labs:
                end = rom.index(b'\xFC', addr + hdr) + 1
                data = rom[addr:end]
                cs = 'credits' if any(x <= addr < y for x, y in csr) else 'us'
                seg.append({'id': lab, 'addr': '%05X' % addr, 'hex': data.hex(),
                            'hdr': data[:hdr].hex(), 'us': ps3text.decode(data[hdr:-1], cs)})
            out[name] = {'note': note, 'start': l0, 'end': l1, 'hdr': hdr, 'runs': seg}
            continue
        for i, j in runs:
            addr = records[i][1]
            if a0 <= addr < a1:
                start, data = asmlist.run_bytes(records, rom, i, j)
                lab, body = asmlist.split_label(records[i][2])
                seg.append({
                    'id': lab or '%s#%03d' % (name, len(seg)),
                    'line': records[i][0], 'line_end': records[j][0],
                    'addr': '%05X' % start, 'hex': data.hex(),
                    'us': ps3text.decode(data[:-1], 'us'),
                })
        out[name] = {'note': note, 'start': l0, 'end': l1, 'runs': seg}
    return out


def main():
    rebuild = '--rebuild' in sys.argv
    rom = open(US_ROM, 'rb').read()
    segs = extract(rom)
    old = {}
    if os.path.exists(OUT) and not rebuild:
        for sname, s in json.load(open(OUT, encoding='utf-8'))['segments'].items():
            for r in s['runs']:
                old[(sname, r['id'])] = r
    total = 0
    for sname, s in segs.items():
        for r in s['runs']:
            o = old.get((sname, r['id']))
            r['en'] = o['en'] if o else r['us']
            if o and o.get('note'):
                r['note'] = o['note']
            if o and o.get('jp'):
                r['jp'] = o['jp']
            total += 1
    doc = {'format': 'ps3 script v1',
           'notes': 'Edit only `en`. Markup as in dialogue.json. `line` is the ps3.asm line of the run at extraction time (informational; generators relocate runs by label bounds).',
           'segments': segs}
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print('segments:', ', '.join('%s=%d' % (k, len(v['runs'])) for k, v in segs.items()))
    print('%d runs, wrote %s' % (total, OUT))


if __name__ == '__main__':
    main()
