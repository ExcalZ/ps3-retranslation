"""Banked space, intro, and Wren scripts remain reachable past 64 KB."""
import os
import re
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ps3harness import Machine, Symbols  # noqa: E402
from extract_script import parse_us  # noqa: E402
import ps3text  # noqa: E402


def main():
    sym = Symbols()
    m = Machine()
    base = sym['GameScript']
    high = int(re.search(r'=\$([0-9A-F]+)\s+ScriptBank_High', sym.text).group(1), 16)
    table = sym['ScriptBank_SpaceTable']
    targets = (
        'loc_303C0', 'loc_30A0A', None, 'loc_3044E', 'loc_3052C', None,
        'loc_305CE', 'loc_30BE6', None, 'loc_30A9E', 'loc_307D2',
        'loc_3085C', 'loc_3094A',
    )
    for index, label in enumerate(targets):
        offset = int.from_bytes(m.peek(table + index * 4, 4), 'big')
        if label is None:
            assert offset == 0xFFFFFFFF, index
            continue
        want = sym[label]
        assert offset == want - base, (label, hex(offset), hex(want - base))
        m.poke(high, (offset >> 16).to_bytes(2, 'big'))
        m.call(sym['ScriptBank_Resolve'], d0=offset & 0xFFFF)
        assert m.a[0] == want, (label, hex(m.a[0]), hex(want))
        assert m.peek(want + 2, 2) == b'\xFF\x00', label

    # Pre-extension emulator states retain pixels in this RAM. They must not
    # accidentally select the high bank when an ordinary script runs.
    m.poke(high, b'\x12\x22')
    m.call(sym['ScriptBank_Resolve'], d0=sym['loc_25F24'] - base)
    assert m.a[0] == sym['loc_25F24']

    m.call(sym['ScriptBank_Set30A3E'])
    offset = m.d[0]
    assert offset == sym['loc_30A3E'] - base and offset >= 0x10000
    assert m.peek(high, 2) == b'\x00\x01'
    m.call(sym['ScriptBank_Set305FE'])
    offset = sym['loc_305FE'] - base
    assert m.d[0] == offset
    assert m.peek(0xFFFFD064, 2) == (offset & 0xFFFF).to_bytes(2, 'big')
    assert m.peek(high, 2) == (offset >> 16).to_bytes(2, 'big')
    m.call(sym['ScriptBank_Resolve'], d0=offset & 0xFFFF)
    assert m.a[0] == sym['loc_305FE']
    m.call(sym['loc_A1A2'])
    assert m.peek(high, 2) == b'\x00\x00'
    assert m.peek(0xFFFFD064, 2) == b'\x00\x00'
    m.call(sym['ScriptBank_Set307B0'])
    offset = sym['loc_307B0'] - base
    assert m.d[0] == offset
    assert m.peek(0xFFFFD064, 2) == (offset & 0xFFFF).to_bytes(2, 'big')
    assert m.peek(high, 2) == (offset >> 16).to_bytes(2, 'big')
    m.call(sym['ScriptBank_Resolve'], d0=offset & 0xFFFF)
    assert m.a[0] == sym['loc_307B0']
    assert m.peek(m.a[0] + 2, 2) == b'\xFF\x00'
    # The transformation scene keeps word offsets relative to GameScript2.
    # Three of its six choices now cross the GameScript 64 KB boundary.
    wren = ('loc_30708', 'loc_30732', 'loc_3075A',
            'loc_30780', 'loc_30780', 'loc_30780')
    for index, label in enumerate(wren):
        m.call(sym['ScriptBank_SelectWrenScript'], d0=index * 2)
        offset = sym[label] - base
        assert m.d[0] == index * 2
        assert m.peek(0xFFFFD064, 2) == (offset & 0xFFFF).to_bytes(2, 'big')
        assert m.peek(high, 2) == (offset >> 16).to_bytes(2, 'big')
        m.call(sym['ScriptBank_Resolve'], d0=offset & 0xFFFF)
        assert m.a[0] == sym[label], (label, hex(m.a[0]))
        assert m.peek(m.a[0] + 2, 2) == b'\xFF\x00', label

    # Audit the entire emitted dialogue, including every conditional redirect.
    # A matching source listing alone cannot catch a truncated ROM pointer.
    rom = open(os.path.join(HERE, '..', 'PSIII_Disasm', 'ps3built.bin'), 'rb').read()
    addresses = {match.group(2): int(match.group(1), 16) for match in re.finditer(
        r'^\s*\d+/\s*([0-9A-F]+)\s*:.*?\s([A-Za-z_][A-Za-z0-9_]*):', sym.text, re.M)}
    entries = parse_us(rom)
    doc = json.load(open(os.path.join(HERE, '..', 'work', 'dialogue.json'), encoding='utf-8'))
    starts = {e['addr'] for e in entries}
    assert len(entries) == len(doc['entries']) == 546
    assert sym['loc_30C70'] - base < 0x20000
    for e, want in zip(entries, doc['entries']):
        label, addr = e['label'], e['addr']
        if label:
            assert label == want['id'] and addresses[label] == addr, label
        offset = addr - base
        m.poke(high, (offset >> 16).to_bytes(2, 'big'))
        m.call(sym['ScriptBank_Resolve'], d0=offset & 0xFFFF)
        assert m.a[0] == addr, label
        raw = rom[addr:e['end']]
        assert raw[2:4].hex().upper() == want['flags'].replace(' ', ''), want['id']
        assert raw[4:] == (ps3text.encode(want['en'], 'us') + b'\xFC' if want['en'] else b''), want['id']
        if e['target']:
            target = addresses[e['target']]
            target_base = addresses[e['target_base']]
            assert target in starts, (label, e['target'])
            assert raw[:2] == (target - target_base).to_bytes(2, 'big'), label
            assert (target - base) >> 16 == offset >> 16, label
        else:
            assert raw[:2] == b'\x00\x00', label

    # Every active source word pointer must contain its intended full relative
    # address in the assembled ROM. This covers NPC, event, and scene tables.
    pointer_lines = re.finditer(
        r'^\s*\d+/\s*([0-9A-F]+)\s*:\s*[0-9A-F ]+?\s+dc\.w\s+'
        r'(loc_[0-9A-F]+)-(GameScript2?)\b', sym.text, re.M)
    count = 0
    for match in pointer_lines:
        addr = int(match.group(1), 16)
        target, basis = match.group(2), match.group(3)
        delta = addresses[target] - addresses[basis]
        assert 0 <= delta < 0x10000, (target, basis, hex(delta))
        assert rom[addr:addr + 2] == delta.to_bytes(2, 'big'), (target, hex(addr))
        count += 1
    assert count >= 500, count
    print('test_scriptbank: %d dialogue entries and %d script word pointers passed' % (len(entries), count))


if __name__ == '__main__':
    main()
