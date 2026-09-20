"""Check every `en` string in work/dialogue.json and work/script.json against its
budget - the same rules `proofread.html` applies, from the shell.

    python tools/linecheck.py            # report every violation, exit 1 if any
    python tools/linecheck.py --changed  # only entries whose `en` differs from `us`
    python tools/linecheck.py --widths   # also print the widest line of each changed entry

Proportional text (dialogue, battle, shops, credits): 192 px per line in the
dialogue face; the first page holds two lines ({BR}), each {PAGE} one more.
Items and techniques 72 px (the technique names repeated in `menus` too),
enemies 75 px, party names 40 px, the two field main-menu labels 56 px (four
lines for the first, one for the second); the other menu-map windows (`menus`,
`menus2`, `equip`) draw proportionally inside their stock cell budget, a {BR}
moving to the next pool line. Fixed-width: the game-select lists and speed
prompt in `shops`, `marriage`, `megido`, `title`, and the ending transmission
(`namestrings`, 24 cells); the widest US line of the segment is the cell
budget. Inserted names count 34 px, numbers 15 px, as the proofreader assumes.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import diafont, ps3text

WIDTH = diafont.build()[1]
INSERT_PX = {0xE8: 34, 0xE4: 15}
INSERT_CELLS = {0xE8: 6, 0xE4: 3}
VWF_SEGMENTS = {'items': 72, 'techs': 72, 'enemies': 75, 'charnames': 40}
VWF_LINE_SEGMENTS = ('battle', 'shops', 'credits')
MENU_TECHS = tuple('menus#%03d' % i for i in range(20, 36))   # technique names in the Techs screen
MAIN_MENU = ('menus#000', 'menus#001')
FIXED_MENUS = ('shops#054', 'shops#056', 'shops#064', 'shops#065', 'shops#066', 'shops#067', 'shops#068')   # game-select lists and the speed prompt: stock 8x8
POOLED_SEGMENTS = ('menus', 'menus2', 'equip')   # every menu-map window draws proportionally inside its stock cell budget
LINE = 192


def pages(text, charset='us'):
    """[[line, line], [line], ...]; each line a list of byte or (ctrl, arg)."""
    data = ps3text.encode(text, charset)
    out = [[]]
    line = []
    i = 0
    while i < len(data):
        b = data[i]
        if b == 0xF8:
            out[-1].append(line); line = []
        elif b in (0xEC, 0xFC):
            out[-1].append(line); line = []; out.append([])
        elif b in INSERT_PX:
            i += 1; line.append((b, data[i]))
        else:
            line.append(b)
        i += 1
    out[-1].append(line)
    return [p for k, p in enumerate(out) if k == 0 or any(p)]


def px(line):
    return sum(INSERT_PX[b[0]] if isinstance(b, tuple) else WIDTH[b] for b in line)


def cells(line):
    return sum(INSERT_CELLS[b[0]] if isinstance(b, tuple) else 1 for b in line)


def text_of(line):
    return ''.join('{%s}' % ps3text.CTRL[b[0]] if isinstance(b, tuple) else ps3text.US_DECODE.get(b, '?')
                   for b in line)


def check_vwf(text, limit=LINE, first_lines=2, rest_lines=1, charset='us'):
    """Return a list of problems (strings); empty when the text fits."""
    problems = []
    try:
        pg = pages(text, charset)
    except (ValueError, KeyError) as e:
        return ['cannot encode: %s' % e]
    for k, p in enumerate(pg):
        allowed = first_lines if k == 0 else rest_lines
        if len(p) > allowed:
            problems.append('page %d has %d lines (max %d)' % (k, len(p), allowed))
        for l in p:
            w = px(l)
            if w > limit:
                problems.append('%d px > %d: %r' % (w, limit, text_of(l)))
    return problems


def widest(text, charset='us'):
    return max((px(l) for p in pages(text, charset) for l in p), default=0)


def segment_budget(seg):
    return max((cells(l) for r in seg['runs'] for p in pages(r['us'], r.get('charset', 'us')) for l in p), default=1)


def run(changed_only=False, show_widths=False):
    bad = 0
    dia = json.load(open(os.path.join(ROOT, 'work', 'dialogue.json'), encoding='utf-8'))
    for e in dia['entries']:
        if changed_only and e['en'] == e['us']:
            continue
        pr = check_vwf(e['en'])
        if show_widths and not pr:
            print('%-12s %3d px' % (e['id'], widest(e['en'])))
        for p in pr:
            bad += 1
            print('dialogue %s: %s' % (e['id'], p))
    scr = json.load(open(os.path.join(ROOT, 'work', 'script.json'), encoding='utf-8'))
    for name, seg in scr['segments'].items():
        fixed = None
        for r in seg['runs']:
            if changed_only and r['en'] == r['us']:
                continue
            cs = r.get('charset', 'us')
            if name == 'credits' and any('Ａ' <= ch <= 'Ｚ' for ch in r['us']):
                continue   # the ending staff roll: bold capitals under the assembler's charset map, not text
            if r['id'] in MAIN_MENU:
                pr = check_vwf(r['en'], 56, 4 if r['id'] == MAIN_MENU[0] else 1, 1, cs)
            elif name in VWF_SEGMENTS or r['id'] in MENU_TECHS:
                pr = check_vwf(r['en'], VWF_SEGMENTS.get(name, VWF_SEGMENTS['techs']), 2, 1, cs)
            elif name in VWF_LINE_SEGMENTS and r['id'] not in FIXED_MENUS:
                pr = check_vwf(r['en'], LINE, 99 if name == 'shops' else 2, 1, cs)
            elif name in POOLED_SEGMENTS:
                if fixed is None:
                    fixed = segment_budget(seg)
                pr = check_vwf(r['en'], fixed * 8, 99, 99, cs)
            else:
                if fixed is None:
                    fixed = segment_budget(seg)
                try:
                    pr = ['%d cells > %d: %r' % (cells(l), fixed, text_of(l))
                          for p in pages(r['en'], cs) for l in p if cells(l) > fixed]
                except (ValueError, KeyError) as ex:
                    pr = ['cannot encode: %s' % ex]
            if show_widths and not pr:
                print('%-14s %3d px' % (r['id'], widest(r['en'], cs)))
            for p in pr:
                bad += 1
                print('%s %s: %s' % (name, r['id'], p))
    print('%d problem(s)' % bad)
    return bad


if __name__ == '__main__':
    sys.exit(1 if run('--changed' in sys.argv, '--widths' in sys.argv) else 0)
