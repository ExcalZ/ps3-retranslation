"""Build invariants, checked before a release and by the test run.

    python tools/checkbuild.py

Reads the last assembly (PSIII_Disasm/ps3built.bin and ps3.lst) and the sources:

 1. the JSON text is what the assembly source holds (gentext.py --check is clean);
 2. the generated font binaries match a fresh generation (diafont.py);
 3. tools/proofread.html is in sync with its template and the font binaries;
 4. the ROM's header end address and checksum match the file;
 5. TechniqueData remains 24 fixed 16-byte gameplay records, and translated
    display-name slots keep the same stride;
    the compressed enemy-art block remains byte-for-byte stock;
 6. the VWF RAM block stays inside the boot-only SEGA-screen area ($FFFFE400-$FFFFFBFF),
    the dialogue pool stays inside the font block's blank tiles ($C0-$FF), and the menu
    pool stays below the sprite table at tile $540;
 7. no extension routine sits below the original end of ROM ($C0000): the retranslation
    adds code past it so nothing in the original image moves;
 8. the option flags are all 0 or 1 and vwf_dialogue implies the diafont binaries exist.
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
    # 5. Technique records are gameplay data, not variable-length text. Enemy
    # records such as Molmos store fixed IDs ($48 for enemy Foie), so growing
    # an embedded name silently redirects the AI into another record.
    techniques = (
        'Foi', 'Zan', 'Gra', 'Tsu', 'Res', 'Gires', 'Rever', 'Anti',
        'Ner', 'Rimit', 'Shiza', 'Deban', 'Fanbi', 'Forsa', 'Nasak', 'Shu',
        'Megido', 'Grantz', 'FoiCopy', 'ZanCopy', 'GraCopy', 'TsuCopy',
        'GiresCopy', 'Poison',
    )
    tech_base = sym['TechniqueData']
    bad = []
    for i, name in enumerate(techniques):
        addr = sym['Tech_' + name]
        if addr != tech_base + i * 16:
            bad.append('%s@$%X' % (name, addr))
    if sym['TechniqueData_End'] != tech_base + len(techniques) * 16:
        bad.append('end@$%X' % sym['TechniqueData_End'])
    if bad:
        fail('TechniqueData lost its 16-byte record layout: ' + ', '.join(bad))
    else:
        ok('TechniqueData: 24 fixed 16-byte records')
    tech_bytes = rom[tech_base:sym['TechniqueData_End']]
    stock_tech_sha256 = 'e45f32c383a1a5bf24dd47924dc32503e2c42258e4694623e5dc4106c0f29a89'
    if hashlib.sha256(tech_bytes).hexdigest() != stock_tech_sha256:
        fail('TechniqueData metadata differs from the stock 384-byte table')
    else:
        ok('TechniqueData bytes match stock')
    # Extension includes must not split compressed art. A previous placement
    # landed inside Neo Madder's stream and gave it a shredded battle sprite.
    art_start, art_end = sym['loc_8D57C'], sym['loc_9371C']
    stock = open(os.path.join(DISASM, 'ps3original.bin'), 'rb').read()
    if (art_end - art_start != 0x9371C - 0x8D57C or
            rom[art_start:art_end] != stock[0x8D57C:0x9371C]):
        fail('compressed enemy art from loc_8D57C to loc_9371C differs from stock')
    else:
        ok('compressed enemy art is contiguous and matches stock')
    if opts.get('vwf_dialogue') == '1':
        name_base = sym['TechniqueNameData']
        name_end = sym['TechniqueNameData_End']
        malformed = []
        for i, name in enumerate(techniques):
            slot = rom[name_base + i * 16:name_base + (i + 1) * 16]
            if b'\xFC' not in slot:
                malformed.append(name)
        if name_end != name_base + len(techniques) * 16 or malformed:
            fail('TechniqueNameData lost its 16-byte slots%s' % (
                ': missing terminator in ' + ', '.join(malformed) if malformed else ''))
        else:
            ok('TechniqueNameData: 24 translated 16-byte display slots')
    # Dialogue offsets are words. The translated script crosses $10000;
    # late scenes and the intro's closing narration use the banked resolver.
    if opts.get('extended_script') == '1':
        base = sym['GameScript']
        if sym['loc_30C70'] - base >= 0x20000:
            fail('dialogue exceeds the two-bank resolver')
        if sym['loc_304DA'] - base >= 0x10000:
            fail('unbanked loc_304DA script call has crossed the 16-bit limit')
        if sym['loc_30330'] - base >= 0x10000:
            fail('NPC loc_30330 has crossed the 16-bit table limit')
        scriptbank_high = int(re.search(r'=\$([0-9A-F]+)\s+ScriptBank_High', lst).group(1), 16)
        if not (0xFFFFE8CA <= scriptbank_high and scriptbank_high + 2 <= 0xFFFFE900):
            fail('ScriptBank_High overlaps another extension RAM block')
        else:
            ok('ScriptBank_High $%X lies between menu and save-slot RAM' % scriptbank_high)
        ending_pending = int(re.search(r'=\$([0-9A-F]+)\s+Ending_Pending', lst).group(1), 16)
        if not (ending_pending == scriptbank_high + 2 and ending_pending + 2 <= 0xFFFFE900):
            fail('Ending_Pending overlaps another extension RAM block')
        else:
            ok('Ending_Pending $%X follows ScriptBank_High' % ending_pending)
        source = open(os.path.join(DISASM, 'ps3.asm'), encoding='latin-1').read()
        intro_call = source.split('loc_1656:', 1)[1].split('Screen_Intro:', 1)[0]
        if ('jsr\t(ScriptBank_Set307B0).l' not in intro_call or
                'jmp\t(ScriptBank_Dialogue).l' not in intro_call):
            fail('intro closing narration is not routed through the banked loader')
        else:
            ok('intro closing narration uses the banked loader')
        wren_select = source.split('loc_18B22:', 1)[1].split('loc_18B5C:', 1)[0]
        wren_dialogue = source.split('loc_18B76:', 1)[1].split('loc_18B8A:', 1)[0]
        if ('jsr\t(ScriptBank_SelectWrenScript).l' not in wren_select or
                'jsr\t(ScriptBank_Dialogue).l' not in wren_dialogue):
            fail('Wren transformation dialogue is not routed through the banked loader')
        else:
            ok('Wren transformation dialogue uses the banked loader')
        ending_select = source.split('loc_152C6:', 1)[1].split('loc_152F4:', 1)[0]
        ending_exit = source.split('loc_A1A2:', 1)[1].split('loc_A1B4:', 1)[0]
        if ('jsr\t(ScriptBank_Set305FE).l' not in ending_select or
                'clr.w\t(ScriptBank_High).w' not in ending_exit):
            fail('ending event script does not set and clear its script bank')
        else:
            ok('ending event script sets and clears its script bank')
        # Any word-sized source reference is unsafe once its target exceeds
        # the relative 64 KB range, including map/NPC tables and future text.
        labels = {m.group(2): int(m.group(1), 16) for m in re.finditer(
            r'^\s*\d+/\s*([0-9A-F]+)\s*:.*?\s(loc_[0-9A-F]+):', lst, re.M)}
        script_bases = {'GameScript': base, 'GameScript2': sym['GameScript2']}
        word_refs = []
        for path in (os.path.join(DISASM, 'ps3.asm'),
                     os.path.join(DISASM, 'ext', 'scriptbank.asm')):
            for line in open(path, encoding='latin-1'):
                if not re.search(r'\b(?:dc\.w|move\.w|cmpi\.w)\b', line):
                    continue
                for name, basis in re.findall(r'(loc_[0-9A-F]+)-(GameScript2?)\b', line):
                    if labels[name] - script_bases[basis] >= 0x10000:
                        word_refs.append('%s (%s)' % (name, basis))
        if word_refs:
            fail('16-bit script references beyond $10000: ' + ', '.join(sorted(set(word_refs))))
        else:
            ok('all word-sized script references fit their base')
    # 6. VWF placement
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
        if opts.get('fix_technique_confirm') == '1':
            moff = int(re.search(r'^MenuTech_RAM_End\s*=\s*MenuTech_RAM\+(\d+)', ram, re.M).group(1))
            mbase = base + endoff
            mend = mbase + moff
            if mend > sbase:
                fail('Technique-input RAM $%X-$%X overlaps SaveSlots RAM' % (mbase, mend))
            else:
                ok('Technique-input RAM $%X-$%X' % (mbase, mend))
        pool = int(re.search(r'^VWFDIA_POOL\s*=\s*\$([0-9A-F]+)', src, re.M).group(1), 16)
        cells = int(re.search(r'^VWFDIA_CELLS\s*=\s*(\d+)', src, re.M).group(1))
        if not (0xC0 <= pool and pool + 2 * cells <= 0x100):
            fail('pool tiles $%X-$%X leave the blank font tiles $C0-$FF' % (pool, pool + 2 * cells - 1))
        else:
            ok('pool tiles $%X-$%X' % (pool, pool + 2 * cells - 1))
        ending_pool = int(re.search(r'^VWFENDING_POOL\s*=\s*\$([0-9A-F]+)', src, re.M).group(1), 16)
        if not (0x400 <= ending_pool and ending_pool + 2 * cells <= 0x540):
            fail('ending pool tiles $%X-$%X overlap scene art or the sprite table' % (
                ending_pool, ending_pool + 2 * cells - 1))
        else:
            ok('ending pool tiles $%X-$%X below the sprite table' % (
                ending_pool, ending_pool + 2 * cells - 1))
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
            # The inherited background can use $25C-$27B. The remaining ranges
            # are outside its art, the active sprite table and visible window rows.
            free = ((0x364, 0x380), (0x554, 0x560),
                    (0x580, 0x5CC), (0x5F0, 0x600))
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
            if bad or overlap or len(spans) != 15:
                fail('battle pool lines outside the free ranges %s or overlapping %s' % (bad, overlap))
            else:
                ok('battle pool: %d lines outside background art and active tilemaps' % len(spans))
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
        extension_labels = ['VWFDia_Entry', 'VWFDia_ScrollUp',
                            'VWFDia_Font', 'TechniqueNameData']
        for option, label in (('fast_walk', 'FastWalk_Init'),
                              ('fast_transitions', 'Battle_SaveMusic'),
                              ('extended_script', 'ScriptBank_Resolve'),
                              ('fix_ending_transmission', 'Ending_Queue'),
                              ('battle_target_left', 'BattleTarget_Prev')):
            if opts.get(option) == '1':
                extension_labels.append(label)
        for name in extension_labels:
            if sym[name] < 0xC0000:
                fail('%s at $%X is below the original end of ROM' % (name, sym[name]))
        ok('extension routines sit past $C0000')
    # 7. options
    for k in ('scrolling_ground', 'fast_transitions', 'fast_walk', 'extended_script',
              'fix_ending_transmission', 'fix_stale_input', 'battle_target_left',
              'fix_technique_confirm', 'four_save_slots', 'fix_tech_distributor',
              'vwf_dialogue', 'vwf_scroll_shadow', 'vwf_menu', 'vwf_shop',
              'vwf_battle', 'smooth_scroll'):
        if k not in opts:
            fail('option %s missing or not 0/1' % k)
    for k in ('vwf_menu', 'vwf_shop', 'vwf_battle', 'smooth_scroll'):
        if opts.get(k) == '1' and opts.get('vwf_dialogue') != '1':
            fail('%s requires vwf_dialogue' % k)
    fade_wait = b'\x76\x02' if opts.get('fast_transitions') == '1' else b'\x76\x04'
    for label in ('loc_80F6', 'loc_8142', 'loc_817E', 'loc_820E'):
        if rom[sym[label]:sym[label] + 2] != fade_wait:
            fail('%s does not use the configured transition dwell' % label)
    if not any(label in ' '.join(problems) for label in ('loc_80F6', 'loc_8142', 'loc_817E', 'loc_820E')):
        ok('transition fades use %d-frame palette dwell' % (2 if opts.get('fast_transitions') == '1' else 4))
    ok('options: ' + ', '.join('%s=%s' % kv for kv in sorted(opts.items())))
    print('sha256', hashlib.sha256(rom).hexdigest())
    if problems:
        print('%d problem(s)' % len(problems))
        sys.exit(1)
    print('checkbuild: all invariants hold')


if __name__ == '__main__':
    main()
