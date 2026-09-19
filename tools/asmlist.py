"""Parse the Macro Assembler AS listing (PSIII_Disasm/ps3.lst) into (line number, address,
source) records, and find every text run in the source: a maximal group of consecutive
`dc.b` lines that ends with a $FC terminator and begins with the first line carrying a
quoted string or a text control byte.

Used by the extractors and by the text generators, which replace runs in ps3.asm by their
source line numbers.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DISASM = os.path.join(ROOT, 'PSIII_Disasm')
LST = os.path.join(DISASM, 'ps3.lst')
ASM = os.path.join(DISASM, 'ps3.asm')

LST_RE = re.compile(r'^\s*(\d+)/\s*([0-9A-F]+) :(.*)$')
CTRL_BYTES = ('$F8', '$EC', '$E4', '$E8', '$F4', '$F0', '$BE')


def listing():
    """[(lineno, addr, source)] for every source line of ps3.asm that the listing shows.
    Only the first listing record of a source line is kept (continuation lines of long
    `dc.b` statements carry no source)."""
    out = []
    seen = set()
    with open(LST, encoding='latin-1') as f:
        for line in f:
            m = LST_RE.match(line)
            if not m:
                continue
            ln = int(m.group(1))
            if ln in seen:
                continue
            seen.add(ln)
            out.append((ln, int(m.group(2), 16), m.group(3)[21:].rstrip('\n')))
    return out


def split_label(src):
    """'Label:\\tdc.b ...' -> ('Label', 'dc.b ...'); plain lines -> (None, line)."""
    m = re.match(r'^([A-Za-z_.][A-Za-z0-9_.]*):\s*(.*)$', src.strip())
    if m:
        return m.group(1), m.group(2)
    return None, src.strip()


def is_dcb(body):
    return bool(re.match(r'^dc\.b\b', body))


def dcb_ends_fc(body):
    return bool(re.search(r'\$FC\s*(;.*)?$', body))


def dcb_is_text_start(body):
    if '"' in body:
        return True
    return any(c in body for c in CTRL_BYTES)


def text_runs(records):
    """Find text runs. Returns [(start_index, end_index)] into `records` (inclusive)."""
    runs = []
    i = 0
    n = len(records)
    while i < n:
        ln, addr, src = records[i]
        label, body = split_label(src)
        if is_dcb(body) and dcb_is_text_start(body):
            j = i
            ok = False
            while j < n:
                l2, a2, s2 = records[j]
                lab2, b2 = split_label(s2)
                if j > i and (lab2 is not None or not is_dcb(b2)):
                    break
                if is_dcb(b2) and dcb_ends_fc(b2):
                    ok = True
                    break
                j += 1
            if ok:
                runs.append((i, j))
                i = j + 1
                continue
        i += 1
    return runs


def run_bytes(records, rom, i, j):
    """Bytes of the run records[i..j] from the ROM: from the address of the first line to
    the address of the line after the last one (or the last line's end)."""
    start = records[i][1]
    # end = address of the next listing record after j with a different address
    k = j + 1
    while k < len(records) and records[k][1] == records[j][1]:
        k += 1
    end = records[k][1] if k < len(records) else start
    data = rom[start:end]
    # the run must end with $FC; trim any padding after it (e.g. an `even` on the same line is impossible, but be safe)
    if 0xFC in data:
        data = data[:data.rindex(0xFC) + 1]
    return start, data


if __name__ == '__main__':
    import sys
    rom = open(os.path.join(DISASM, 'ps3original.bin'), 'rb').read()
    recs = listing()
    runs = text_runs(recs)
    print(len(runs), 'runs')
    for i, j in runs[:int(sys.argv[1]) if len(sys.argv) > 1 else 40]:
        start, data = run_bytes(recs, rom, i, j)
        print('%5d-%5d %05X %s' % (recs[i][0], recs[j][0], start, data[:40]))
