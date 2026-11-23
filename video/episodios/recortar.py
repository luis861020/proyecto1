#!/usr/bin/env python3
"""Recorta el fondo claro y uniforme de las poses generadas y deja PNG con transparencia.

Uso: python3 recortar.py <entrada.png> <salida.png> [tolerancia]
Rellena desde los bordes solo el fondo conectado, así no borra la camiseta blanca ni papeles.
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

src, dst = sys.argv[1], sys.argv[2]; tol = float(sys.argv[3]) if len(sys.argv) > 3 else 24
im = Image.open(src).convert("RGB"); a = np.asarray(im).astype(np.int16); h, w, _ = a.shape
border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]]); bgc = np.median(border, 0)
# también tolera la variación suave del fondo (degradado/sombra)
dist = np.abs(a - bgc).max(2)
lum = a.mean(2); bglike = (dist < tol) | ((lum > bgc.mean() - 10) & (a.max(2) - a.min(2) < 26) & (dist < tol * 1.6))
m = Image.fromarray(np.where(bglike, 255, 0).astype(np.uint8)).copy()  # copia editable
for x in range(0, w, 6):
    for y in (0, h - 1):
        if m.getpixel((x, y)) == 255: ImageDraw.floodfill(m, (x, y), 128)
for y in range(0, h, 6):
    for x in (0, w - 1):
        if m.getpixel((x, y)) == 255: ImageDraw.floodfill(m, (x, y), 128)
fg = np.asarray(m) != 128
alpha = Image.fromarray((fg * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.3))
# oscurece un poco el borde para que no quede halo claro sobre la oficina oscura
al = np.asarray(alpha).astype(np.float32) / 255; edge = (al > 0.02) & (al < 0.98)
out = a.astype(np.float32); out[edge] *= 0.82
res = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert("RGBA"); res.putalpha(alpha)
res = res.crop(res.getchannel("A").getbbox()); res.save(dst)
print(dst, res.size, f"fondo={bgc.astype(int).tolist()}")
