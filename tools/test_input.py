"""VBlank's joypad read under the interpreter, with a model of the pad on port 1.

The interrupt skips ReadJoypads while bit 6 of $FFFFD006 (a VRAM copy in progress) or
bit 3 (the Z80 stopped) is set, but still sets the frame flag, so the main loop runs a
frame on whatever joypad_pressed holds. With fix_input_repeat the skipping path clears
the pressed bytes: one press is acted on once, and a press made during a skipped frame
is still reported by the next read. With the option off the stale byte stands (the
stock behaviour, which let a technique's ally target move twice for one press).

    python tools/test_input.py
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from ps3harness import Machine, Symbols

HELD, PRESSED, HELD2, PRESSED2 = 0xFFFFD000, 0xFFFFD001, 0xFFFFD002, 0xFFFFD003
FLAGS = 0xFFFFD006          # bit 6: VRAM copy in progress, bit 3: Z80 stopped
FRAME = 0xFFFFD004          # bit 7: set by every interrupt
PORT1, PORT2 = 0xA10003, 0xA10005
Z80_BUSREQ = 0xA11100       # reads 0: the bus is granted at once
STUB = 0xFFFFF000           # an rts the interrupt returns to
RIGHT, LEFT = 0x08, 0x04


class Pad(Machine):
    """Port 1 answers for the buttons in self.pad (1 = pressed, the game's bit order)."""

    def __init__(self):
        super().__init__()
        self.pad = 0
        self.th = 0x40

    def wb(self, addr, v):
        if addr & 0xFFFFFF in (PORT1, PORT2):
            self.th = v & 0x40
            return
        super().wb(addr, v)

    def rb(self, addr):
        a = addr & 0xFFFFFF
        if a == PORT1:
            if self.th:
                return 0x40 | (~self.pad & 0x3F)            # C B Right Left Down Up
            return (~(self.pad >> 2)) & 0x30                # Start A
        if a == PORT2:
            return 0x7F if self.th else 0x3F                # nothing pressed
        if a == Z80_BUSREQ:
            return 0
        return super().rb(addr)


def skip_to_stub(cpu):
    cpu.pc = STUB


def vblank(m, sym, flags=0):
    m.poke(FLAGS, bytes([flags]))
    m.poke(FRAME, bytes([0]))
    m.poke(STUB, b'\x4E\x75')
    sp = 0xFFFFFE00 - 4
    m.wl(sp, m.SENTINEL)
    m.wl(sp - 4, STUB)                                      # the interrupt frame: SR, PC
    m.ww(sp - 6, 0x2000)
    m.a[7] = sp - 6
    m.pc = sym['VBlank']
    m.steps = 0
    m.run(2000000)
    assert m.peek(FRAME, 1)[0] & 0x80, 'frame flag not set'
    return m.peek(HELD, 4)


def main():
    sym = Symbols()
    opt = re.search(r'=\$([01])\s+fix_input_repeat = [01]', sym.text)
    assert opt, 'fix_input_repeat not in the listing'
    fix = int(opt.group(1))
    m = Pad()
    # The interrupt's other work (sprite table, scroll and sound updates) does not touch
    # the pads; return from it at once.
    for name in ('loc_729E', 'loc_6EA0', 'loc_71A6'):
        m.on_pc[sym[name]] = skip_to_stub
    for skip in (0x40, 0x08):
        m.poke(HELD, bytes(4))
        m.pad = RIGHT
        held, pressed, _, _ = vblank(m, sym)
        assert (held, pressed) == (RIGHT, RIGHT), (held, pressed)
        m.poke(PRESSED2, bytes([0x10]))
        held, pressed, _, pressed2 = vblank(m, sym, skip)   # the frame overran into a copy
        if fix:
            assert (held, pressed, pressed2) == (RIGHT, 0, 0), (skip, held, pressed, pressed2)
        else:
            assert (held, pressed) == (RIGHT, RIGHT), (skip, held, pressed)
        held, pressed, _, _ = vblank(m, sym)                # still held: no new press
        assert (held, pressed) == (RIGHT, 0), (held, pressed)
        m.pad = 0
        vblank(m, sym)
        m.pad = LEFT                                        # pressed during a skipped frame
        held, pressed, _, _ = vblank(m, sym, skip)
        assert held == 0 and pressed == 0, (held, pressed)
        held, pressed, _, _ = vblank(m, sym)                # ... reported by the next read
        assert (held, pressed) == (LEFT, LEFT), (held, pressed)
        m.pad = 0
        vblank(m, sym)
    print('  fix_input_repeat = %d: %s' % (fix, 'a skipped read clears the pressed bytes, no press lost'
                                           if fix else 'a skipped read leaves the pressed byte standing (stock)'))
    print('test_input: all passed')


if __name__ == '__main__':
    main()
