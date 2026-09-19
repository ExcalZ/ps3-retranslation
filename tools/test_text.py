"""The text codec round-trips every original string: decode(hex) -> markup -> encode == hex,
for the US script (dialogue.json, script.json) and the aligned JP text.

    python tools/test_text.py
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import ps3text

def main():
    n = 0
    d = json.load(open(os.path.join(ROOT, 'work', 'dialogue.json'), encoding='utf-8'))
    for e in d['entries']:
        raw = bytes.fromhex(e['hex'])
        if not e['header_only']:
            body = raw[4:-1]
            assert ps3text.encode(ps3text.decode(body, 'us'), 'us') == body, e['id']
            assert ps3text.encode(e['us'], 'us') == body, e['id']
            n += 1
        if e['jp'] is not None:
            jraw = bytes.fromhex(e['hex'])  # us hex; jp hex is not stored per entry - re-derive from the JP ROM
    jp_rom = os.path.join(ROOT, 'Phantasy Star III - Toki no Keishousha (Japan).md')
    if os.path.exists(jp_rom):
        rom = open(jp_rom, 'rb').read()
        m = 0
        for e in d['entries']:
            if e['jp'] and not e['header_only'] and '{END}' not in e['jp']:
                a = int(e['jp_addr'], 16) + 4
                body = rom[a:rom.index(b'\xFC', a)]
                assert ps3text.encode(e['jp'], 'jp') == body, (e['id'], e['jp'])
                m += 1
        print('  %d JP entries re-encode to their ROM bytes' % m)
    s = json.load(open(os.path.join(ROOT, 'work', 'script.json'), encoding='utf-8'))
    for name, seg in s['segments'].items():
        hdr = seg.get('hdr', 0)
        for r in seg['runs']:
            raw = bytes.fromhex(r['hex'])[hdr:-1]
            cs = 'credits' if (name == 'credits' and any(0xA0 <= b <= 0xB9 for b in raw)) else 'us'
            if ps3text.encode(r['us'], cs) != raw:
                # the two credits lines with mixed spaces are decoded with the credits charset only
                assert ps3text.encode(r['us'], 'credits') == raw, (name, r['id'])
            n += 1
    print('  %d US strings round-trip' % n)
    print('test_text: all passed')

if __name__ == '__main__':
    main()
