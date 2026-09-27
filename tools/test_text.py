"""The text codec round-trips every original string: decode(hex) -> markup -> encode == hex,
for the US script (dialogue.json, script.json) and the aligned JP text.

    python tools/test_text.py
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import ps3text
import extract_jp
import extract_script

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
        jp_entries = extract_script.walk_jp(rom, extract_script.JP_SCRIPT,
                                            extract_script.JP_SCRIPT_END)
        assert jp_entries[-1]['addr'] == 0x30DAE
        by_addr = {'%05X' % e['addr']: e for e in jp_entries}
        for e in d['entries']:
            if e['jp_addr']:
                assert e['jp'] == by_addr[e['jp_addr']]['jp'], e['id']
        m = 0
        for e in d['entries']:
            if e['jp'] and not e['header_only'] and '{END}' not in e['jp']:
                a = int(e['jp_addr'], 16) + 4
                body = rom[a:rom.index(b'\xFC', a)]
                assert ps3text.encode(e['jp'], 'jp') == body, (e['id'], e['jp'])
                m += 1
        print('  %d JP entries re-encode to their ROM bytes' % m)
    s = json.load(open(os.path.join(ROOT, 'work', 'script.json'), encoding='utf-8'))
    monitor = s['segments']['namestrings']
    assert len(monitor['runs']) == 48
    assert 'jp_extra' not in monitor
    if os.path.exists(jp_rom):
        sources = [extract_jp.clean(t) for _, t in extract_jp.strings(
            rom, extract_jp.JP_MONITOR, 40)]
        for r, indices in zip(monitor['runs'], extract_jp.MONITOR_JP_MAP):
            assert r.get('jp') == ' / '.join(sources[i] for i in indices), r['id']
        print('  48 ending lines retain their JP source')
    for name, seg in s['segments'].items():
        hdr = seg.get('hdr', 0)
        for r in seg['runs']:
            if not r['hex']:
                # Extension-only messages have no original ROM bytes to
                # round-trip; their encoding is checked by gentext/checkbuild.
                continue
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
