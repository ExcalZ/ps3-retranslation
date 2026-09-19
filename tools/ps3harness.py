"""Run routines of the assembled PS3 ROM under the tools/md/emu68k.py interpreter, with a
model of the VDP data port that records VRAM writes.

    from ps3harness import Machine, Symbols
    sym = Symbols()
    m = Machine()                      # ROM at 0, 64 KB of zero work RAM
    m.a[6] = 0xFFFFD280
    m.call(sym['loc_10038'], a0=text_addr, a1=0xFFFF9D26, d0=0x8000)
    m.vram[0x1800:0x1820]              # the first pool tile

The interpreter refuses opcodes it does not model instead of guessing, so a Trap means
"model that opcode", not "the ROM is wrong". Tests seed only the RAM they need.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, 'md'))
from emu68k import CPU, Trap   # noqa: E402,F401

ROM = os.environ.get('PS3_ROM', os.path.join(ROOT, 'PSIII_Disasm', 'ps3built.bin'))
LST = os.environ.get('PS3_LST', os.path.join(ROOT, 'PSIII_Disasm', 'ps3.lst'))

VDP_DATA, VDP_CTRL = 0xC00000, 0xC00004


class Symbols:
    """Label -> address from the assembler listing (labels of ps3.asm and its includes)."""

    def __init__(self, path=LST):
        self.text = open(path, encoding='latin-1').read()
        self._cache = {}

    def __getitem__(self, name):
        if name not in self._cache:
            m = re.search(r'/\s*([0-9A-F]{1,6}) :\s+(?:[0-9A-F]{4}\s+)*\s*' + re.escape(name) + r':', self.text)
            if not m:
                raise KeyError(name)
            self._cache[name] = int(m.group(1), 16)
        return self._cache[name]

    def value(self, name):
        """Value of a `name = expr` symbol from the listing's symbol table."""
        m = re.search(r'^\s*' + re.escape(name) + r'\s+.*?\s([0-9A-F]+)\s*$', self.text, re.M)
        return int(m.group(1), 16) if m else None


class Machine(CPU):
    def __init__(self, rom=None, ram=None):
        rom = rom if rom is not None else open(ROM, 'rb').read()
        mem = bytearray(0x1000000)
        mem[:len(rom)] = rom
        if ram:
            mem[0xFF0000:0xFF0000 + len(ram)] = ram
        super().__init__(mem, pc=0, sp=0xFFFFFE00)
        self.vram = bytearray(0x10000)
        self.vram_writes = []
        self._ctrl = []
        self._vdp_addr = 0
        self._vdp_code = 0
        self._pend = {}
        self.inc = 2

    def wb(self, addr, v):
        a = addr & 0xFFFFFF
        if 0xC00000 <= a <= 0xC00007:
            self._vdp_byte(a, v & 0xFF)
            return
        self.m[a] = v & 0xFF

    def rb(self, addr):
        a = addr & 0xFFFFFF
        if 0xC00004 <= a <= 0xC00007:
            return 0x34 if (a & 1) else 0x00
        return self.m[a]

    def _vdp_byte(self, a, v):
        port = VDP_CTRL if a >= 0xC00004 else VDP_DATA
        if a & 1:
            word = (self._pend.pop(port, 0) << 8) | v
            self._vdp_word(port, word)
        else:
            self._pend[port] = v

    def _vdp_word(self, port, w):
        if port == VDP_CTRL:
            if w & 0x8000 and not self._ctrl:
                if (w >> 8) == 0x8F:
                    self.inc = w & 0xFF
                return
            self._ctrl.append(w)
            if len(self._ctrl) == 2:
                w1, w2 = self._ctrl
                self._vdp_addr = (w1 & 0x3FFF) | ((w2 & 3) << 14)
                self._vdp_code = ((w1 >> 14) & 3) | ((w2 >> 2) & 0x3C)
                self._ctrl = []
            return
        if self._vdp_code & 1:
            at = self._vdp_addr & 0xFFFF
            self.vram[at] = (w >> 8) & 0xFF
            self.vram[(at + 1) & 0xFFFF] = w & 0xFF
            self.vram_writes.append(at)
            self._vdp_addr = (self._vdp_addr + self.inc) & 0xFFFF

    # -- convenience --------------------------------------------------------
    def poke(self, addr, data):
        for i, b in enumerate(data):
            self.m[(addr + i) & 0xFFFFFF] = b

    def peek(self, addr, n):
        return bytes(self.m[(addr + i) & 0xFFFFFF] for i in range(n))

    def call(self, pc, limit=2000000, **regs):
        """Run from pc until the sentinel return; register overrides as d0=..., a1=..."""
        for k, v in regs.items():
            idx = int(k[1])
            (self.d if k[0] == 'd' else self.a)[idx] = v & 0xFFFFFFFF
        self.a[7] = 0xFFFFFE00 - 4
        self.wl(self.a[7], self.SENTINEL)
        self.pc = pc
        self.steps = 0
        self.run(limit)
        return self.steps
