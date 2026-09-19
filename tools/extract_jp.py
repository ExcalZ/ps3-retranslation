"""Fill the `jp` fields of work/script.json from the Japanese ROM.

    python tools/extract_jp.py

The JP tables live at different addresses but keep the US order for the name tables, so
items, techniques, enemies and party names pair by index (the party names are found by
their stat records). The menu strings pair by index after their position headers; the
battle and shop messages need explicit maps because the JP script has lines the US
merged or dropped (`jp_extra` on a segment lists the unpaired JP lines, in order, for
the translator). Names for the credits, equipment slots and the monitor messages are
left for the translator (the monitor text is attached as jp_extra).
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import ps3text  # noqa: E402

JP_ROM = os.path.join(ROOT, 'Phantasy Star III - Toki no Keishousha (Japan).md')
US_ROM = os.path.join(ROOT, 'PSIII_Disasm', 'ps3original.bin')
SCRIPT = os.path.join(ROOT, 'work', 'script.json')

JP_ITEMS, JP_TECHS, JP_ENEMIES = 0x392E6, 0x398D8, 0x3BE3C
JP_MENUS = 0x1F6B0
JP_BATTLE = 0x3D8FA
JP_SHOPS_TECHTYPES = {0: 0x3DD64, 1: 0x3DD71, 2: 0x3DD7E, 3: 0x3DD8A}   # Melee/Order/Heal/Time
JP_SHOPS = 0x3DD8A
JP_MONITOR = 0x30CD7


def strings(rom, start, n=None, stride=None, limit=None):
    """FC-terminated strings from `start`: n of them, or until `limit`."""
    p = start
    out = []
    while (n is None or len(out) < n) and (limit is None or p < limit):
        e = rom.index(b'\xFC', p)
        if limit is not None and e >= limit:
            break
        out.append((p, ps3text.decode(rom[p:e], 'jp')))
        p = p + stride if stride else e + 1
    return out


KANA = re.compile('[぀-ヿ０-ｚ]')


def clean(text):
    """Drop the pointer-table / position bytes that precede some JP strings: everything up
    to the last {XX} byte token, then leading blank tiles."""
    i = text.rfind('}')
    if i >= 0 and re.match(r'\{[0-9A-F]{2}\}', text[text.rfind('{', 0, i):i + 1] or ''):
        text = text[i + 1:]
    return text.lstrip('　')


def clean_menu(text):
    """Menu strings carry 2-4 position bytes that decode as digits/capitals; keep from the
    first kana (or a {BR} that starts an empty first line)."""
    m = KANA.search(text)
    j = text.find('{BR}')
    k = min(x for x in (m.start() if m else len(text), j if j >= 0 else len(text)))
    text = text[k:] if k < len(text) else text
    # header bytes that happen to decode as kana are followed by blank tiles: drop
    # through the last blank tile found in the first ten characters
    head = text[:10]
    if '　' in head:
        text = text[head.rfind('　') + 1:]
    return text


def main():
    jp = open(JP_ROM, 'rb').read()
    us = open(US_ROM, 'rb').read()
    doc = json.load(open(SCRIPT, encoding='utf-8'))
    segs = doc['segments']
    filled = 0

    def pair(seg, texts):
        nonlocal filled
        runs = segs[seg]['runs']
        assert len(texts) >= len(runs), (seg, len(texts), len(runs))
        for r, t in zip(runs, texts):
            r['jp'] = t
            filled += 1

    pair('items', [t for _, t in strings(jp, JP_ITEMS, len(segs['items']['runs']))])
    pair('techs', [t for _, t in strings(jp, JP_TECHS, len(segs['techs']['runs']), stride=16)])
    pair('enemies', [t for _, t in strings(jp, JP_ENEMIES, len(segs['enemies']['runs']))])

    # party names: the JP stat record has the same 7 bytes (mask, 5 stats, level) before the name
    for r in segs['charnames']['runs']:
        a = int(r['addr'], 16)
        key = us[a - 7:a]
        for m in re.finditer(re.escape(key), jp):
            p = m.start() + 7
            e = jp.index(b'\xFC', p)
            if e - p <= 8:
                r['jp'] = ps3text.decode(jp[p:e], 'jp'); filled += 1
                break

    # menus: same order, each JP string behind 2-4 position bytes
    runs = segs['menus']['runs']
    jl = [t for _, t in strings(jp, JP_MENUS, len(runs) + 2)]
    first = next(i for i, t in enumerate(jl) if 'アイテム' in t)
    for k, r in enumerate(runs):
        r['jp'] = clean_menu(jl[first + k])
        filled += 1

    # battle: JP has party/single variants the US merged
    jb = [t for _, t in strings(jp, JP_BATTLE, 30)]
    bmap = {0: 0, 1: 1, 2: 2, 3: 3, 4: (4, 5), 5: (6, 7), 6: (8, 9), 7: 10, 8: 11, 9: 12, 10: 13, 11: 14, 12: 15,
            13: 16, 14: 17, 15: 18, 16: 19, 17: 20, 18: 21, 19: 22, 20: 23, 21: 24, 22: (25, 26), 23: 27, 24: 28, 25: 29}
    for i, r in enumerate(segs['battle']['runs']):
        j = bmap[i]
        r['jp'] = ' / '.join(jb[x] for x in j) if isinstance(j, tuple) else jb[j]
        filled += 1

    # shops: four tech-type names sit before the region; then the US index i maps to JP i-3
    # (4..10), i-2 (11..21), i-1 (22..26), i (27..68)
    js = [t for _, t in strings(jp, JP_SHOPS, 69)]
    extra = []
    for i, r in enumerate(segs['shops']['runs']):
        if i < 4:
            p = JP_SHOPS_TECHTYPES[i]
            r['jp'] = ps3text.decode(jp[p:jp.index(b'\xFC', p)], 'jp')
        else:
            j = i - 3 if i <= 10 else i - 2 if i <= 21 else i - 1 if i <= 26 else i
            r['jp'] = clean(js[j])
        filled += 1
    segs['shops']['jp_extra'] = [clean(js[8]), clean(js[26])]   # inn "stay or talk?" prompt and its menu, dropped in the US

    # monitor messages: different line breaks; attach the JP lines for the translator
    segs['namestrings']['jp_extra'] = [clean(t) for _, t in strings(jp, JP_MONITOR, 43)]

    with open(SCRIPT, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print('filled %d jp fields, wrote %s' % (filled, SCRIPT))


if __name__ == '__main__':
    main()
