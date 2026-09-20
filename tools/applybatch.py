"""Merge a batch of translations into work/dialogue.json or work/script.json and
check each one against its budget.

    python tools/applybatch.py batch.json [--script]

`batch.json` maps entry ids (dialogue) or run ids (script segments, with
--script) to the new `en` text. Every id must exist; each entry is written
only after the whole batch parses. The budget report comes from linecheck.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import linecheck

CRLF = '\r\n'
LF = '\n'


def main():
    path = sys.argv[1]
    script = '--script' in sys.argv
    batch = json.load(open(path, encoding='utf-8'))
    target = os.path.join(ROOT, 'work', 'script.json' if script else 'dialogue.json')
    raw = open(target, encoding='utf-8', newline='').read()
    doc = json.loads(raw)
    if script:
        index = {r['id']: (name, r) for name, seg in doc['segments'].items() for r in seg['runs']}
    else:
        index = {e['id']: ('dialogue', e) for e in doc['entries']}
    missing = [k for k in batch if k not in index]
    if missing:
        sys.exit('unknown ids: %s' % ', '.join(missing))
    bad = 0
    for k, text in batch.items():
        seg, e = index[k]
        e['en'] = text
        cs = e.get('charset', 'us')
        if seg == 'dialogue' or seg in linecheck.VWF_LINE_SEGMENTS:
            pr = linecheck.check_vwf(text, charset=cs)
        elif seg in linecheck.VWF_SEGMENTS or k in linecheck.MENU_TECHS:
            pr = linecheck.check_vwf(text, linecheck.VWF_SEGMENTS.get(seg, linecheck.VWF_SEGMENTS['techs']), 2, 1, cs)
        elif k in linecheck.MAIN_MENU:
            pr = linecheck.check_vwf(text, 56, 4 if k == linecheck.MAIN_MENU[0] else 1, 1, cs)
        else:
            budget = linecheck.segment_budget(doc['segments'][seg])
            pr = ['%d cells > %d: %r' % (linecheck.cells(l), budget, linecheck.text_of(l))
                  for p in linecheck.pages(text, cs) for l in p if linecheck.cells(l) > budget]
        for p in pr:
            bad += 1
            print('%s: %s' % (k, p))
    # keep the file's own line endings (the JSON files are CRLF in Git) and
    # its trailing-newline convention
    out = json.dumps(doc, ensure_ascii=False, indent=1)
    if raw.endswith(LF):
        out += LF
    if CRLF in raw:
        out = out.replace(LF, CRLF)
    with open(target, 'w', encoding='utf-8', newline='') as f:
        f.write(out)
    print('%d applied, %d problem(s)' % (len(batch), bad))
    return bad


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
