"""Build the retranslation ROM from source.

    python tools/sourcebuild.py [out.bin] [--no-gen] [--keep-going]

1. gentext.py writes work/dialogue.json and work/script.json into PSIII_Disasm/ps3.asm
   (skipped with --no-gen);
2. the assembler runs (PSIII_Disasm/build.bat: asw + p2bin);
3. the header checksum is fixed in Python (build.bat's fixheader is not on PATH when the
   script runs it) and the ROM is copied to `out.bin` (default: ps3en.bin in the repo root).

The assembler log is shown and the build fails on any assembler error. The size of the ROM
is checked against the header's end address.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'md'))
DISASM = os.path.join(ROOT, 'PSIII_Disasm')
BUILT = os.path.join(DISASM, 'ps3built.bin')


def run(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True, shell=True)
    return p.returncode, p.stdout + p.stderr


def assemble():
    for f in ('ps3.log', 'ps3.p', 'ps3.h'):
        try:
            os.remove(os.path.join(DISASM, f))
        except FileNotFoundError:
            pass
    if os.path.exists(BUILT):
        shutil.move(BUILT, BUILT.replace('.bin', '.prev.bin'))
    cmd = 'AS\\win32\\asw.exe -xx -c -E -A -L ps3.asm'
    rc, out = run(cmd, DISASM)
    log = os.path.join(DISASM, 'ps3.log')
    if os.path.exists(log):
        print(open(log, encoding='latin-1').read())
        raise SystemExit('assembler reported errors (see PSIII_Disasm/ps3.log)')
    tail = [l for l in out.splitlines() if l.strip()][-4:]
    print('\n'.join(tail))
    rc, out = run('AS\\win32\\ps3p2bin.exe ps3.p ps3built.bin ps3.h', DISASM)
    if rc != 0 or not os.path.exists(BUILT):
        print(out)
        raise SystemExit('p2bin failed')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    out = args[0] if args else os.path.join(ROOT, 'ps3en.bin')
    if '--no-gen' not in sys.argv:
        rc = subprocess.call([sys.executable, os.path.join(HERE, 'gentext.py')])
        if rc != 0:
            raise SystemExit('gentext.py failed')
    assemble()
    import expand
    rom = open(BUILT, 'rb').read()
    end = int.from_bytes(rom[0x1A4:0x1A8], 'big') + 1
    if end != len(rom):
        raise SystemExit('ROM is %d bytes but the header says %d' % (len(rom), end))
    fixed = expand.fix_checksum(rom)
    if fixed != rom:
        open(BUILT, 'wb').write(fixed)
        print('checksum fixed: %04X' % expand.checksum(fixed))
    shutil.copyfile(BUILT, out)
    import hashlib
    print('%s  %d bytes  sha256 %s' % (out, len(fixed), hashlib.sha256(fixed).hexdigest()))


if __name__ == '__main__':
    main()
