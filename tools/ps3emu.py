"""Drive Phantasy Star III under BlastEm 0.6.2 through its GDB stub.

    from ps3emu import PS3
    with PS3("ps3en.bin") as em:      # boots from power-on
        em.frames(120)
        em.press("S")                 # Start on the title
        em.shot("work/analysis/title.png")

A frame is one hit of the breakpoint on ReadJoypad's `move.b (a1), d1` (right after
`not.b d0`); the wanted pad state is written into d0 there, so the emulator window never
sees the keyboard. Bits are the game's own: U D L R = 0-3, B 4, C 5, A 6, Start 7.

`shot()` captures the emulator window (works while BlastEm is stopped in the stub).
`ram(addr, n)` reads work RAM; `sram(slot)` reads a save slot's odd bytes.

BlastEm is looked for at ../ps4-translate/blastem-win32-0.6.2/blastem.exe and then at
blastem-win32-0.6.2/blastem.exe beside this repository (set BLASTEM to override).
Savestates are not used: the game is driven from reset, which makes every scenario a
deterministic pad script (see tools/scenarios.py).
"""
import os
import re
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, 'md'))
import blastem_drive   # noqa: E402
import winshot         # noqa: E402

BUTTON = blastem_drive.BUTTON
_CANDIDATES = [os.environ.get('BLASTEM', ''),
               os.path.join(ROOT, 'blastem-win32-0.6.2', 'blastem.exe'),
               os.path.join(os.path.dirname(ROOT), 'ps4-translate', 'blastem-win32-0.6.2', 'blastem.exe')]
BLASTEM = next((p for p in _CANDIDATES if p and os.path.exists(p)), _CANDIDATES[1])
LST = os.path.join(ROOT, 'PSIII_Disasm', 'ps3.lst')


def listing_address(label, after=None, lst=LST):
    return blastem_drive.listing_address(lst, label, after)


class PS3(blastem_drive.BlastEm):
    def __init__(self, rom, port=1234, lst=LST, sram=None):
        self.rom = os.path.abspath(rom)
        self.lst = lst
        self.pad = 0
        self.frame = 0
        self.bps = set()
        self.log = None
        self.vints = 0
        self.lag_samples = []
        self.vint_log = []
        args = [BLASTEM, self.rom, '-D']
        self.proc = subprocess.Popen(args, cwd=os.path.dirname(BLASTEM),
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.sock = None
        for _ in range(100):
            try:
                self.sock = socket.create_connection(('127.0.0.1', port), timeout=1)
                break
            except OSError:
                time.sleep(0.1)
        if not self.sock:
            self.proc.kill()
            raise RuntimeError("BlastEm's GDB stub did not answer")
        self.sock.settimeout(60)
        self.buf = b''
        self.pad_bp = listing_address('ReadJoypad', r'move\.b\s+\(a1\), d1', lst)
        self.breakpoint(self.pad_bp)
        self.vint_bp = None

    # ReadJoypad is called for both pads in one VBlank; only the first call is a frame
    def step_frame(self, hook=None):
        while True:
            pc = self.cont()
            if pc == self.pad_bp:
                a1 = self.regs()['a'][1]
                if a1 == 0xFFFFD000:
                    self.setreg(0, self.pad)
                    self.frame += 1
                    return
                self.setreg(0, 0)
                continue
            if hook:
                hook(pc)

    def ram(self, addr, n):
        return self.read(addr, n)

    def sram(self, slot, n=0x800):
        """The odd-byte payload of backup RAM slot `slot` ($1000 bytes of address space)."""
        raw = self.read(0x200000 + slot * 0x1000, n * 2)
        return bytes(raw[1::2])

    def shot(self, path):
        hw = winshot.windows_of_pid(self.proc.pid)
        if not hw:
            raise RuntimeError('no BlastEm window')
        winshot.capture(self.proc.pid, path)
        return path


if __name__ == '__main__':
    rom = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'ps3en.bin')
    with PS3(rom) as em:
        em.frames(200)
        em.press('S')
        em.frames(60)
        print(em.shot(os.path.join(ROOT, 'work', 'analysis', 'boot.png')))


# ---------------------------------------------------------------- scenario helpers
SCREEN_TITLE, SCREEN_GAMESEL, SCREEN_MAIN = 4, 0xC, 0x10


def boot_to_field(em, saves=0):
    """Power-on -> title -> game select -> (no saves) text speed -> new game -> Landen.
    Returns when the player controls Rhys in Landen town (map $5A)."""
    while em.word(0xFFFFD012) != SCREEN_TITLE:
        em.frames(1)
    em.frames(60); em.press('S')
    while em.word(0xFFFFD012) != SCREEN_GAMESEL:
        em.frames(1)
    em.frames(150)
    for _ in range(4):
        em.press('C'); em.frames(60)
    while not (em.word(0xFFFFD012) == SCREEN_MAIN and em.word(0xFFFFD022) == 0x5A):
        em.press('C', hold=2, release=6)
    em.frames(30)


def teleport(em, map_id, x, y, facing=0x1018):
    """Fake a door transition: the field loop reloads the map next frame."""
    em.write(0xFFFFD024, map_id.to_bytes(2, 'big'))
    em.write(0xFFFFD04A, x.to_bytes(2, 'big') + y.to_bytes(2, 'big'))
    em.write(0xFFFFD04E, facing.to_bytes(2, 'big'))
    em.write(0xFFFFD005, bytes([em.byte(0xFFFFD005) | 0x10]))
    em.frames(90)


def objects(em, base=0xFFFFC300, n=26, size=0x40):
    tab = em.read(base, size * n)
    out = []
    for i in range(n):
        o = tab[i * size:(i + 1) * size]
        if o[0]:
            out.append((i, o))
    return out
