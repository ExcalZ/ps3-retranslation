"""Run the dialogue VWF engine (ext/vwf.asm) under the 68000 interpreter and compare its
output - window tilemap rows and the pool tiles it uploads - with a Python reference
composer built from the same font binaries.

    python tools/test_vwf.py

Covers: plain text, {BR}, {PAGE} continuation state, {NAME} inserts, {NUM} numbers,
clipping at the right edge, the page scroll (VWFDia_ScrollUp), the fixed-width
fallback for windows that are not the dialogue's, the opening scroll, and the field
menu (pool tile per screen cell, main-list staging, $44(a6) padding, and the
hand-off past row 24).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import ps3text                       # noqa: E402
from ps3harness import Machine, Symbols   # noqa: E402

V = os.path.join(ROOT, 'PSIII_Disasm', 'vwf')
FONT = open(os.path.join(V, 'diafont.bin'), 'rb').read()
WIDTH = open(os.path.join(V, 'diawidth.bin'), 'rb').read()
POOL, CELLS, STRIDE = 0xC0, 24, 0x34
CTX = 0xFFFFD280
TEMPLATE_ROW0, LIVE_ROW0, LIVE_ROW1 = 0xFFFF9D26, 0xFFFF9AB6, 0xFFFF9B1E
NAMES = 0xFFFFD480         # char_name_saved: pointer table for {NAME:nn}
NUMS = 0xFFFFD4A0          # longs for {NUM:nn}
TEXT = 0x0FF000            # scratch text lives in the unused part of the 1 MB window


def compose(line_bytes):
    """Reference: 1bpp canvas rows (24 bytes each) and the pen position for one line."""
    canvas = [bytearray(26) for _ in range(8)]
    x = 0
    for b in line_bytes:
        w = WIDTH[b]
        if w == 0:
            continue
        if x + w - 1 > 192:
            continue
        for r in range(8):
            v = (FONT[b * 8 + r] << 8) >> (x & 7)
            canvas[r][x >> 3] |= (v >> 8) & 0xFF
            canvas[r][(x >> 3) + 1] |= v & 0xFF
        x += w
    return canvas, x


def expand(canvas):
    """Reference: 24 4bpp tiles (ink 1, paper 2)."""
    out = bytearray()
    for c in range(CELLS):
        for r in range(8):
            byte = canvas[r][c]
            for shift in (4, 0):
                nib = (byte >> shift) & 0xF
                v = 0
                for bit in (8, 4, 2, 1):
                    v = (v << 4) | (1 if nib & bit else 2)
                out += v.to_bytes(2, 'big')
    return bytes(out)


def expand_open(canvas, shadow=True):
    """Reference for the scroll: transparent paper, ink 1, a black (2) shadow 1 px right
    and down of the ink."""
    ink = [bytes(r[:26]) for r in canvas]
    sh = [bytearray(26) for _ in range(8)]
    if shadow:
        for r in range(1, 8):
            prev = int.from_bytes(ink[r - 1], 'big') >> 1
            sh[r][:] = prev.to_bytes(26, 'big')
    out = bytearray()
    for c in range(CELLS):
        for r in range(8):
            v = 0
            for bit in range(7, -1, -1):
                mask = 1 << bit
                v = (v << 4) | (1 if ink[r][c] & mask else (2 if sh[r][c] & mask else 0))
            out += v.to_bytes(4, 'big')
    return bytes(out)


def rows(m, row0):
    mark = m.peek(row0, CELLS * 2)
    glyph = m.peek(row0 + STRIDE, CELLS * 2)
    return ([int.from_bytes(mark[i:i + 2], 'big') for i in range(0, CELLS * 2, 2)],
            [int.from_bytes(glyph[i:i + 2], 'big') for i in range(0, CELLS * 2, 2)])


def machine(sym):
    m = Machine()
    m.poke(CTX + 0x42, (STRIDE).to_bytes(2, 'big'))
    m.poke(CTX + 0x44, (CELLS).to_bytes(2, 'big'))
    return m


def render(m, sym, text, row0=TEMPLATE_ROW0, attr=0x8000):
    data = ps3text.encode(text, 'us') + b'\xFC'
    m.poke(TEXT, data)
    m.vram_writes = []
    m.a[6] = CTX
    m.call(sym['loc_10038'], a0=TEXT, a1=row0, d0=attr)
    # the stock renderer leaves a1 at the last line's mark row; the shop list writes
    # the price relative to a1 after the name
    stride = int.from_bytes(m.peek(CTX + 0x42, 2), 'big')
    lines = text.split('{PAGE}')[0].count('{BR}')
    assert m.a[1] & 0xFFFFFF == (row0 + 2 * stride * lines) & 0xFFFFFF, ('a1 after render', hex(m.a[1]), hex(row0), lines)


def check_line(m, line_bytes, row0, line, attr=0x8000, label=''):
    canvas, x = compose(line_bytes)
    cells = (x + 7) // 8
    mark, glyph = rows(m, row0)
    assert mark == [attr | 0x1F] * CELLS, (label, 'mark row', mark)
    want = [attr | (POOL + line * CELLS + i) for i in range(cells)] + [attr | 0x1F] * (CELLS - cells)
    assert glyph == want, (label, 'glyph row', [hex(v) for v in glyph], [hex(v) for v in want])
    base = (POOL + line * CELLS) * 32
    assert bytes(m.vram[base:base + cells * 32]) == expand(canvas)[:cells * 32], (label, 'pool tiles')
    return x


def test_plain(sym):
    m = machine(sym)
    render(m, sym, 'Nothing unusual here.')
    x = check_line(m, b'Nothing unusual here.', TEMPLATE_ROW0, 0, label='plain')
    assert x == sum(WIDTH[b] for b in b'Nothing unusual here.')
    assert m.peek(CTX + 1, 1)[0] & 0x30 == 0, 'no continuation flags'
    print('  plain line ok (%d px)' % x)


def test_br_and_page(sym):
    m = machine(sym)
    render(m, sym, 'The legends of Landen,{BR}your homeland, tell of{PAGE}world-sweeping wars{PAGE}fought.')
    check_line(m, b'The legends of Landen,', TEMPLATE_ROW0, 0, label='br line 0')
    check_line(m, b'your homeland, tell of', TEMPLATE_ROW0 + 2 * STRIDE, 1, label='br line 1')
    flags = m.peek(CTX + 1, 1)[0]
    assert flags & 0x20, 'bit 5 (more text) set after {PAGE}'
    cont = int.from_bytes(m.peek(CTX + 0x3E, 4), 'big')
    assert m.peek(cont, 5) == b'world', 'continuation pointer after the $EC'
    print('  {BR} and {PAGE} ok')
    return m, cont


def test_scroll(sym):
    m, cont = test_br_and_page(sym)
    # the game copies the template into the live window; emulate that for the two rows
    for off in (0, STRIDE, 2 * STRIDE, 3 * STRIDE):
        m.poke(LIVE_ROW0 + off, m.peek(TEMPLATE_ROW0 + off, CELLS * 2))
    # page wait done: scroll up, then render the continuation into the second line
    m.a[6] = CTX
    m.call(sym['VWFDia_ScrollUp'], a0=LIVE_ROW1, a1=LIVE_ROW0)
    check_line(m, b'your homeland, tell of', LIVE_ROW0, 0, label='scrolled line')
    m.poke(CTX + 1, bytes([m.peek(CTX + 1, 1)[0] & ~0x20]))
    m.vram_writes = []
    m.call(sym['loc_10038'], a0=cont, a1=LIVE_ROW1, d0=0x8000)
    check_line(m, b'world-sweeping wars', LIVE_ROW1, 1, label='next page')
    check_line(m, b'your homeland, tell of', LIVE_ROW0, 0, label='scrolled line kept')
    print('  page scroll ok')


def test_inserts(sym):
    m = machine(sym)
    m.poke(0x0FF800, b'Rhys\xFC')
    m.poke(NAMES, (0x0FF800).to_bytes(4, 'big'))
    m.poke(NUMS, (1234).to_bytes(4, 'big'))
    m.poke(NUMS + 4, (0).to_bytes(4, 'big'))
    render(m, sym, "{NAME:00}'s party won.{BR}Earned {NUM:00} XP and {NUM:04}.", row0=LIVE_ROW0)
    check_line(m, b"Rhys's party won.", LIVE_ROW0, 0, label='name insert')
    check_line(m, b'Earned \x02\x03\x04\x05 XP and \x01.', LIVE_ROW0 + 2 * STRIDE, 1, label='number insert')
    assert m.peek(CTX + 1, 1)[0] & 0x10 == 0, 'insert flag cleared'
    print('  {NAME} and {NUM} inserts ok')


def test_long_names(sym):
    """$E0 nn in a record's four-letter name field draws entry nn of VWFName_Table: inline in
    the proportional renderer, and through the stock renderer's recursion (with the insert
    flag restored) when the fixed path draws it - in both cases inside a {NAME} insert."""
    m = machine(sym)
    m.poke(0x0FF800, bytes([0xE0, 1, 0xFC, 0, 0]))       # a record name field: entry 1
    m.poke(NAMES, (0x0FF800).to_bytes(4, 'big'))
    m.poke(0x0FF810, bytes([0xE0, 17, 0xFC, 0, 0]))      # entry 17
    m.poke(NAMES + 4, (0x0FF810).to_bytes(4, 'big'))
    render(m, sym, '{NAME:00} defended {NAME:04}.', row0=LIVE_ROW0)
    check_line(m, b'Searren defended Shiin.', LIVE_ROW0, 0, label='long names, proportional')
    assert m.peek(CTX + 1, 1)[0] & 0x10 == 0, 'insert flag cleared'
    other = 0xFFFF9C9E                                    # a fixed-width window row
    render(m, sym, '1.{NAME:00} LV', row0=other)
    mark, glyph = rows(m, other)
    assert glyph[:12] == [0x8000 | c for c in b'1.Searren LV'], [hex(w) for w in glyph[:12]]
    print('  long party names ok')


def test_clip(sym):
    m = machine(sym)
    text = 'W' * 40
    render(m, sym, text)
    x = check_line(m, text.encode(), TEMPLATE_ROW0, 0, label='clip')
    assert x <= 192, x
    print('  right-edge clipping ok (%d px)' % x)


def test_fixed_fallback(sym):
    m = machine(sym)
    other = 0xFFFF9C9E   # a name-list window row: must take the stock path
    render(m, sym, 'Rhys', row0=other)
    mark, glyph = rows(m, other)
    assert glyph[:4] == [0x8000 | c for c in b'Rhys'], glyph[:4]
    assert not m.vram_writes, 'stock path uploads nothing'
    print('  fixed-width fallback ok')


def test_opening_scroll(sym):
    """loc_F7F0 with the new-game script offset: a line goes to plane A at (row, col) with
    pool tiles $200 + 24*((row/4) mod 8), blanks are tile 0; the row-clearing string and
    other screens take the stock path."""
    m = Machine()
    so = sym['loc_304DA'] - sym['GameScript2']
    m.poke(0xFFFFD064, so.to_bytes(2, 'big'))
    text = b'Laia was born.'
    m.poke(TEXT, text + bytes([0xFC]))
    m.call(sym['loc_F7F0'], a0=TEXT, d1=2, d2=30, d3=0x6000)
    canvas, x = compose(text)
    cells = (x + 7) // 8
    slot = (30 // 4) & 7
    first = 0x200 + slot * CELLS
    row = 0xC000 + 30 * 128 + 2 * 2
    words = [int.from_bytes(m.vram[row + i * 2:row + i * 2 + 2], 'big') for i in range(CELLS)]
    assert words == [0x6000 | (first + i) for i in range(cells)] + [0] * (CELLS - cells), [hex(w) for w in words]
    assert bytes(m.vram[first * 32:first * 32 + CELLS * 32]) == expand_open(canvas), 'scroll tiles (transparent paper + shadow)'
    # the stock path for the blank row-clearing string and for another script offset
    m2 = Machine(); m2.poke(0xFFFFD064, so.to_bytes(2, 'big'))
    m2.call(sym['loc_F7F0'], a0=sym['loc_1B8C'], d1=0, d2=5, d3=0x6000)
    assert not any(w < 0xC000 for w in m2.vram_writes), 'no pool upload for the clearing string'
    print('  opening scroll ok (%d px, slot %d)' % (x, slot))


MENU_POOL, MENU_STRIDE, PLANE_A, MAP_ID = 0x240, 0x80, 0xFFFF2000, 0xFFFFD022


def menu_machine(sym, pad):
    m = Machine()
    m.poke(CTX + 0x42, (MENU_STRIDE).to_bytes(2, 'big'))
    m.poke(CTX + 0x44, pad.to_bytes(2, 'big'))
    m.poke(MAP_ID, (0x202).to_bytes(2, 'big'))
    return m


def menu_words(m, row, col, n):
    d = m.peek(PLANE_A + row * MENU_STRIDE + col * 2, n * 2)
    return [int.from_bytes(d[i:i + 2], 'big') for i in range(0, n * 2, 2)]


def check_menu_line(m, line_bytes, row, col, pad, attr=0x8000, label=''):
    """Mark row `row`, glyph row `row + 1`: pad cells of paper in the mark row (or the ink
    width if wider), pool tiles $240 + row*32 + (col-4) for the ink cells, paper after."""
    canvas, x = compose(line_bytes)
    cells = (x + 7) // 8
    n = max(cells, pad)
    first = MENU_POOL + row * 32 + (col - 4)
    assert menu_words(m, row, col, n) == [attr | 0x1F] * n, (label, 'mark row')
    want = [attr | (first + i) for i in range(cells)] + [attr | 0x1F] * (n - cells)
    assert menu_words(m, row + 1, col, n) == want, (label, 'glyph row', [hex(v) for v in menu_words(m, row + 1, col, n)], [hex(v) for v in want])
    assert bytes(m.vram[first * 32:first * 32 + cells * 32]) == expand(canvas)[:cells * 32], (label, 'pool tiles')
    return x


def test_menu_items(sym):
    """The item screen: names at (mark row 2, col 4), (2, 26) and (15, 4) with $44(a6) = 10,
    equipped names with the $C000 attribute; the cell after the last never leaks."""
    m = menu_machine(sym, 10)
    render(m, sym, 'Steel Swd', row0=PLANE_A + 2 * MENU_STRIDE + 4 * 2)
    check_menu_line(m, b'Steel Swd', 2, 4, 10, label='left column')
    render(m, sym, 'Grenade Launcher', row0=PLANE_A + 2 * MENU_STRIDE + 26 * 2, attr=0xC000)
    x = check_menu_line(m, b'Grenade Launcher', 2, 26, 10, attr=0xC000, label='right column, equipped')
    assert (x + 7) // 8 == 10, x
    assert menu_words(m, 3, 36, 1) == [0], 'nothing written past column 35'
    render(m, sym, 'Laia Pendant', row0=PLANE_A + 15 * MENU_STRIDE + 4 * 2)
    check_menu_line(m, b'Laia Pendant', 15, 4, 10, label='lower block')
    # redrawing the same cell reuses its tile: the first name's tiles are overwritten in place
    render(m, sym, 'Monomate', row0=PLANE_A + 2 * MENU_STRIDE + 4 * 2)
    check_menu_line(m, b'Monomate', 2, 4, 10, label='redraw')
    assert m.peek(CTX + 1, 1)[0] & 0x30 == 0
    print('  menu item names ok')


def test_menu_labels(sym):
    """A label block with {BR}{BR} (four rows per label, $44(a6) = 8) and a block whose
    third label falls past row 24 and is drawn by the stock renderer."""
    m = menu_machine(sym, 8)
    render(m, sym, 'Head{BR}{BR}R Hand{BR}{BR}L Hand', row0=PLANE_A + 0 * MENU_STRIDE + 5 * 2)
    check_menu_line(m, b'Head', 0, 5, 8, label='label 1')
    check_menu_line(m, b'R Hand', 4, 5, 8, label='label 2')
    check_menu_line(m, b'L Hand', 8, 5, 8, label='label 3')
    m = menu_machine(sym, 8)
    render(m, sym, 'Luck{BR}{BR}Skill{BR}{BR}Late', row0=PLANE_A + 18 * MENU_STRIDE + 5 * 2)
    check_menu_line(m, b'Luck', 18, 5, 8, label='label near the bottom')
    check_menu_line(m, b'Skill', 22, 5, 8, label='last pooled row')
    assert menu_words(m, 27, 5, 8) == [0x8000 | c for c in b'Late'] + [0x801F] * 4, 'hand-off: stock glyph tiles on row 27'
    assert menu_words(m, 26, 5, 8) == [0x801F] * 8, 'hand-off: stock mark row'
    print('  menu labels and the row-24 hand-off ok')


def test_menu_main_list(sym):
    """The main-menu list is rendered into a 10x12 staging buffer and copied to
    plane A later. Its five exact line addresses must use the pool tiles for
    screen rows 1/3/5/7/9, column 16, without pooling nearby staging text."""
    staging = 0xFFFF9A82
    m = menu_machine(sym, 8)
    m.poke(CTX + 0x42, (0x14).to_bytes(2, 'big'))
    labels = (b'Item', b'Technique', b'Stats', b'Equip')
    render(m, sym, ' Item{BR} Technique{BR} Stats{BR} Equip', row0=staging)
    for i, label in enumerate(labels):
        row0 = staging + 2 + i * 0x28
        canvas, x = compose(label)
        cells = (x + 7) // 8
        mark = [int.from_bytes(m.peek(row0 + j * 2, 2), 'big') for j in range(7)]
        glyph = [int.from_bytes(m.peek(row0 + 0x14 + j * 2, 2), 'big') for j in range(7)]
        first = MENU_POOL + (1 + i * 2) * 32 + 13
        assert m.peek(row0 - 2, 2) == b'\0\0', (label, 'fixed left margin')
        assert mark == [0x801F] * 7, (label, 'mark row')
        assert glyph == ([0x8000 | (first + j) for j in range(cells)] +
                         [0x801F] * (7 - cells)), (label, 'glyph row', glyph)
        assert bytes(m.vram[first * 32:first * 32 + cells * 32]) == expand(canvas)[:cells * 32], (label, 'pool tiles')

    m = menu_machine(sym, 8)
    m.poke(CTX + 0x42, (0x14).to_bytes(2, 'big'))
    render(m, sym, ' Switch', row0=0xFFFF9B22)
    first = MENU_POOL + 9 * 32 + 13
    canvas, x = compose(b'Switch')
    cells = (x + 7) // 8
    glyph = [int.from_bytes(m.peek(0xFFFF9B38 + j * 2, 2), 'big') for j in range(7)]
    assert glyph == [0x8000 | (first + j) for j in range(cells)] + [0x801F] * (7 - cells)
    assert bytes(m.vram[first * 32:first * 32 + cells * 32]) == expand(canvas)[:cells * 32]

    m = menu_machine(sym, 8)
    m.poke(CTX + 0x42, (0x14).to_bytes(2, 'big'))
    render(m, sym, 'Nearby', row0=0xFFFF9A86)
    assert not m.vram_writes, 'nearby staging address must stay fixed width'
    print('  main-menu staging list ok')


def test_menu_off(sym):
    """Outside a menu screen the plane A buffer takes the stock path (the battle box
    draws there); inside it, rows the pool does not cover do too."""
    m = menu_machine(sym, 8)
    m.poke(MAP_ID, (0x5A).to_bytes(2, 'big'))
    render(m, sym, 'Rhys', row0=PLANE_A + 2 * MENU_STRIDE + 4 * 2)
    assert menu_words(m, 3, 4, 4) == [0x8000 | c for c in b'Rhys'], 'field map: stock tiles'
    assert not m.vram_writes
    m = menu_machine(sym, 8)
    render(m, sym, 'Rhys', row0=PLANE_A + 24 * MENU_STRIDE + 16 * 2)   # the row-25 name plate
    assert menu_words(m, 25, 16, 4) == [0x8000 | c for c in b'Rhys'], 'name plate: stock tiles'
    render(m, sym, 'Rhys', row0=PLANE_A + 2 * MENU_STRIDE + 2 * 2)     # column 2: left of the pool
    assert menu_words(m, 3, 2, 4) == [0x8000 | c for c in b'Rhys'], 'column 2: stock tiles'
    assert not m.vram_writes
    print('  menu fallbacks ok')


# the shop list windows: first mark row, line stride, cells, pool base (VWFShop_Table)
SHOP_LISTS = ((0xFFFFA126, 0x48, 16, 0x240), (0xFFFF9D30, 0x38, 11, 0x290), (0xFFFF9E80, 0x38, 11, 0x2C7))
SHOP_ROW0, SHOP_STRIDE, SHOP_CELLS = SHOP_LISTS[0][:3]


def test_shop_list(sym):
    """A store screen ($222): the five lines of the buy list ($FFFFA126 + i*$48, 16 cells)
    and of the two sell-list pages ($FFFF9D30 / $FFFF9E80 + i*$38, 11 cells) each get
    their own pool line; other rows of the buffers, other windows and other screens
    take the stock path."""
    m = Machine()
    m.poke(MAP_ID, (0x222).to_bytes(2, 'big'))
    names = (b'Grenade Launcher', b'Knife', b'Laconian Sword', b'Monomate', b'Star Atomizer')
    for row0, stride, cells_w, pool in SHOP_LISTS:
        m.poke(CTX + 0x42, (stride // 2).to_bytes(2, 'big'))
        m.poke(CTX + 0x44, cells_w.to_bytes(2, 'big'))
        for i, name in enumerate(names):
            render(m, sym, name.decode(), row0=row0 + i * stride)
            canvas, x = compose(name)
            cells = (x + 7) // 8
            row = m.peek(row0 + i * stride, cells_w * 2)
            mark = [int.from_bytes(row[j:j + 2], 'big') for j in range(0, cells_w * 2, 2)]
            row = m.peek(row0 + i * stride + stride // 2, cells_w * 2)
            glyph = [int.from_bytes(row[j:j + 2], 'big') for j in range(0, cells_w * 2, 2)]
            first = pool + cells_w * i
            assert mark == [0x801F] * cells_w, (hex(row0), name, mark)
            assert glyph == [0x8000 | (first + c) for c in range(cells)] + [0x801F] * (cells_w - cells), (hex(row0), name, [hex(v) for v in glyph])
            assert bytes(m.vram[first * 32:first * 32 + cells * 32]) == expand(canvas)[:cells * 32], (hex(row0), name, 'tiles')
    assert (compose(b'Grenade Launcher')[1] + 7) // 8 <= 11, 'the widest name stays clear of the price at cell 11'
    m.poke(CTX + 0x42, (0x24).to_bytes(2, 'big'))
    m.poke(CTX + 0x44, (SHOP_CELLS).to_bytes(2, 'big'))
    # a row that is not a line start (the glyph row of line 0), a 24-cell window on the
    # same screen (the dialogue box, its own pool), and the same buffer on the field map
    m.vram_writes = []
    render(m, sym, 'Knife', row0=SHOP_ROW0 + 0x24)
    assert m.peek(SHOP_ROW0 + 0x48, 2) == bytes([0x80, ord('K')]), 'off-line row: stock tiles'
    assert not m.vram_writes
    m.poke(CTX + 0x42, (STRIDE).to_bytes(2, 'big'))
    m.poke(CTX + 0x44, (24).to_bytes(2, 'big'))
    render(m, sym, 'Welcome.', row0=LIVE_ROW0)
    check_line(m, b'Welcome.', LIVE_ROW0, 0, label='shop prompt in the dialogue box')
    m.poke(CTX + 0x42, (0x24).to_bytes(2, 'big'))
    m.poke(CTX + 0x44, (SHOP_CELLS).to_bytes(2, 'big'))
    m.poke(MAP_ID, (0x5A).to_bytes(2, 'big'))
    m.vram_writes = []
    render(m, sym, 'Knife', row0=SHOP_ROW0)
    assert m.peek(SHOP_ROW0 + 0x24, 2) == bytes([0x80, ord('K')]) and not m.vram_writes, 'field map: stock tiles'
    print('  shop list ok')


def test_battle_box(sym):
    """The battle screen ($232): an enemy-group line in the box buffer, the five character
    names of the stat window (five-cell pool lines, $44(a6) = 4), an item-list entry at a
    name's cell with $44(a6) = 9, and the message row still on the dialogue pool."""
    m = Machine()
    m.poke(MAP_ID, (0x232).to_bytes(2, 'big'))
    # the enemy group: "{NAME:00} {NUM:00}" into the box buffer, stride $44
    m.poke(0x0FF800, b'Chirper\xFC')
    m.poke(NAMES, (0x0FF800).to_bytes(4, 'big'))
    m.poke(NUMS, (2).to_bytes(4, 'big'))
    m.poke(CTX + 0x42, (0x44).to_bytes(2, 'big'))
    m.poke(CTX + 0x44, (12).to_bytes(2, 'big'))
    render(m, sym, '{NAME:00} {NUM:00}', row0=0xFFFF9D70)
    canvas, x = compose(b'Chirper \x03')
    cells = (x + 7) // 8
    glyph = [int.from_bytes(m.peek(0xFFFF9D70 + 0x44 + 2 * c, 2), 'big') for c in range(11)]
    assert glyph == [0x8000 | (0x580 + c) for c in range(cells)] + [0x801F] * (11 - cells), [hex(v) for v in glyph]
    assert bytes(m.vram[0x580 * 32:0x580 * 32 + cells * 32]) == expand(canvas)[:cells * 32]
    assert m.peek(0xFFFF9D70 + 0x44 + 22, 2) == b'\x00\x00', 'the twelfth cell stays untouched (capacity 11)'
    # character names: five cells apart in plane A row 20, $44(a6) = 4
    m.poke(CTX + 0x42, (0x80).to_bytes(2, 'big'))
    m.poke(CTX + 0x44, (4).to_bytes(2, 'big'))
    for i, name in enumerate((b'Rhys', b'Marina', b'Searren', b'Mieu', b'Lyle')):
        row0 = PLANE_A + 20 * 0x80 + (6 + 5 * i) * 2
        render(m, sym, name.decode(), row0=row0)
        canvas, x = compose(name)
        cells = (x + 7) // 8
        assert cells <= 5, (name, x)
        n = max(cells, 4)
        glyph = [int.from_bytes(m.peek(row0 + 0x80 + 2 * c, 2), 'big') for c in range(n)]
        first = 0x5AC + 5 * i
        assert glyph == [0x8000 | (first + c) for c in range(cells)] + [0x801F] * (n - cells), (name, [hex(v) for v in glyph])
        assert bytes(m.vram[first * 32:first * 32 + cells * 32]) == expand(canvas)[:cells * 32], name
    # an item-list entry at the second name's cell, told apart by $44(a6) = 9
    m.poke(CTX + 0x44, (9).to_bytes(2, 'big'))
    row0 = PLANE_A + 20 * 0x80 + 11 * 2
    render(m, sym, 'Star Atomizer', row0=row0)
    canvas, x = compose(b'Star Atomizer')
    cells = (x + 7) // 8
    n = max(cells, 9)               # the stock pads to $44(a6) = 9
    glyph = [int.from_bytes(m.peek(row0 + 0x80 + 2 * c, 2), 'big') for c in range(n)]
    assert glyph == [0x8000 | (0x25C + c) for c in range(cells)] + [0x801F] * (n - cells), [hex(v) for v in glyph]
    assert bytes(m.vram[0x25C * 32:0x25C * 32 + cells * 32]) == expand(canvas)[:cells * 32]
    # the message row keeps the dialogue pool
    m.poke(CTX + 0x42, (STRIDE).to_bytes(2, 'big'))
    m.poke(CTX + 0x44, (24).to_bytes(2, 'big'))
    render(m, sym, "You've been ambushed!", row0=0xFFFF2C0A)
    check_line(m, b"You've been ambushed!", 0xFFFF2C0A, 0, label='battle message')
    # off the battle screen the same rows are stock
    m.poke(MAP_ID, (0x5A).to_bytes(2, 'big'))
    m.poke(CTX + 0x42, (0x80).to_bytes(2, 'big'))
    m.poke(CTX + 0x44, (4).to_bytes(2, 'big'))
    m.vram_writes = []
    render(m, sym, 'Rhys', row0=PLANE_A + 20 * 0x80 + 6 * 2)
    assert m.peek(PLANE_A + 21 * 0x80 + 6 * 2, 2) == bytes([0x80, ord('R')]) and not m.vram_writes
    print('  battle box ok')


SMOOTH_POOL, SMOOTH_RATE_ADDR, GAME_ROUTINE = 0x580, 0xFFFFD11C, 0xFFFFD284


def smooth_view(canvases, k):
    """Reference: the 32-px interior at offset k over the 48-px stack of three lines
    (blank, line 0, blank, line 1, blank, line 2), as 96 tiles (ink 1, paper 2)."""
    out = bytearray()
    for block in range(4):
        rows = []
        for r in range(8):
            y = k + block * 8 + r
            if y & 8:
                rows.append(canvases[y >> 4][y & 7])
            else:
                rows.append(bytearray(26))
        out += expand(rows)
    return bytes(out)


def test_smooth_scroll(sym):
    """A page advance with smooth_scroll: loc_A368 composes the next page into a third
    canvas, then each frame shows the interior slid by the option's rate on pool tiles
    $580-$5DF, and at 16 px both lines are drawn the ordinary way."""
    def box_machine():
        m = machine(sym)
        m.poke(MAP_ID, (0x5A).to_bytes(2, 'big'))
        # the window geometry loc_FC58 copies with: 6 rows of $34 bytes, $4C to the next plane row
        m.poke(CTX + 0x30, (STRIDE).to_bytes(2, 'big')); m.poke(CTX + 0x46, (6).to_bytes(2, 'big'))
        m.poke(CTX + 0x7C, (0x80 - STRIDE).to_bytes(2, 'big')); m.poke(CTX + 0x3C, (0x100).to_bytes(2, 'big'))
        return m
    m = box_machine()
    render(m, sym, 'The legends of Landen,{BR}your homeland, tell of{PAGE}world-sweeping wars{PAGE}fought.', row0=LIVE_ROW0)
    cont = int.from_bytes(m.peek(CTX + 0x3E, 4), 'big')
    l0, l1, l2 = compose(b'The legends of Landen,')[0], compose(b'your homeland, tell of')[0], compose(b'world-sweeping wars')[0]
    m.poke(SMOOTH_RATE_ADDR, bytes([0x48]))          # speed 5: 1 px per frame
    m.poke(CTX + 0xC, bytes([7])); m.poke(CTX + 0xD, bytes([1]))
    m.a[6] = CTX
    # frame 1: the counter wraps, the page advance begins: offset 0 on the scroll pool
    m.vram_writes = []
    m.call(sym['loc_A368'])
    flags = m.peek(CTX + 1, 1)[0]
    assert flags & 0x20, 'the third page keeps the continuation flag set'
    assert int.from_bytes(m.peek(CTX + 0x3E, 4), 'big') != cont, 'continuation pointer moved to the third page'
    for r in range(4):
        words = [int.from_bytes(m.peek(LIVE_ROW0 + r * STRIDE + 2 * c, 2), 'big') for c in range(CELLS)]
        assert words == [0x8000 | (SMOOTH_POOL + r * CELLS + c) for c in range(CELLS)], ('interior row', r, [hex(w) for w in words[:4]])
    assert bytes(m.vram[SMOOTH_POOL * 32:SMOOTH_POOL * 32 + 96 * 32]) == smooth_view((l0, l1, l2), 0), 'view at 0 px'
    # frames 2..: one px per frame; check the view half way
    for k in range(1, 8):
        m.call(sym['loc_A368'])
    assert bytes(m.vram[SMOOTH_POOL * 32:SMOOTH_POOL * 32 + 96 * 32]) == smooth_view((l0, l1, l2), 7), 'view at 7 px'
    assert m.peek(CTX + 0xC, 1)[0] == 0, 'the page counter is frozen while scrolling'
    for k in range(8, 16):
        m.call(sym['loc_A368'])
    assert bytes(m.vram[SMOOTH_POOL * 32:SMOOTH_POOL * 32 + 96 * 32]) == smooth_view((l0, l1, l2), 15), 'view at 15 px'
    # the 16th px finishes: lines 0 and 1 are the old line 1 and the new page, on the dialogue pool
    m.call(sym['loc_A368'])
    check_line(m, b'your homeland, tell of', LIVE_ROW0, 0, label='scrolled line 0')
    check_line(m, b'world-sweeping wars', LIVE_ROW1, 1, label='scrolled line 1')
    # idle: the next frames count as the stock does (the counter moves again)
    m.call(sym['loc_A368'])
    assert m.peek(CTX + 0xC, 1)[0] == 1, 'the page counter runs again'
    # a button press pays out two lines ($D = 2 after `move.w #2, $C(a6)`): the second
    # starts the frame the first finishes, not eight frames later as the stock counter
    # would have it
    m3 = box_machine()
    render(m3, sym, 'aa{BR}bb{PAGE}cc{PAGE}dd{PAGE}ee', row0=LIVE_ROW0)
    ca, cb, cc, cd = (compose(t)[0] for t in (b'aa', b'bb', b'cc', b'dd'))
    m3.poke(SMOOTH_RATE_ADDR, bytes([0x48])); m3.poke(CTX + 0xC, bytes([7])); m3.poke(CTX + 0xD, bytes([2]))
    m3.a[6] = CTX
    for k in range(16):
        m3.call(sym['loc_A368'])
    assert m3.peek(CTX + 0xD, 1)[0] == 1
    assert bytes(m3.vram[SMOOTH_POOL * 32:SMOOTH_POOL * 32 + 96 * 32]) == smooth_view((ca, cb, cc), 15), 'first line at 15 px'
    m3.call(sym['loc_A368'])            # 16 px: finishes, and the second line begins at once
    assert m3.peek(CTX + 0xD, 1)[0] == 0, 'the second line was taken'
    assert bytes(m3.vram[SMOOTH_POOL * 32:SMOOTH_POOL * 32 + 96 * 32]) == smooth_view((cb, cc, cd), 0), 'second line at 0 px'
    for r in range(4):
        words = [int.from_bytes(m3.peek(LIVE_ROW0 + r * STRIDE + 2 * c, 2), 'big') for c in range(CELLS)]
        assert words == [0x8000 | (SMOOTH_POOL + r * CELLS + c) for c in range(CELLS)], ('chained interior row', r)
    assert m3.peek(CTX + 0xC, 1)[0] == 0, 'the page counter did not move'
    m3.call(sym['loc_A368'])
    assert bytes(m3.vram[SMOOTH_POOL * 32:SMOOTH_POOL * 32 + 96 * 32]) == smooth_view((cb, cc, cd), 1), 'second line at 1 px: no gap'
    for k in range(15):
        m3.call(sym['loc_A368'])
    check_line(m3, b'cc', LIVE_ROW0, 0, label='chained line 0')
    check_line(m3, b'dd', LIVE_ROW1, 1, label='chained line 1')
    assert m3.peek(CTX + 0xD, 1)[0] == 0 and m3.peek(CTX + 1, 1)[0] & 0x20, 'a third line waits for the button'
    for k in range(8):
        m3.call(sym['loc_A368'])
    assert m3.peek(CTX + 0xD, 1)[0] == 0xFF and int.from_bytes(m3.peek(GAME_ROUTINE, 2), 'big') == 8, 'then the wait state'
    # the fastest speed takes four frames, the slowest sixty-four
    for value, frames in ((0x08, 4), (0x88, 64)):
        m2 = box_machine()
        render(m2, sym, 'a{PAGE}b{PAGE}c', row0=LIVE_ROW0)
        m2.poke(SMOOTH_RATE_ADDR, bytes([value])); m2.poke(CTX + 0xC, bytes([7])); m2.poke(CTX + 0xD, bytes([1]))
        m2.a[6] = CTX
        n = 0
        while True:
            m2.call(sym['loc_A368']); n += 1
            if int.from_bytes(m2.peek(LIVE_ROW1 + STRIDE, 2), 'big') == 0x8000 | (POOL + CELLS):
                break
            assert n < 200
        assert n == frames + 1, (hex(value), n)
    print('  smooth page scroll ok')


def main():
    sym = Symbols()
    for t in (test_plain, test_br_and_page, test_scroll, test_inserts, test_long_names, test_clip, test_fixed_fallback, test_opening_scroll,
              test_menu_items, test_menu_labels, test_menu_main_list, test_menu_off,
              test_shop_list, test_battle_box, test_smooth_scroll):
        t(sym)
    print('test_vwf: all passed')


if __name__ == '__main__':
    main()
