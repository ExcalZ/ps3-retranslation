"""Tile several screenshots into one PNG, downscaled, for quick review.

    python tools/montage.py out.png [--scale 2] [--cols 2] a.png b.png ...
"""
import os, struct, sys, zlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'md'))
import pngread


def write_rgb(path, rows, w, h):
    raw = b''.join(b'\x00' + bytes(v for px in r for v in px) for r in rows)
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xFFFFFFFF)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                           + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def montage(paths, out, scale=2, cols=2, gap=4):
    imgs = [pngread.read(p) for p in paths]
    w, h = imgs[0][0] // scale, imgs[0][1] // scale
    rows_n = (len(imgs) + cols - 1) // cols
    W = cols * w + (cols - 1) * gap; H = rows_n * h + (rows_n - 1) * gap
    canvas = [[(40, 40, 40)] * W for _ in range(H)]
    for i, (iw, ih, px) in enumerate(imgs):
        ox = (i % cols) * (w + gap); oy = (i // cols) * (h + gap)
        for y in range(h):
            row = px[y * scale]
            crow = canvas[oy + y]
            for x in range(w):
                crow[ox + x] = row[x * scale]
    write_rgb(out, canvas, W, H)
    return out


if __name__ == '__main__':
    args = sys.argv[1:]
    out = args.pop(0)
    scale = 2; cols = 2
    while args and args[0].startswith('--'):
        k = args.pop(0)
        if k == '--scale': scale = int(args.pop(0))
        elif k == '--cols': cols = int(args.pop(0))
    print(montage(args, out, scale, cols))
