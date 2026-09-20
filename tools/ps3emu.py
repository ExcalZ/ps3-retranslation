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
    def __init__(self, rom, port=1234, lst=LST, sram=None, state=None):
        """`state`: a BlastEm .state saved by save_state (its .ram beside it): the game
        resumes there, through the 0.6.2 reset-on-load workaround of the base class, with
        the work RAM put back from the .ram file."""
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
        if state:
            args += ['-s', os.path.abspath(state)]
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
        if state:
            self._survive_startup_reset(os.path.abspath(state))
        self.pad_bp = listing_address('ReadJoypad', r'move\.b\s+\(a1\), d1', lst)
        self.breakpoint(self.pad_bp)
        self.vint_bp = None

    def _survive_startup_reset(self, state):
        """As the base class, but the work RAM comes from the .ram file save_state wrote
        beside the state (the base class needs a reference RAM image this repository
        does not carry), and the sound-driver stubs use this game's labels."""
        r = self.regs()
        pc = r['pc']
        entry = int.from_bytes(self.read(4, 4), 'big')
        for label in ('JumpTo_UpdateSound',):
            try:
                self.write(listing_address(label), bytes([0x4E, 0x75]))
            except KeyError:
                pass
        self.write(entry, bytes([0x33, 0xFC, 0x01, 0x00, 0x00, 0xA1, 0x12, 0x00, 0x4E, 0xF9]) + pc.to_bytes(4, 'big'))
        self.breakpoint(entry)
        stop = self.cont()
        assert stop == entry, 'expected the startup reset at %06X, stopped at %06X' % (entry, stop)
        self.write_ram(open(os.path.splitext(state)[0] + '.ram', 'rb').read())
        for i in range(8):
            self.setreg(i, r['d'][i])
            self.setreg(8 + i, r['a'][i])
        self.setreg(16, r['sr'])
        self.unbreak(entry)

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
        if not getattr(self, '_topmost', False):
            # the window DC only holds BlastEm's own pixels while nothing covers the
            # window: raise it (asynchronously - its thread is stopped in the stub, so
            # the request is served during the next frames) before the first capture
            import ctypes
            swp = ctypes.windll.user32.SetWindowPos
            swp.argtypes = [ctypes.c_void_p] * 2 + [ctypes.c_int] * 4 + [ctypes.c_uint]
            for h in hw:   # HWND_TOPMOST; NOSIZE | NOMOVE | NOACTIVATE | ASYNCWINDOWPOS
                swp(h, ctypes.c_void_p(-1), 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010 | 0x4000)
            self._topmost = True
            self.frames(2)
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


# ---------------------------------------------------------------- snapshots
# A snapshot is the 64 KB of work RAM plus the CPU registers, taken at the pad
# breakpoint, and it resumes into a fresh BlastEm at that same breakpoint: RAM
# and registers go back, the CPU returns through the snapshot's own stack, and
# a faked map transition makes the game rebuild VRAM, CRAM and the VDP from
# RAM (a snapshot must therefore be taken on a map the field loop can reload,
# not in a battle or a menu). RAM holds ROM addresses (object routines,
# script and name pointers), so a snapshot is tied to the ROM's layout: it is
# keyed by the ROM's SHA-256 and is remade when the ROM changes.
STATES = os.path.join(ROOT, 'work', 'states')


def _rom_key(rom):
    import hashlib
    return hashlib.sha256(open(rom, 'rb').read()).hexdigest()[:16]


def snapshot(em, name):
    """Save work RAM and registers under work/states/<name>-<romkey>.snap."""
    os.makedirs(STATES, exist_ok=True)
    path = os.path.join(STATES, '%s-%s.snap' % (name, _rom_key(em.rom)))
    r = em.regs()
    hdr = b''.join(v.to_bytes(4, 'big') for v in r['d'] + r['a'] + [r['sr'], r['pc'], em.frame])
    open(path, 'wb').write(hdr + em.read(0xFF0000, 0x10000))
    return path


def resume(em, name):
    """Put a snapshot back into a BlastEm that has just started (its first pad read),
    then reload its map at the player's position so VRAM follows. Returns False when no
    snapshot matches the ROM."""
    path = os.path.join(STATES, '%s-%s.snap' % (name, _rom_key(em.rom)))
    if not os.path.exists(path):
        return False
    data = open(path, 'rb').read()
    v = [int.from_bytes(data[i:i + 4], 'big') for i in range(0, 19 * 4, 4)]
    em.write_ram(data[19 * 4:])
    for i in range(16):
        em.setreg(i, v[i])
    em.setreg(16, v[16])
    em.frame = v[18]
    teleport(em, em.word(0xFFFFD022), em.word(0xFFFFC008), em.word(0xFFFFC00A), em.word(0xFFFFD04E))
    # the map reload rebuilt the map's art but not the font block (tiles $00-$FF, loaded
    # once at game start by map $210): load it through the game's own routine from a
    # trampoline in the unused part of BlastEm's 1 MB ROM copy, entered by the return
    # address on the stack at the pad breakpoint (the stub cannot set PC)
    font = listing_address('loc_66000')
    loader = listing_address('LoadDataInVRAMWithOffset')
    sp = em.regs()['a'][7]
    ret = int.from_bytes(em.read(sp, 4), 'big')
    tramp = 0xF0000
    code = (bytes([0x48, 0xE7, 0xFF, 0xFE])                        # movem.l d0-d7/a0-a6, -(sp)
            + bytes([0x41, 0xF9]) + font.to_bytes(4, 'big')          # lea (font).l, a0
            + bytes([0x70, 0x00])                                    # moveq #0, d0
            + bytes([0x32, 0x3C, 0x20, 0x00])                        # move.w #$2000, d1
            + bytes([0x4E, 0xB9]) + loader.to_bytes(4, 'big')        # jsr (loader).l
            + bytes([0x4C, 0xDF, 0x7F, 0xFF])                        # movem.l (sp)+, d0-d7/a0-a6
            + bytes([0x4E, 0xF9]) + ret.to_bytes(4, 'big'))          # jmp (ret).l
    em.write(tramp, code)
    em.write(sp, tramp.to_bytes(4, 'big'))
    em.frames(2)
    return True


def boot_to_field(em, saves=0):
    """Power-on -> title -> game select -> (no saves) text speed -> new game -> Landen.
    Returns when the player controls Rhys in Landen town (map $5A). With a 'landen'
    snapshot for this ROM (work/states/) it resumes there instead, in a few seconds; the
    long way takes the snapshot for next time."""
    em.frames(1)
    if resume(em, 'landen'):
        if em.word(0xFFFFD012) == SCREEN_MAIN and em.word(0xFFFFD022) == 0x5A:
            return
    while em.word(0xFFFFD012) != SCREEN_TITLE:
        em.frames(1)
    em.frames(60); em.press('S')
    while em.word(0xFFFFD012) != SCREEN_GAMESEL:
        em.frames(1)
    new_game_intro(em)
    while not (em.word(0xFFFFD012) == SCREEN_MAIN and em.word(0xFFFFD022) == 0x5A):
        em.press('C', hold=2, release=6)
    em.frames(30)
    snapshot(em, 'landen')


def new_game_intro(em):
    """From the game-select screen with no saves: press through the slot checks and the
    text-speed prompt until the opening (map $3AE) starts. State-driven, so a press that
    lands during a transition is simply repeated."""
    em.frames(150)
    while em.word(0xFFFFD022) != 0x3AE:
        em.press('C', hold=2, release=30)


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


def npc_list(em):
    """(slot, x, y, script_offset) of the NPC objects on the current map."""
    out = []
    for i, o in objects(em):
        if int.from_bytes(o[4:8], 'big') == 0x1D9A:
            out.append((i, int.from_bytes(o[8:10], 'big'), int.from_bytes(o[10:12], 'big'),
                        int.from_bytes(o[0x26:0x28], 'big')))
    return out


def walk_to(em, x, y, tries=4):
    """Walk Rhys to (x, y) with the d-pad (16 px per tile, 1 px per frame)."""
    for _ in range(tries):
        px, py = em.word(0xFFFFC008), em.word(0xFFFFC00A)
        dx, dy = x - px, y - py
        if not dx and not dy:
            return True
        if dx:
            em.pad = BUTTON['R' if dx > 0 else 'L']; em.frames(abs(dx)); em.pad = 0; em.frames(8)
        if dy:
            em.pad = BUTTON['D' if dy > 0 else 'U']; em.frames(abs(dy)); em.pad = 0; em.frames(8)
    return (em.word(0xFFFFC008), em.word(0xFFFFC00A)) == (x, y)


def talk(em, npc_x, npc_y):
    """Stand above an NPC, face it and press A (A = talk, C = menu)."""
    walk_to(em, npc_x, npc_y - 16)
    em.pad = BUTTON['D']; em.frames(2); em.pad = 0; em.frames(8)
    em.press('A', hold=2, release=2)


STATE_DIR = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'blastem')


def save_state(em, path):
    """Press BlastEm's save-state key (the backtick, ui.save_state) in its window and copy
    the quicksave it writes to `path`. The .state holds VRAM, CRAM, VSRAM and the VDP
    registers, which the stub cannot read (tools/vramaudit.py reads them back)."""
    import ctypes, shutil
    sys.path.insert(0, os.path.join(HERE, 'md'))
    import winshot
    d = os.path.join(STATE_DIR, os.path.splitext(os.path.basename(em.rom))[0])
    q = os.path.join(d, 'quicksave.state')
    if os.path.exists(q):
        os.remove(q)
    for h in winshot.windows_of_pid(em.proc.pid):
        ctypes.windll.user32.PostMessageW(h, 0x100, 0xC0, 0x00290001)
        ctypes.windll.user32.PostMessageW(h, 0x101, 0xC0, 0xC0290001)
    for _ in range(120):
        em.frames(1)
        if os.path.exists(q):
            break
    em.frames(5)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    shutil.copy(q, path)
    open(os.path.splitext(path)[0] + '.ram', 'wb').write(em.read(0xFF0000, 0x10000))   # for vramaudit's locator
    return path


def soft_reset(em):
    """Restart the game without restarting BlastEm (backup RAM survives): at the pad-read
    breakpoint the top of the stack is ReadJoypad's return address, so point it at the
    entry point. The stub cannot set PC directly (P11 answers E01)."""
    sp = em.regs()['a'][7]
    entry = int.from_bytes(em.read(4, 4), 'big')
    em.write(sp, entry.to_bytes(4, 'big'))
    em.frames(2)
    while em.word(0xFFFFD012) != SCREEN_TITLE:
        em.frames(1)
