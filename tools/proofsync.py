"""Render tools/proofread.html from proofread_template.html with the current dialogue face,
its widths and the stock 8x8 font embedded, so the page works from file:// with no fetch.

    python tools/proofsync.py
"""
import base64, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
V = os.path.join(ROOT, 'PSIII_Disasm', 'vwf')
font = open(os.path.join(V, 'diafont.bin'), 'rb').read()
width = open(os.path.join(V, 'diawidth.bin'), 'rb').read()
rom = open(os.path.join(ROOT, 'PSIII_Disasm', 'ps3original.bin'), 'rb').read()
stock = rom[0x66000:0x66000 + 0x100 * 32]
embed = 'const FONT_B64="%s";\nconst WIDTH_B64="%s";\nconst STOCK_B64="%s";' % tuple(
    base64.b64encode(x).decode() for x in (font, width, stock))
tpl = open(os.path.join(HERE, 'proofread_template.html'), encoding='utf-8').read()
out = tpl.replace('/*EMBED*/', embed)
open(os.path.join(HERE, 'proofread.html'), 'w', encoding='utf-8').write(out)
print('wrote tools/proofread.html (%d bytes)' % len(out))
