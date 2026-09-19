"""Render a block of uncompressed 4bpp 8x8 tiles from a ROM as a labelled, high-contrast PNG sheet.

    python tools/fontsheet.py rom.bin 0x66000 256 out.png [cols] [scale]

The PS3 text font uses colour 1 for ink and colour 2 for paper; other colours are drawn grey.
Row/column labels (hex) are drawn in the margins so a tile index can be read off the sheet.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'md'))
import png

PAL = {0: 140, 1: 0, 2: 255, 3: 200}
# tiny 3x5 hex digit font for the margin labels
_DIG = {
 '0':"111101101101111",'1':"010110010010111",'2':"111001111100111",'3':"111001111001111",
 '4':"101101111001001",'5':"111100111001111",'6':"111100111101111",'7':"111001001001001",
 '8':"111101111101111",'9':"111101111001111",'A':"010101111101101",'B':"110101110101110",
 'C':"111100100100111",'D':"110101101101110",'E':"111100110100111",'F':"111100110100100"}

def decode_tile(blk):
    g = []
    for y in range(8):
        row = []
        for x in range(4):
            b = blk[y*4+x]; row.append(b >> 4); row.append(b & 15)
        g.append(row)
    return g

def render(data, ntiles, cols, path, scale=5, base=0):
    gap = 1; cell = 8+gap
    rows = (ntiles+cols-1)//cols
    mx = 3*4  # left margin in unscaled px
    my = 6
    W = (mx+cols*cell+gap)*scale; H = (my+rows*cell+gap)*scale
    img = [bytearray([90])*W for _ in range(H)]
    def put(x, y, v):
        for dy in range(scale):
            row = img[y*scale+dy]
            for dx in range(scale): row[x*scale+dx] = v
    def text(x, y, s):
        for ch in s:
            bits = _DIG[ch]
            for i, b in enumerate(bits):
                if b == '1': put(x+i%3, y+i//3, 255)
            x += 4
    for c in range(cols):
        text(mx+c*cell+gap, 0, '%X' % ((base+c) & 15))
    for r in range(rows):
        text(0, my+r*cell+gap+1, '%02X' % ((base+r*cols) >> 4 & 0xFF))
    for i in range(ntiles):
        t = decode_tile(data[i*32:(i+1)*32])
        ox = mx+gap+(i%cols)*cell; oy = my+gap+(i//cols)*cell
        for y in range(8):
            for x in range(8):
                put(ox+x, oy+y, PAL.get(t[y][x], 200))
    png.write_gray(path, img, W, H)
    print('wrote', path)

if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read()
    off = int(sys.argv[2], 0); n = int(sys.argv[3], 0); out = sys.argv[4]
    cols = int(sys.argv[5]) if len(sys.argv) > 5 else 16
    scale = int(sys.argv[6]) if len(sys.argv) > 6 else 5
    render(rom[off:off+n*32], n, cols, out, scale)
