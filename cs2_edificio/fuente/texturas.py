"""Genera el atlas de texturas (BaseColor, Normal, MaskMap) del edificio.
Uso: python texturas.py <carpeta_salida> <nombre_malla>
Atlas 2048x2048, rejilla 4x4 de celdas de 512 px. Cada celda de fachada = 3 m x 3 m."""
import sys, numpy as np
from PIL import Image, ImageFilter

S, C = 2048, 512
rng = np.random.default_rng(7)
col = np.zeros((S, S, 3), np.float32); hgt = np.zeros((S, S), np.float32)
met = np.zeros((S, S), np.float32); smo = np.full((S, S), .25, np.float32); ao = np.ones((S, S), np.float32)

def noise(scale, amp=1.0):
    n = rng.random((C // scale + 2, C // scale + 2)).astype(np.float32)
    im = Image.fromarray((n * 255).astype(np.uint8)).resize((C, C), Image.BICUBIC)
    return (np.asarray(im, np.float32) / 255 - .5) * amp

def hexc(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)

class Cell:
    def __init__(s, c, r):
        s.y, s.x = r * C, c * C
        s.col, s.h = col[s.y:s.y+C, s.x:s.x+C], hgt[s.y:s.y+C, s.x:s.x+C]
        s.m, s.s, s.ao = met[s.y:s.y+C, s.x:s.x+C], smo[s.y:s.y+C, s.x:s.x+C], ao[s.y:s.y+C, s.x:s.x+C]
    def fill(s, h, var=.04, sc=8, sm=.25):
        s.col[:] = hexc(h) * (1 + noise(sc, var * 2)[..., None] + noise(2, var)[..., None]); s.s[:] = sm
    def rect(s, x0, y0, x1, y1, h, height=0, var=.02, m=0, sm=None):
        x0, y0, x1, y1 = map(int, (x0, y0, x1, y1))
        s.col[y0:y1, x0:x1] = hexc(h) * (1 + noise(4, var)[y0:y1, x0:x1, None])
        s.h[y0:y1, x0:x1] = height; s.m[y0:y1, x0:x1] = m
        if sm is not None: s.s[y0:y1, x0:x1] = sm
    def glass(s, x0, y0, x1, y1):
        x0, y0, x1, y1 = map(int, (x0, y0, x1, y1)); yy = np.linspace(0, 1, y1 - y0)[:, None, None]
        g = hexc('#3d5466') * (1 - yy) + hexc('#7f98a8') * yy
        xx = np.arange(x1 - x0)[None, :, None]; refl = ((xx + (np.arange(y1 - y0)[:, None, None] * .6)) % 160 < 30) * .10
        s.col[y0:y1, x0:x1] = g + refl; s.h[y0:y1, x0:x1] = -.6; s.s[y0:y1, x0:x1] = .92; s.ao[y0:y1, x0:x1] = .8
    def shutters(s, x0, y0, x1, y1):
        s.rect(x0, y0, x1, y1, '#3f6b4a', .15, sm=.35)
        for y in range(int(y0) + 6, int(y1) - 4, 9): s.col[y:y+3, int(x0)+3:int(x1)-3] *= .72; s.h[y:y+3, int(x0):int(x1)] = .05

px = C / 3.0  # px por metro
PLASTER, STONE = '#e6d3b3', '#b8ab97'

# (0,0) ventana
w = Cell(0, 0); w.fill(PLASTER)
wx0, wx1, wy0, wy1 = C/2 - .6*px, C/2 + .6*px, .6*px, 2.1*px
w.shutters(wx0 - .62*px, wy0, wx0 - .04*px, wy1); w.shutters(wx1 + .04*px, wy0, wx1 + .62*px, wy1)
w.rect(wx0 - 8, wy0 - 8, wx1 + 8, wy1, '#f2efe8', -.1, sm=.4); w.glass(wx0 + 12, wy0 + 12, wx1 - 12, wy1 - 6)
w.rect(C/2 - 5, wy0 + 12, C/2 + 5, wy1 - 6, '#f2efe8', -.3)
w.rect(wx0 - 18, wy1, wx1 + 18, wy1 + 12, '#d9d4c9', .25)
# (1,0) puerta balcón
b = Cell(1, 0); b.fill(PLASTER)
bx0, bx1, by0 = C/2 - .55*px, C/2 + .55*px, .7*px
b.shutters(bx0 - .58*px, by0, bx0 - .04*px, C); b.shutters(bx1 + .04*px, by0, bx1 + .58*px, C)
b.rect(bx0 - 8, by0 - 8, bx1 + 8, C, '#f2efe8', -.1, sm=.4); b.glass(bx0 + 12, by0 + 12, bx1 - 12, C - 4)
b.rect(C/2 - 5, by0 + 12, C/2 + 5, C, '#f2efe8', -.3); b.rect(bx0 + 12, C*.62, bx1 - 12, C*.62 + 8, '#f2efe8', -.3)
# (2,0) local comercial (planta baja 3,5 m)
sh = Cell(2, 0); sh.fill(STONE, .05, 6)
vy = C / 3.5
sh.rect(.25*px, .25*vy, C - .25*px, .85*vy, '#2f4a3a', .1, sm=.5); sh.rect(.25*px, .55*vy, C - .25*px, .62*vy, '#d9b65a', .12, m=.8, sm=.6)
sh.rect(.3*px, .95*vy, C - .3*px, 3.05*vy, '#2b2b2b', -.05, m=.7, sm=.5); sh.glass(.3*px + 10, .95*vy + 10, C - .3*px - 10, 3.05*vy - 10)
sh.rect(C*.62, .95*vy + 10, C*.62 + 8, 3.05*vy - 10, '#2b2b2b', -.3, m=.7)
sh.rect(.3*px - 6, 3.05*vy, C - .3*px + 6, 3.05*vy + 10, '#d9d4c9', .2)
# (3,0) portal de entrada
d = Cell(3, 0); d.fill(STONE, .05, 6)
dx0, dx1, dy0 = C/2 - .8*px, C/2 + .8*px, .9*vy
d.rect(dx0 - 22, dy0 - 22, dx1 + 22, C, '#cfc6b6', .2); d.rect(dx0, dy0, dx1, C, '#5b3a22', -.4, var=.06, sm=.4)
d.glass(dx0 + 10, dy0 + 10, dx1 - 10, dy0 + .45*vy)
for x in (dx0 + 18, C/2 + 10):
    for y0 in (dy0 + .55*vy, dy0 + 1.5*vy):
        d.rect(x, y0, x + .62*px, y0 + .8*vy, '#6b4529', -.3)
d.rect(C/2 - 3, dy0 + .45*vy, C/2 + 3, C, '#3a2414', -.5); d.rect(C/2 - 30, dy0 + 1.4*vy, C/2 - 18, dy0 + 1.47*vy, '#c9a24a', -.2, m=1, sm=.7)
# (0,1) enlucido liso, (1,1) piedra, (2,1) grava cubierta, (3,1) remate
Cell(0, 1).fill(PLASTER)
st = Cell(1, 1); st.fill(STONE, .05, 6)
for i, y in enumerate(range(0, C, 64)):
    st.h[y:y+4] = -.3; st.col[y:y+4] *= .8
    for x in range((i % 2) * 64, C, 128): st.h[y:y+64, x:x+4] = -.3; st.col[y:y+64, x:x+4] *= .8
rf = Cell(2, 1); rf.fill('#8a8781', .25, 1, sm=.1); rf.h[:] = noise(1, .6)
tr = Cell(3, 1); tr.fill('#dedad1', .03, 16, sm=.3)
for y in (C//3, 2*C//3): tr.h[y:y+6] = -.4; tr.col[y:y+6] *= .85
# (0,2) barandilla, (1,2) metal, (2,2) hormigón losa
r = Cell(0, 2); r.fill('#9fb1ba', .02, 16, sm=.85); r.s[:] = .85
r.rect(0, 0, C, 40, '#2e3236', .3, m=.9, sm=.55); r.rect(0, C - 30, C, C, '#2e3236', .3, m=.9, sm=.55)
for x in range(0, C, 128): r.rect(x, 0, x + 14, C, '#2e3236', .3, m=.9, sm=.55)
mt = Cell(1, 2); mt.fill('#a3a7aa', .03, 1, sm=.5); mt.m[:] = .85
for y in range(0, C, 32): mt.h[y:y+3] = -.3; mt.col[y:y+3] *= .8
Cell(2, 2).fill('#c4c0b8', .05, 4, sm=.2)
# celdas libres
for c, rr in [(3, 2)] + [(i, 3) for i in range(4)]: Cell(c, rr).fill('#808080', 0)

out, name = sys.argv[1], sys.argv[2]
hb = np.asarray(Image.fromarray(((hgt + 1) * 127).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5)), np.float32) / 127
gy, gx = np.gradient(hb); k = 6.0
nrm = np.dstack([-gx * k, gy * k, np.ones_like(gx)]); nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
aob = ao
save = lambda a, f: Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8)).save(f"{out}/{name}_{f}.png")
save(col, 'BaseColor'); save(nrm * .5 + .5, 'Normal')
save(np.dstack([met, aob, np.zeros_like(met), smo]), 'MaskMap')
print('texturas listas')
