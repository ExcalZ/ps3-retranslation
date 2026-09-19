"""Phantasy Star III text codec: the US (ASCII-tile) and JP (kana-tile) charsets, the
control codes of the game's text renderer, and decode/encode between ROM bytes and a
readable markup.

The renderer (`loc_10038` in the disassembly) treats every byte below $E0 as a tile
index in the 8x8 text font loaded at VRAM $0000, and everything from $E0 up as a control:

    $E4 nn   insert the number stored at $FFFFD4A0+nn (or a name, if the
             long there is a pointer)                                      -> {NUM:nn}
    $E8 nn   insert the string whose pointer sits at char_name_saved+nn   -> {NAME:nn}
    $EC      wait for a button, clear the box, continue                    -> {PAGE}
    $F0 nn   draw tile nn with a handakuten mark in the row above (JP)     -> precomposed kana
    $F4 nn   draw tile nn with a dakuten mark in the row above (JP)        -> precomposed kana
    $F8      new line                                                      -> {BR}
    $FC      end of string

US text is ASCII (tile index == ASCII code for $20-$7E). The two tiles $BE,$BF together
draw the "III" of "Alisa III" and are written {III}. The JP font is kana only.
"""
import unicodedata

CTRL = {0xE4: 'NUM', 0xE8: 'NAME'}
CTRL_REV = {v: k for k, v in CTRL.items()}

# ---------------------------------------------------------------- JP charset
_JP_ROWS = {
    0x01: '0123456789©SEGA',
    0x10: 'ー「」。、？！※♪',          # $19-$1E are the dakuten mark tiles / misc, $1F space
    0x20: 'HLMPTV',
    0x30: 'あいうえおかきくけこさしすせそた',
    0x40: 'ちつてとなにぬねのはひふへほまみ',
    0x50: 'むめもやゆよらりるれろわをんぁぃ',
    0x60: 'ぅぇぉゃゅょっアイウエオカキクケ',
    0x70: 'コサシスセソタチツテトナニヌネノ',
    0x80: 'ハヒフヘホマミムメモヤユヨラリル',
    0x90: 'レロワヲンァィゥェォャュョッ',
    0xA0: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
}
JP_DECODE = {0x1F: ' ', 0x1E: '／', 0x1D: '゜', 0x00: '　'}
for base, s in _JP_ROWS.items():
    for i, ch in enumerate(s):
        JP_DECODE[base + i] = ch
JP_ENCODE = {v: k for k, v in JP_DECODE.items()}
JP_ENCODE[' '] = 0x1F

# ---------------------------------------------------------------- US charset
US_DECODE = {b: chr(b) for b in range(0x20, 0x7F)}
US_DECODE.update({0x01 + i: str(i) for i in range(10)})   # the JP-layout digits survive in the US font
US_DECODE.update({0x10: '-', 0x13: '.', 0x14: ',', 0x1F: ' '})
# the bold capitals at $A0-$B9 (credits) are written as fullwidth letters so they stay
# distinct from the ASCII face
US_DECODE.update({0xA0 + i: chr(0xFF21 + i) for i in range(26)})
US_ENCODE = {chr(b): b for b in range(0x20, 0x7F)}
US_ENCODE.update({chr(0xFF21 + i): 0xA0 + i for i in range(26)})
# the staff-roll part of the credits is assembled under a `charset` directive that maps
# space, '-', '.', ',' and the digits to the JP-layout tiles; encode with charset='credits'
# there so the bytes match what the assembler produced for the original source
CREDITS_ENCODE = dict(US_ENCODE)
CREDITS_ENCODE.update({' ': 0x1F, '-': 0x10, '.': 0x13, ',': 0x14})
CREDITS_ENCODE.update({str(i): 0x01 + i for i in range(10)})
CREDITS_ENCODE.update({chr(0x41 + i): 0xA0 + i for i in range(26)})
CREDITS_ENCODE[' '] = 0x20     # the two literal $20 spaces the original source has there
CREDITS_DECODE = dict(US_DECODE)
CREDITS_DECODE[0x20] = ' '


def decode(data, charset='us'):
    """ROM bytes (without the trailing $FC) -> markup string."""
    dec = {'us': US_DECODE, 'jp': JP_DECODE, 'credits': CREDITS_DECODE}[charset]
    out = []
    i = 0
    n = len(data)
    while i < n:
        b = data[i]
        if b == 0xFC:
            out.append('{END}'); i += 1; continue
        if b == 0xF8:
            out.append('{BR}'); i += 1; continue
        if b == 0xEC:
            out.append('{PAGE}'); i += 1; continue
        if b in CTRL:
            out.append('{%s:%02X}' % (CTRL[b], data[i + 1])); i += 2; continue
        if b in (0xF4, 0xF0):
            k = data[i + 1]
            base = dec.get(k, '{%02X}' % k)
            mark = '゙' if b == 0xF4 else '゚'
            out.append(unicodedata.normalize('NFC', base + mark)); i += 2; continue
        if b == 0xBE and i + 1 < n and data[i + 1] == 0xBF:
            out.append('{III}'); i += 2; continue
        if b in dec:
            out.append(dec[b])
        else:
            out.append('{%02X}' % b)
        i += 1
    return ''.join(out)


def encode(text, charset='us'):
    """markup string -> ROM bytes, without the trailing $FC."""
    enc = {'us': US_ENCODE, 'jp': JP_ENCODE, 'credits': CREDITS_ENCODE}[charset]
    out = bytearray()
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == '{':
            j = text.index('}', i)
            tok = text[i + 1:j]
            i = j + 1
            if tok == 'BR':
                out.append(0xF8)
            elif tok == 'END':
                out.append(0xFC)
            elif tok == 'PAGE':
                out.append(0xEC)
            elif tok == 'III':
                out += b'\xBE\xBF'
            elif ':' in tok:
                name, arg = tok.split(':')
                out.append(CTRL_REV[name]); out.append(int(arg, 16))
            else:
                out.append(int(tok, 16))
            continue
        if ch in enc:
            out.append(enc[ch])
        elif charset == 'jp':
            d = unicodedata.normalize('NFD', ch)
            if len(d) == 2 and d[1] in ('゙', '゚') and d[0] in enc:
                out.append(0xF4 if d[1] == '゙' else 0xF0); out.append(enc[d[0]])
            else:
                raise ValueError('cannot encode %r' % ch)
        else:
            raise ValueError('cannot encode %r' % ch)
        i += 1
    return bytes(out)


if __name__ == '__main__':
    import sys
    rom = open(sys.argv[1], 'rb').read()
    off = int(sys.argv[2], 0)
    cs = sys.argv[3] if len(sys.argv) > 3 else 'us'
    end = rom.index(b'\xFC', off)
    print(decode(rom[off:end], cs))
