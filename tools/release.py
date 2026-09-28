"""Package the retranslation: standard and no-parallax BPS patches, web patcher, readme.

    python tools/release.py 1.0 [--rom ps3en.bin] [--allow-stale]

Writes release/PS3_Retranslation_v1.0/{PS3_Retranslation_v1.0.bps,
PS3_Retranslation_v1.0_No_Battle_Parallax.bps, Patcher.html, readme.txt}
and release/PS3_Retranslation_v1.0.zip. The source is the stock US ROM
(PSIII_Disasm/ps3original.bin); the patch is made with Flips when flips/flips.exe exists
and with tools/md/bps.py otherwise, re-applied, and the result must equal the ROM byte for
byte. Refuses a ROM that differs from the last assembly. Every number in the readme is a
@TOKEN@ filled from the files themselves, so the text cannot disagree with the patch.
"""
import datetime
import hashlib
import os
import re
import subprocess
import sys
import zipfile
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, 'md'))
import bps       # noqa: E402
import expand    # noqa: E402
import webpatch  # noqa: E402
sys.path.insert(0, HERE)
from ps3harness import Symbols  # noqa: E402

SRC = os.path.join(ROOT, 'PSIII_Disasm', 'ps3original.bin')
BUILT = os.path.join(ROOT, 'PSIII_Disasm', 'ps3built.bin')
FLIPS = os.path.join(ROOT, 'flips', 'flips.exe')
STOCK_SCROLL_START = 0x780C0
STOCK_SCROLL_END = 0x781BC


def hashes(data):
    return {'SIZE': '{:,}'.format(len(data)), 'CRC32': '%08X' % (zlib.crc32(data) & 0xFFFFFFFF),
            'MD5': hashlib.md5(data).hexdigest().upper(), 'SHA1': hashlib.sha1(data).hexdigest().upper()}


def without_battle_parallax(src, rom):
    """Use the stock US battle scroll tables in the otherwise unchanged build."""
    start = Symbols()['loc_780C0']
    end = Symbols()['loc_781BC']
    stock = src[STOCK_SCROLL_START:STOCK_SCROLL_END]
    if end - start != len(stock) or len(rom) < end:
        raise SystemExit('battle scroll table size or placement changed; inspect before packaging')
    if rom[start:end] == stock:
        raise SystemExit('standard ROM already has stock battle scrolling')
    alternate = bytearray(rom)
    alternate[start:end] = stock
    alternate = expand.fix_checksum(alternate)
    assert alternate[:0x18E] == rom[:0x18E]
    assert alternate[0x190:start] == rom[0x190:start]
    assert alternate[end:] == rom[end:]
    return alternate


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        raise SystemExit(__doc__)
    ver = args[0]
    rom_path = os.path.join(ROOT, 'ps3en.bin')
    if '--rom' in sys.argv:
        rom_path = sys.argv[sys.argv.index('--rom') + 1]
    src = open(SRC, 'rb').read()
    rom = open(rom_path, 'rb').read()
    built = expand.fix_checksum(open(BUILT, 'rb').read())
    if rom != built and '--allow-stale' not in sys.argv:
        raise SystemExit('%s differs from the last assembly (PSIII_Disasm/ps3built.bin); rebuild or pass --allow-stale' % rom_path)
    alternate = without_battle_parallax(src, rom)
    name = 'PS3_Retranslation_v%s' % ver
    out = os.path.join(ROOT, 'release', name)
    os.makedirs(out, exist_ok=True)
    patch_path = os.path.join(out, name + '.bps')
    if os.path.exists(FLIPS):
        subprocess.check_call([FLIPS, '--create', '--bps', SRC, rom_path, patch_path])
        patch = open(patch_path, 'rb').read()
    else:
        patch = bps.create(src, rom, b'')
        open(patch_path, 'wb').write(patch)
    assert bps.apply(patch, src) == rom, 'patch does not re-apply byte-exact'
    alternate_name = name + '_No_Battle_Parallax.bps'
    alternate_patch = bps.create(src, alternate, b'')
    assert bps.apply(alternate_patch, src) == alternate, 'alternate patch does not re-apply byte-exact'
    open(os.path.join(out, alternate_name), 'wb').write(alternate_patch)
    webpatch.render_patcher(patch, os.path.join(out, 'Patcher.html'),
                            template=os.path.join(ROOT, 'release', 'patcher_template.html'),
                            tokens={'TITLE': 'Phantasy Star III: English Retranslation', 'SUBTITLE': 'v' + ver,
                                    'GAME': 'Phantasy Star III - Generations of Doom (USA, Europe)',
                                    'PATCH': name + '.bps',
                                    'OUT_NAME': 'Phantasy Star III - English Retranslation v' + ver,
                                    'README_NOTE': '', 'HINT': ''})
    tokens = {'VERSION': ver, 'DATE': datetime.date.today().isoformat(), 'PATCH': name + '.bps',
              'ALT_PATCH': alternate_name,
              'OUT_CHECKSUM': '%04X' % expand.checksum(rom)}
    for k, v in hashes(src).items():
        tokens['SRC_' + k] = v
    for k, v in hashes(rom).items():
        tokens['OUT_' + k] = v
    for k, v in hashes(alternate).items():
        tokens['ALT_' + k] = v
    tokens['ALT_CHECKSUM'] = '%04X' % expand.checksum(alternate)
    text = open(os.path.join(ROOT, 'release', 'readme_template.txt'), encoding='utf-8').read()
    for k, v in tokens.items():
        text = text.replace('@%s@' % k, v)
    left = re.findall(r'@[A-Z][A-Z0-9_]*@', text)
    if left:
        raise SystemExit('unfilled readme tokens: %s' % ', '.join(sorted(set(left))))
    open(os.path.join(out, 'readme.txt'), 'w', encoding='utf-8', newline='\r\n').write(text)
    zpath = os.path.join(ROOT, 'release', name + '.zip')
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(out)):
            z.write(os.path.join(out, f), name + '/' + f)
    print('wrote %s (%d-byte standard patch, %d-byte no-parallax patch)' %
          (zpath, len(patch), len(alternate_patch)))


if __name__ == '__main__':
    main()
