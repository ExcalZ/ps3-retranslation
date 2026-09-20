"""Write the `en` text of work/dialogue.json and work/script.json into PSIII_Disasm/ps3.asm.

    python tools/gentext.py            # rewrite the text runs in place
    python tools/gentext.py --check    # report what would change, touch nothing

The generator works on the assembly text alone (no listing needed): the main script is the
region between the labels GameScript and loc_30C70, walked entry by entry (`dc.w target`,
`dc.b chk, set`, text lines, `dc.b $FC`); every other segment is bounded by two labels and
its runs are found by the same syntactic rule asmlist.py uses. The JSON is checked against
the source as it goes - entry count, labels, flag bytes - so a JSON that has lost or gained
an entry stops the build instead of shifting every following string.

Text is emitted one `dc.b` line per screen line, quoted where the bytes are printable
ASCII and as hex bytes elsewhere; inside a `charset`-mapped region (the credits) every
byte is emitted as hex so the assembler's mapping cannot alter it.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import ps3text   # noqa: E402
from extract_text import SEGMENTS   # noqa: E402

ASM = os.path.join(ROOT, 'PSIII_Disasm', 'ps3.asm')
DIALOGUE = os.path.join(ROOT, 'work', 'dialogue.json')
SCRIPT = os.path.join(ROOT, 'work', 'script.json')

LABEL_RE = re.compile(r'^([A-Za-z_.][A-Za-z0-9_.]*):\s*(.*)$')
CTRL_BYTES = ('$F8', '$EC', '$E4', '$E8', '$F4', '$F0', '$BE')


def split_label(line):
    m = LABEL_RE.match(line.strip())
    if m:
        return m.group(1), m.group(2).strip()
    return None, line.strip()


def is_dcb(body):
    return body.startswith('dc.b')


def ends_fc(body):
    return bool(re.search(r'\$FC\s*(;.*)?$', body))


def is_text_start(body):
    return '"' in body or any(c in body for c in CTRL_BYTES)


# ------------------------------------------------------------------ emitting

def _quote(s):
    return '"' + s.replace('"', '\\I') + '"'


def render_bytes(data, hexonly=False):
    """dc.b operand lists for a byte string - more than one when the assembler's limit
    of 20 operands per statement would be exceeded."""
    parts = []
    run = ''
    for b in data:
        if not hexonly and 0x20 <= b < 0x7F:
            run += chr(b)
        else:
            if run:
                parts.append(_quote(run)); run = ''
            parts.append('$%02X' % b)
    if run:
        parts.append(_quote(run))
    return [', '.join(parts[i:i + 16]) for i in range(0, len(parts), 16)]


def text_lines(data, hexonly=False, label=None, terminator=True):
    """Assembly lines for text bytes (without $FC): one line per screen line, the control
    bytes $F8/$EC/$FC on their own lines, as the original source lays them out."""
    chunks = []
    cur = bytearray()
    for b in data:
        if b in (0xF8, 0xEC, 0xFC):
            if cur:
                chunks.append(bytes(cur)); cur = bytearray()
            chunks.append(bytes([b]))
        else:
            cur.append(b)
    if cur:
        chunks.append(bytes(cur))
    if terminator:
        chunks.append(b'\xFC')
    lines = []
    for c in chunks:
        for ops in render_bytes(c, hexonly):
            lines.append('\tdc.b\t' + ops)
    if label:
        if len(lines) == 1:
            lines = ['%s:\tdc.b\t%s' % (label, lines[0][len('\tdc.b\t'):])]
        else:
            lines[0] = '%s:%s' % (label, lines[0])
    return lines


# ------------------------------------------------------------------ source walking

class Source:
    def __init__(self, path):
        self.path = path
        with open(path, encoding='latin-1', newline='') as f:
            self.text = f.read()
        self.nl = '\r\n' if '\r\n' in self.text[:2000] else '\n'
        self.lines = self.text.split(self.nl)
        self.edits = []   # (start, end_exclusive, new_lines)

    def label_index(self):
        d = {}
        for i, l in enumerate(self.lines):
            lab, body = split_label(l)
            if lab and lab not in d:
                d[lab] = i
        return d

    def charset_regions(self):
        """Line ranges under a `charset 'x', ...` directive (until a bare `charset`)."""
        regions = []
        start = None
        for i, l in enumerate(self.lines):
            s = l.strip()
            if re.match(r'^charset\s+\S', s):
                if start is None:
                    start = i
            elif re.match(r'^charset\s*(;.*)?$', s):
                if start is not None:
                    regions.append((start, i)); start = None
        if start is not None:
            regions.append((start, len(self.lines)))
        return regions

    def in_charset(self, i, regions):
        return any(a <= i < b for a, b in regions)

    def replace(self, start, end, new_lines):
        if self.lines[start:end] != new_lines:
            self.edits.append((start, end, new_lines))

    def apply(self):
        for start, end, new in sorted(self.edits, reverse=True):
            self.lines[start:end] = new
        with open(self.path, 'w', encoding='latin-1', newline='') as f:
            f.write(self.nl.join(self.lines))


def find_runs(src, a, b):
    """Text runs between line indices a and b: [(i, j, label)] inclusive line range."""
    runs = []
    i = a
    while i < b:
        lab, body = split_label(src.lines[i])
        if is_dcb(body) and is_text_start(body):
            j = i
            ok = False
            while j < b:
                l2, b2 = split_label(src.lines[j])
                if j > i and (l2 is not None or not is_dcb(b2)):
                    break
                if is_dcb(b2) and ends_fc(b2):
                    ok = True; break
                j += 1
            if ok:
                runs.append((i, j, lab)); i = j + 1; continue
        i += 1
    return runs


def gen_segments(src, doc, problems):
    labels = src.label_index()
    regions = src.charset_regions()
    for spec in SEGMENTS:
        name, l0, l1 = spec[:3]
        opts = spec[4] if len(spec) > 4 else {}
        seg = doc['segments'].get(name)
        if seg is None:
            problems.append('segment %s missing from script.json' % name); continue
        a, b = labels[l0], labels[l1]
        hexonly = src.in_charset(a, regions)
        if 'hdr' in opts:
            # labelled entries: label line, `dc.b hdr...` line, text lines, $FC
            labs = sorted(i for lab, i in labels.items() if a <= i < b)
            if len(labs) != len(seg['runs']):
                problems.append('%s: %d labelled entries in source, %d in JSON' % (name, len(labs), len(seg['runs']))); continue
            for i, r in zip(labs, seg['runs']):
                lab = split_label(src.lines[i])[0]
                if lab != r['id']:
                    problems.append('%s: label %s vs JSON %s' % (name, lab, r['id'])); break
                j = i + 1
                while not is_dcb(split_label(src.lines[j])[1]):
                    j += 1
                k = j + 1   # first text line
                e = k
                while not ends_fc(split_label(src.lines[e])[1]):
                    e += 1
                cs = src.in_charset(k, regions)
                data = ps3text.encode(r['en'], 'credits' if cs else 'us')
                src.replace(k, e + 1, text_lines(data, hexonly=cs))
            continue
        runs = find_runs(src, a, b)
        if len(runs) != len(seg['runs']):
            problems.append('%s: %d runs in source, %d in JSON' % (name, len(runs), len(seg['runs']))); continue
        for (i, j, lab), r in zip(runs, seg['runs']):
            if lab and lab != r['id']:
                problems.append('%s: run label %s vs JSON %s' % (name, lab, r['id'])); break
            try:
                data = ps3text.encode(r['en'], 'us')
            except ValueError as ex:
                problems.append('%s/%s: %s' % (name, r['id'], ex)); continue
            src.replace(i, j + 1, text_lines(data, hexonly=hexonly, label=lab))


def gen_dialogue(src, doc, problems):
    labels = src.label_index()
    a, b = labels['GameScript'], labels['loc_30C70']
    entries = doc['entries']
    i = a
    n = 0
    while i < b:
        lab, body = split_label(src.lines[i])
        if not body.startswith('dc.w'):
            i += 1; continue
        # header found: label may be on the previous non-blank line
        k = i - 1
        while k > a and not src.lines[k].strip():
            k -= 1
        plab = split_label(src.lines[k])[0] if k > a else None
        if n >= len(entries):
            problems.append('dialogue: more entries in source than in JSON'); return
        e = entries[n]; n += 1
        want = e['id'] if not e['id'].startswith('us_') else None
        if want and plab != want and lab != want:
            problems.append('dialogue: entry %d label %s vs JSON %s' % (n, plab, want)); return
        flags_line = split_label(src.lines[i + 1])[1]
        mf = re.match(r'^dc\.b\s+\$([0-9A-F]{2}),\s*\$([0-9A-F]{2})\s*$', flags_line)
        if not mf or ('%s %s' % (mf.group(1), mf.group(2))).upper() != e['flags']:
            problems.append('dialogue: entry %s flags %r vs JSON %s' % (e['id'], flags_line, e['flags'])); return
        k = i + 2
        if e['header_only']:
            # a US redirect target without text of its own (the renderer would run into
            # the next header): the translation may restore the JP line there, so emit
            # text when `en` is non-empty and take it out again when it is empty
            has_text = is_dcb(split_label(src.lines[k])[1])
            j = k
            if has_text:
                while not ends_fc(split_label(src.lines[j])[1]):
                    j += 1
                j += 1
            if e['en']:
                try:
                    data = ps3text.encode(e['en'], 'us')
                except ValueError as ex:
                    problems.append('dialogue/%s: %s' % (e['id'], ex)); i = j; continue
                src.replace(k, j, text_lines(data))
            elif has_text:
                src.replace(k, j, [])
            i = j
            continue
        j = k
        while not ends_fc(split_label(src.lines[j])[1]):
            j += 1
        try:
            data = ps3text.encode(e['en'], 'us')
        except ValueError as ex:
            problems.append('dialogue/%s: %s' % (e['id'], ex)); i = j + 1; continue
        src.replace(k, j + 1, text_lines(data))
        i = j + 1
    if n != len(entries):
        problems.append('dialogue: %d entries in source, %d in JSON' % (n, len(entries)))


def main():
    check = '--check' in sys.argv
    src = Source(ASM)
    problems = []
    gen_dialogue(src, json.load(open(DIALOGUE, encoding='utf-8')), problems)
    gen_segments(src, json.load(open(SCRIPT, encoding='utf-8')), problems)
    for p in problems:
        print('PROBLEM:', p)
    print('%d line ranges differ' % len(src.edits))
    if problems:
        sys.exit(1)
    if not check:
        src.apply()
        print('wrote', ASM)


if __name__ == '__main__':
    main()
