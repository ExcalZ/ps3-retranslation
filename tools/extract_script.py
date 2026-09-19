"""Extract the main game script (GameScript / GameScript2) from the US disassembly and the
JP ROM, align the two, and write work/dialogue.json.

    python tools/extract_script.py [--rebuild]

The US side is read from the assembler listing (PSIII_Disasm/ps3.lst) so every entry keeps
its label and the label of its flag-branch target; the bytes themselves come from the US
ROM at the listed addresses. The JP side is walked structurally from the JP ROM
(entries are `target.w, checkflag.b, setflag.b, text..., $FC`, padded to even) and the
two sequences are aligned with NPC-table anchors, flag-branch targets, and order.

Without --rebuild an existing work/dialogue.json keeps its `en` fields and notes; the
jp/us/hex fields are always regenerated from the ROMs.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import ps3text  # noqa: E402

DISASM = os.path.join(ROOT, 'PSIII_Disasm')
US_ROM = os.path.join(DISASM, 'ps3original.bin')
JP_ROM = os.path.join(ROOT, 'Phantasy Star III - Toki no Keishousha (Japan).md')
LST = os.path.join(DISASM, 'ps3.lst')
OUT = os.path.join(ROOT, 'work', 'dialogue.json')

US_SCRIPT = 0x25F0A
JP_SCRIPT = 0x25F0C
US_NPC_TABLE = 0x33996
JP_NPC_TABLE = 0x33A30
NPC_MAPS = (0x33D14 - 0x33996) // 2

LST_RE = re.compile(r'^\s*(\d+)/\s*([0-9A-F]+) :(.*)$')


def read_listing_region(start_label, end_label):
    """Yield (address, source) for listing lines between two labels."""
    lines = []
    active = False
    with open(LST, encoding='latin-1') as f:
        for line in f:
            m = LST_RE.match(line)
            if not m:
                continue
            addr = int(m.group(2), 16)
            src = m.group(3)[21:]   # skip the 20-column object-code field
            if src.strip().startswith(start_label + ':'):
                active = True
            if active and src.strip().startswith(end_label + ':'):
                break
            if active:
                lines.append((addr, src))
    return lines


def parse_us(rom):
    """Entries of the US script from the listing, in ROM order."""
    lines = read_listing_region('GameScript', 'loc_30C70')
    entries = []
    cur = None
    label = None
    base_label = 'GameScript'
    for addr, src in lines:
        s = src.strip()
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*):', s)
        if m:
            label = m.group(1)
            if label == 'GameScript2':
                base_label = 'GameScript2'
            continue
        body = s
        mw = re.match(r'^dc\.w\s+(.+?)\s*$', body)
        if mw:
            tgt = mw.group(1).strip()
            if cur is not None:
                entries.append(cur)
            mt = re.match(r'^(loc_[0-9A-F]+)-(GameScript2?)$', tgt)
            cur = {'label': label, 'addr': addr, 'base': base_label,
                   'target': mt.group(1) if mt else None,
                   'target_base': mt.group(2) if mt else None,
                   'end': None, 'header_only': True}
            label = None
            continue
        mb = re.match(r'^dc\.b\s+(.+?)\s*$', body)
        if mb and cur is not None:
            if cur.get('flags') is None:
                cur['flags'] = (rom[addr], rom[addr + 1])
                cur['text_addr'] = addr + 2
            else:
                cur['header_only'] = False
                if mb.group(1).strip() == '$FC':
                    cur['end'] = addr + 1
    if cur is not None:
        entries.append(cur)
    for e in entries:
        if e['header_only']:
            e['end'] = e['text_addr']
        raw = rom[e['addr']:e['end']]
        e['hex'] = raw.hex()
        e['us'] = ps3text.decode(raw[4:-1] if not e['header_only'] else b'', 'us')
        e['offset'] = e['addr'] - US_SCRIPT
    return entries


# flag bytes that the US script's headers use; a JP header's set-flag byte must be one of
# these (kana text bytes are $30-$9D, so this discriminates a header from an orphan text)
SET_FLAG_VALUES = {0x00, 0x08, 0x0D, 0x25, 0xE6, 0xE7}


def looks_like_header(b):
    """Does a 4-byte group look like `target.w, checkflag, setflag` rather than kana text?"""
    if len(b) < 4:
        return False
    if b[0] > 0xB0 or (b[1] & 1):
        return False
    return (b[2] == 0xFF or b[2] < 0xF0) and b[3] in SET_FLAG_VALUES


def walk_jp(rom, start, limit):
    """Walk the JP script structurally. Entries normally start with a header; the JP script
    also has header-only entries (a branch header with no text, as the US script has) and
    orphan text pieces after an $FC with no header at all (unreachable in the JP game; the
    US script folded them into the preceding entry). Orphans are appended to the previous
    entry's text after an {END} marker."""
    p = start
    entries = []
    while p < limit:
        hdr = rom[p:p + 4]
        if looks_like_header(hdr):
            tgt = int.from_bytes(hdr[:2], 'big')
            chk, st = hdr[2], hdr[3]
            q = p + 4
            if looks_like_header(rom[q:q + 4]):
                entries.append({'addr': p, 'offset': p - start, 'target_off': tgt, 'flags': (chk, st),
                                'header_only': True, 'hex': rom[p:q].hex(), 'jp': ''})
                p = q
                continue
        else:
            # orphan continuation: no header
            q = p
            tgt = chk = st = None
        while q < limit and rom[q] != 0xFC:
            if rom[q] in (0xE4, 0xE8, 0xF4, 0xF0):
                q += 2
            else:
                q += 1
        end = q + 1
        text = ps3text.decode(rom[(p + 4) if tgt is not None else p:end - 1], 'jp')
        if tgt is None and entries:
            prev = entries[-1]
            prev['jp'] += '{END}' + text
            prev['hex'] += rom[p:end].hex()
            prev['orphans'] = prev.get('orphans', 0) + 1
        else:
            entries.append({'addr': p, 'offset': p - start, 'target_off': tgt, 'flags': (chk, st),
                            'header_only': False, 'hex': rom[p:end].hex(), 'jp': text})
        p = end
        if p & 1:
            p += 1
    return entries


def npc_offsets(rom, base):
    """(map_id, index, script_offset, obj_type) for every NPC in the level tables."""
    out = []
    for m in range(NPC_MAPS):
        p = base + 2 * m
        q = p + int.from_bytes(rom[p:p + 2], 'big')
        cnt = int.from_bytes(rom[q:q + 2], 'big')
        if cnt >= 0x8000:
            continue
        q += 2
        for i in range(cnt + 1):
            out.append((m * 2, i, int.from_bytes(rom[q + 6:q + 8], 'big'), rom[q]))
            q += 10
    return out


def align(us_entries, jp_entries, us_rom, jp_rom):
    """Return jp index for each us entry (or None), using anchors then order."""
    us_by_off = {e['offset']: i for i, e in enumerate(us_entries)}
    jp_by_off = {e['offset']: i for i, e in enumerate(jp_entries)}
    us_label_off = {e['label']: e['offset'] for e in us_entries if e['label']}
    # GameScript2 offsets: targets are relative to GameScript2 for entries in that half
    gs2 = next((e['offset'] for e in us_entries if e['base'] == 'GameScript2'), None)

    anchors = {}
    # 1. NPC tables, map by map (the map/NPC structure is identical between regions)
    un = npc_offsets(us_rom, US_NPC_TABLE)
    jn = npc_offsets(jp_rom, JP_NPC_TABLE)
    from collections import defaultdict
    umap = defaultdict(list); jmap = defaultdict(list)
    for r in un: umap[r[0]].append(r)
    for r in jn: jmap[r[0]].append(r)
    for m in umap:
        if len(umap[m]) != len(jmap.get(m, [])):
            continue
        for a, b in zip(umap[m], jmap[m]):
            if a[3] == b[3] and a[2] in us_by_off and b[2] in jp_by_off:
                anchors.setdefault(us_by_off[a[2]], set()).add(jp_by_off[b[2]])
    anchors = {k: v.pop() for k, v in anchors.items() if len(v) == 1}

    # 2. propagate through flag-branch targets, until stable
    def us_target_index(e):
        if e['target'] is None:
            return None
        off = us_label_off.get(e['target'])
        return us_by_off.get(off) if off is not None else None

    def jp_target_index(e, us_e):
        t = e['target_off']
        if us_e['target_base'] == 'GameScript2' and gs2 is not None:
            t += gs2 if False else 0  # JP has a single base; handled below
        return jp_by_off.get(t)

    changed = True
    while changed:
        changed = False
        for ui, ji in list(anchors.items()):
            ue, je = us_entries[ui], jp_entries[ji]
            ut = us_target_index(ue)
            if ut is None:
                continue
            jt = jp_by_off.get(je['target_off'])
            if jt is None:
                continue
            if ut not in anchors:
                anchors[ut] = jt
                changed = True

    # 3. order-based fill between anchors (Needleman-Wunsch on flags within each gap)
    result = [None] * len(us_entries)
    for ui, ji in anchors.items():
        result[ui] = ji
    keys = sorted(anchors)
    bounds = [(-1, -1)] + [(k, anchors[k]) for k in keys] + [(len(us_entries), len(jp_entries))]
    for (u0, j0), (u1, j1) in zip(bounds, bounds[1:]):
        us_gap = list(range(u0 + 1, u1))
        jp_gap = list(range(j0 + 1, j1))
        if not us_gap:
            continue
        if not jp_gap:
            continue
        # DP alignment scoring matching flags
        n, m = len(us_gap), len(jp_gap)
        score = [[0] * (m + 1) for _ in range(n + 1)]
        back = [[0] * (m + 1) for _ in range(n + 1)]
        for i in range(1, n + 1):
            score[i][0] = -i; back[i][0] = 1
        for j in range(1, m + 1):
            score[0][j] = -j; back[0][j] = 2
        for i in range(1, n + 1):
            ue = us_entries[us_gap[i - 1]]
            for j in range(1, m + 1):
                je = jp_entries[jp_gap[j - 1]]
                sim = 3 if ue['flags'] == je['flags'] else (1 if ue['flags'][0] == je['flags'][0] else -2)
                if ue['header_only'] != je['header_only']:
                    sim -= 3
                cands = [(score[i - 1][j - 1] + sim, 0), (score[i - 1][j] - 1, 1), (score[i][j - 1] - 1, 2)]
                score[i][j], back[i][j] = max(cands)
        i, j = n, m
        while i > 0 or j > 0:
            b = back[i][j]
            if b == 0:
                result[us_gap[i - 1]] = jp_gap[j - 1]; i -= 1; j -= 1
            elif b == 1:
                i -= 1
            else:
                j -= 1
    return result, anchors


def main():
    rebuild = '--rebuild' in sys.argv
    us_rom = open(US_ROM, 'rb').read()
    jp_rom = open(JP_ROM, 'rb').read()
    us_entries = parse_us(us_rom)
    jp_entries = walk_jp(jp_rom, JP_SCRIPT, 0x31000)
    # trim the JP walk where it leaves the script (first entry whose flags are implausible
    # after the last plausible one)
    mapping, anchors = align(us_entries, jp_entries, us_rom, jp_rom)

    old = {}
    if os.path.exists(OUT) and not rebuild:
        for e in json.load(open(OUT, encoding='utf-8'))['entries']:
            old[e['id']] = e

    used = set()
    entries = []
    for i, e in enumerate(us_entries):
        ji = mapping[i]
        je = jp_entries[ji] if ji is not None else None
        if ji is not None:
            used.add(ji)
        eid = e['label'] or 'us_%05X' % e['addr']
        rec = {
            'id': eid,
            'addr': '%05X' % e['addr'],
            'base': e['base'],
            'target': e['target'],
            'flags': '%02X %02X' % e['flags'],
            'header_only': e['header_only'],
            'anchor': i in anchors,
            'jp_addr': '%05X' % je['addr'] if je else None,
            'jp': je['jp'] if je else None,
            'us': e['us'],
            'en': old.get(eid, {}).get('en', e['us']),
            'hex': e['hex'],
        }
        if eid in old and old[eid].get('note'):
            rec['note'] = old[eid]['note']
        entries.append(rec)
    unmatched_jp = [{'jp_addr': '%05X' % je['addr'], 'flags': '%02X %02X' % je['flags'],
                     'header_only': je['header_only'], 'jp': je['jp'], 'hex': je['hex']}
                    for i, je in enumerate(jp_entries) if i not in used and je['addr'] < 0x30A00]
    doc = {
        'format': 'ps3 dialogue v1',
        'notes': 'Edit only `en`. {BR} line break, {PAGE} button wait + clear, {NAME:nn}/{NUM:nn}/{VAR:nn} engine inserts, {III} the Alisa III glyph pair.',
        'entries': entries,
        'jp_unmatched': unmatched_jp,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    n_us = len(entries); n_m = sum(1 for e in entries if e['jp'] is not None)
    print('US entries %d (header-only %d), JP entries walked %d, matched %d, anchors %d, JP unmatched %d'
          % (n_us, sum(1 for e in entries if e['header_only']), len(jp_entries), n_m, len(anchors), len(unmatched_jp)))
    print('wrote', OUT)


if __name__ == '__main__':
    main()
