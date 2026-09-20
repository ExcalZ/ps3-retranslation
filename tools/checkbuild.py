"""Build invariants, checked before a release and by the test run.

    python tools/checkbuild.py

Reads the last assembly (PSIII_Disasm/ps3built.bin and ps3.lst) and the sources:

 1. the JSON text is what the assembly source holds (gentext.py --check is clean);
 2. the generated font binaries match a fresh generation (diafont.py);
 3. tools/proofread.html is in sync with its template and the font binaries;
 4. the ROM's header end address and checksum match the file;
 5. the VWF RAM block stays inside the boot-only SEGA-screen area ($FFFFE400-$FFFFFBFF),
    the dialogue pool stays inside the font block's blank tiles ($C0-$FF), and the menu
    pool stays below the sprite table at tile $540;
 6. no extension routine sits below the original end of ROM ($C0000): the retranslation
    adds code past it so nothing in the original image moves;
 7. the option flags are all 0 or 1 and vwf_dialogue implies the diafont binaries exist.
"""
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'md'))
DISASM = os.path.join(ROOT, 'PSIII_Disasm')
problems = []


def fail(msg):
    problems.append(msg)
    print('FAIL', msg)


def ok(msg):
    print('ok  ', msg)


def main():
    import expand
    from ps3harness import Symbols
    # 1. text
    r = subprocess.run([sys.executable, os.path.join(HERE, 'gentext.py'), '--check'], capture_output=True, text=True)
    if r.returncode != 0 or '0 line ranges differ' not in r.stdout:
        fail('gentext --check: ' + (r.stdout + r.stderr).strip().splitlines()[-1])
    else:
        ok('assembly text matches work/*.json')
    # 2. fonts
    import diafont
    font, width, _ = diafont.build()
    for name, data in (('diafont.bin', font), ('diawidth.bin', width)):
        p = os.path.join(DISASM, 'vwf', name)
        if not os.path.exists(p) or open(p, 'rb').read() != data:
            fail('%s is stale: run tools/diafont.py' % name)
        else:
            ok('%s matches a fresh generation' % name)
    # 3. proofreader
    tpl = open(os.path.join(HERE, 'proofread_template.html'), encoding='utf-8').read()
    html = open(os.path.join(HERE, 'proofread.html'), encoding='utf-8').read()
    import base64
    if base64.b64encode(font).decode() not in html or tpl.split('/*EMBED*/')[1] not in html:
        fail('tools/proofread.html is stale: run tools/proofsync.py')
    else:
        ok('proofread.html in sync with the template and the fonts')
    # 4. ROM header
    rom = open(os.path.join(DISASM, 'ps3built.bin'), 'rb').read()
    end = int.from_bytes(rom[0x1A4:0x1A8], 'big') + 1
    if end != len(rom):
        fail('header end $%X vs file size $%X' % (end - 1, len(rom)))
    else:
        ok('ROM %d bytes, header end matches' % len(rom))
    if expand.checksum(rom) != int.from_bytes(rom[0x18E:0x190], 'big'):
        fail('checksum field %04X vs computed %04X (sourcebuild.py fixes it; ps3built.bin is pre-fix)' % (
            int.from_bytes(rom[0x18E:0x190], 'big'), expand.checksum(rom)))
    else:
        ok('checksum %04X' % expand.checksum(rom))
    # 5. VWF placement
    lst = open(os.path.join(DISASM, 'ps3.lst'), encoding='latin-1').read()
    opts = dict(re.findall(r'^(\w+)\s*=\s*([01])\s*$', open(os.path.join(DISASM, 'ps3.options.asm')).read(), re.M))
    sym = Symbols()
    if opts.get('vwf_dialogue') == '1':
        src = open(os.path.join(DISASM, 'ext', 'vwf.asm'), encoding='utf-8').read()
        ram = open(os.path.join(DISASM, 'ext', 'ram.asm'), encoding='utf-8').read()
        base = int(re.search(r'^VWFDia_RAM\s*=\s*\$([0-9A-F]+)', ram, re.M).group(1), 16)
        endoff = int(re.search(r'^VWFDia_RAM_End\s*=\s*VWFDia_RAM\+\$([0-9A-F]+)', ram, re.M).group(1), 16)
        sbase = int(re.search(r'^SaveSlots_RAM\s*=\s*\$([0-9A-F]+)', ram, re.M).group(1), 16)
        send = sbase + int(re.search(r'^SaveSlots_RAM_End\s*=\s*SaveSlots_RAM\+\$([0-9A-F]+)', ram, re.M).group(1), 16)
        if not (base + endoff <= sbase and send <= 0xFFFFFC00):
            fail('SaveSlots RAM $%X-$%X overlaps the VWF block or the stack' % (sbase, send))
        else:
            ok('SaveSlots RAM $%X-$%X' % (sbase, send))
        if not (0xFFFFE400 <= base and base + endoff <= 0xFFFFFC00):
            fail('VWF RAM $%X-$%X leaves the boot-only area' % (base, base + endoff))
        else:
            ok('VWF RAM $%X-$%X inside $FFFFE400-$FFFFFBFF' % (base, base + endoff))
        pool = int(re.search(r'^VWFDIA_POOL\s*=\s*\$([0-9A-F]+)', src, re.M).group(1), 16)
        cells = int(re.search(r'^VWFDIA_CELLS\s*=\s*(\d+)', src, re.M).group(1))
        if not (0xC0 <= pool and pool + 2 * cells <= 0x100):
            fail('pool tiles $%X-$%X leave the blank font tiles $C0-$FF' % (pool, pool + 2 * cells - 1))
        else:
            ok('pool tiles $%X-$%X' % (pool, pool + 2 * cells - 1))
        if opts.get('vwf_menu') == '1':
            menu_pool = int(re.search(r'^VWFMENU_POOL\s*=\s*\$([0-9A-F]+)', src, re.M).group(1), 16)
            menu_rows = int(re.search(r'^VWFMENU_ROWS\s*=\s*(\d+)', src, re.M).group(1))
            menu_cols = int(re.search(r'^VWFMENU_COLS\s*=\s*(\d+)', src, re.M).group(1))
            menu_end = menu_pool + menu_rows * menu_cols
            if menu_end > 0x540:
                fail('menu pool tiles $%X-$%X reach the sprite table at $540' % (menu_pool, menu_end - 1))
            else:
                ok('menu pool tiles $%X-$%X below the sprite table at $540' % (menu_pool, menu_end - 1))
        if opts.get('vwf_shop') == '1':
            # the shop list table (first mark row, stride, lines, $44 to match, capacity, pool):
            # the pool lines must not overlap each other and must sit below the sprite table
            tab = src[src.index('VWFShop_Table:'):]
            tab = tab[:tab.index('dc.w\t0')]
            tab = re.findall(r'^\tdc\.w\t\$([0-9A-F]+), \$?([0-9A-F]+), (\d+), (\d+), (\d+), \$([0-9A-F]+)', tab, re.M)
            spans = sorted((int(pool, 16), int(pool, 16) + int(lines) * int(cap)) for _, _, lines, _, cap, pool in tab)
            if len(spans) < 3 or any(spans[i][1] > spans[i + 1][0] for i in range(len(spans) - 1)) or spans[-1][1] > 0x540:
                fail('shop pool lines %s overlap or reach the sprite table' % spans)
            else:
                ok('shop pool tiles $%X-$%X (%d windows)' % (spans[0][0], spans[-1][1] - 1, len(spans)))
        if opts.get('vwf_battle') == '1':
            # every battle pool line must lie in a range no battle loader touches (see VWFBattle_Table)
            free = ((0x25C, 0x280), (0x364, 0x380), (0x580, 0x5CC))
            tab = src[src.index('VWFBattle_Table:'):]
            tab = tab[:tab.index('dc.w\t0')]
            lines = re.findall(r'^\tdc\.w\t\$([0-9A-F]+), \$?([0-9A-F]+), (\d+), (\d+), (\d+), \$([0-9A-F]+)', tab, re.M)
            spans = []
            for _, _, n, _, cap, pool in lines:
                for i in range(int(n)):
                    spans.append((int(pool, 16) + i * int(cap), int(pool, 16) + (i + 1) * int(cap)))
            spans.sort()
            bad = [s for s in spans if not any(a <= s[0] and s[1] <= b for a, b in free)]
            overlap = [(spans[i], spans[i + 1]) for i in range(len(spans) - 1) if spans[i][1] > spans[i + 1][0]]
            if bad or overlap or len(spans) != 14:
                fail('battle pool lines outside the free ranges %s or overlapping %s' % (bad, overlap))
            else:
                ok('battle pool: %d lines inside $25C-$27F, $364-$37F, $580-$5CB' % len(spans))
        if opts.get('smooth_scroll') == '1':
            sbase = int(re.search(r'^VWFSmooth_RAM\s*=\s*\$([0-9A-F]+)', ram, re.M).group(1), 16)
            sendoff = int(re.search(r'^VWFSmooth_RAM_End\s*=\s*VWFSmooth_RAM\+\$([0-9A-F]+)', ram, re.M).group(1), 16)
            if not (send <= sbase and sbase + sendoff <= 0xFFFFFC00):
                fail('smooth-scroll RAM $%X-$%X overlaps the save-slot block or the stack' % (sbase, sbase + sendoff))
            else:
                ok('smooth-scroll RAM $%X-$%X' % (sbase, sbase + sendoff))
            spool = int(re.search(r'^VWFSMOOTH_POOL\s*=\s*\$([0-9A-F]+)', src, re.M).group(1), 16)
            if not (0x580 <= spool and spool + 96 <= 0x600):
                fail('smooth-scroll pool $%X-$%X leaves the window plane area ($580-$5FF, off on every dialogue screen)' % (spool, spool + 95))
            else:
                ok('smooth-scroll pool $%X-$%X on the window plane' % (spool, spool + 95))
        for name in ('VWFDia_Entry', 'VWFDia_ScrollUp', 'VWFDia_Font'):
            if sym[name] < 0xC0000:
                fail('%s at $%X is below the original end of ROM' % (name, sym[name]))
        ok('extension routines sit past $C0000')
    # 7. options
    for k in ('scrolling_ground', 'four_save_slots', 'fix_tech_distributor', 'vwf_dialogue', 'vwf_scroll_shadow', 'vwf_menu', 'vwf_shop', 'vwf_battle', 'smooth_scroll'):
        if k not in opts:
            fail('option %s missing or not 0/1' % k)
    for k in ('vwf_menu', 'vwf_shop', 'vwf_battle', 'smooth_scroll'):
        if opts.get(k) == '1' and opts.get('vwf_dialogue') != '1':
            fail('%s requires vwf_dialogue' % k)
    ok('options: ' + ', '.join('%s=%s' % kv for kv in sorted(opts.items())))
    print('sha256', hashlib.sha256(rom).hexdigest())
    if problems:
        print('%d problem(s)' % len(problems))
        sys.exit(1)
    print('checkbuild: all invariants hold')


if __name__ == '__main__':
    main()
