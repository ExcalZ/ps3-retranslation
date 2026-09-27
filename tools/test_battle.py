"""Focused regressions for battle transition and result-message fixes."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from ps3harness import Machine, Symbols  # noqa: E402


A6 = 0xFFFFD280
SOUND_QUEUE = 0xFFFFD11E
SOUND_QUEUE_SAVED = 0xFFFFD11F
MAP_MUSIC = 0xFFFFD120
CHAR_NAME_SAVED = 0xFFFFD480
MAP_ID = 0xFFFFD022


def test_battle_music(sym):
    """Castle music comes from the map header, not its entrance command."""
    for map_id, queued, entrance_command, expected in (
        (0x3C, 0x91, 0x00, 0x91),  # event music remains authoritative
        (0x3C, 0xE0, 0x00, 0x9F),  # Landen Castle after fade
        (0x44, 0xE0, 0xFF, 0x95),  # Shusoran Castle after fade
        (0x44, 0xFF, 0xFF, 0x95),  # stop command after map entry
        (0x44, 0xB0, 0xFF, 0x95),  # sound effect is not music
    ):
        m = Machine()
        m.ww(MAP_ID, map_id)
        m.wb(SOUND_QUEUE, queued)
        m.wb(MAP_MUSIC, entrance_command)
        m.call(sym['Battle_SaveMusic'])
        assert m.rb(SOUND_QUEUE_SAVED) == expected, (map_id, queued)

        # The battle exit fades music first, then queues the saved ID.
        m.poke(sym['VDPDisableVInterrupt'], b'\x4e\x75')
        m.poke(sym['VDPEnableVInterrupt'], b'\x4e\x75')
        read_byte = m.rb
        m.rb = lambda addr: 0 if (addr & 0xFFFFFF) == 0xA11100 else read_byte(addr)
        m.wb(SOUND_QUEUE, 0xE0)
        m.call(sym['UpdateSoundQueue'], d0=m.rb(SOUND_QUEUE_SAVED))
        assert m.rb(SOUND_QUEUE) == expected


def test_battle_exit_has_no_pending_audio_fade(sym):
    """Fast battle exits must not queue an E0 fade before restoring music."""
    m = Machine()
    code = m.peek(sym['loc_CE4A'], sym['loc_CE7C'] - sym['loc_CE4A'])
    fade_call = b'\x4e\xb9' + sym['loc_147E0'].to_bytes(4, 'big')
    assert fade_call not in code


def test_enemy_star_force_name(sym):
    """Enemy Gires targets a battle object, whose name is a pointer at +$34."""
    m = Machine()
    target = 0xFFFFCC00
    name = sym['EnemyName_Dryad']
    m.ww(A6 + 0x72, target)
    m.ww(A6 + 0x74, 17)
    m.wl(target + 0x34, name)

    # This regression concerns loc_1051A's result setup. The renderer itself
    # is covered by test_vwf; return immediately after the setup here.
    m.poke(sym['loc_FF0A'], b'\x4E\x75')
    m.call(sym['loc_1051A'], a6=A6)

    assert m.rl(CHAR_NAME_SAVED) == name
    assert m.rl(0xFFFFD4A0) == 17


def test_stale_input(sym):
    """A VBlank that skips the pad read leaves no pressed edges behind.

    The proportional redraw after a target-cursor step writes VRAM across a
    VBlank; the stock handler then kept the previous frame's pressed byte and
    the target routine stepped again on the same tap (the user's slot 6: one
    Right moved the ally cursor three names)."""
    for busy in (0x40, 0x08):   # VRAM being written, Z80 stopped
        m = Machine()
        m.poke(sym['HBlank'], b'\x4e\x75')   # rte -> rts back to the sentinel
        m.wb(0xFFFFD006, busy)
        m.poke(0xFFFFD000, b'\x08\x08\x01\x01')   # held/pressed, both pads
        m.call(sym['VBlank'])
        assert m.peek(0xFFFFD000, 4) == b'\x08\x00\x01\x00', (busy, m.peek(0xFFFFD000, 4))


def test_target_left(sym):
    """Left steps a battle target picker back; the other directions step on.

    The user's slot 6 (2026-09-24): five in the party, choosing Res's target
    (type 2, one ally) in routine $D8. The redraw calls are stubbed; the
    picker's own validation runs."""
    ram = open(os.path.join(ROOT, 'work', 'states', 'user-techtarget-slot6-20260924.ram'), 'rb').read()
    m = Machine(ram=ram)
    for label in ('loc_C9C2', 'loc_C9E6', 'loc_CF52', 'loc_CF72', 'loc_FF30'):
        m.poke(sym[label], b'\x4e\x75')
    seen = []
    for bit in [4] * 6 + [8] * 6 + [1, 2]:   # Left, Right, Up, Down
        m.wb(0xFFFFD001, bit)
        m.call(sym['loc_E7B4'], a6=A6)
        seen.append(m.rb(A6 + 0xD))
    assert seen == [4, 3, 2, 1, 0, 4, 0, 1, 2, 3, 4, 0, 1, 2], seen
    # Defend's ally picker: routine $144 steps, $148 validates as type 2
    m.wb(A6 + 0xD, 0)
    seen = []
    for bit in [4] * 6 + [8] * 6:
        m.wb(0xFFFFD001, bit)
        m.call(sym['loc_E85C'], a6=A6)
        m.call(sym['loc_E83E'], a6=A6)
        seen.append(m.rb(A6 + 0xD))
    assert seen == [4, 3, 2, 1, 0, 4, 0, 1, 2, 3, 4, 0], seen
    # one enemy (type $A): live slots 0, 2 and 5
    for start, want in ((2, 0), (0, 5), (5, 2)):
        m.poke(0xFFFFD102, b'\x00\x25')
        m.wb(A6 + 0xD, start)
        m.call(sym['BattleTarget_Prev'], d0=0xA, a6=A6)
        assert m.rb(A6 + 0xD) == want, (start, m.rb(A6 + 0xD))


def main():
    sym = Symbols()
    test_battle_music(sym)
    print('ok   battle music saves a track, not a sound command')
    test_battle_exit_has_no_pending_audio_fade(sym)
    print('ok   battle exit has no delayed music fade')
    test_enemy_star_force_name(sym)
    print('ok   enemy Star Force uses its battle-object name pointer')
    test_stale_input(sym)
    print('ok   a VBlank without a pad read clears the pressed edges')
    test_target_left(sym)
    print('ok   Left steps a battle or Defend target back, other directions forward')


if __name__ == '__main__':
    main()
