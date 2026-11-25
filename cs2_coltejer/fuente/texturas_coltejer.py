"""Atlas de texturas del Edificio Coltejer (4096 x 4096): BaseColor, Normal, MaskMap, Emissive.
Uso: python texturas_coltejer.py <carpeta_salida> <nombre_malla>
Disposición (también la usa modelo_coltejer.py):
  y 0-1023     8 franjas de vidrio de las fachadas frontal/trasera (32 m, 20 vanos), 128 px cada una
  y 1024-2047  8 franjas de vidrio de las fachadas laterales (37 m, 23 vanos)
  y 2048-3071  aletas | antepechos, aguja, cubierta, pavimento
  y 3072-4095  local comercial, ventana del podio, granito, metal / césped / luz roja"""
import sys, numpy as np
from PIL import Image, ImageFilter

S = 4096
rng = np.random.default_rng(1972)
col = np.zeros((S, S, 3), np.float32); hgt = np.zeros((S, S), np.float32); emi = np.zeros((S, S, 3), np.float32)
met = np.zeros((S, S), np.float32); smo = np.full((S, S), .2, np.float32); ao = np.ones((S, S), np.float32)
hexc = lambda h: np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)

def noise(h, w, sx, sy=None, amp=1.0):
    sy = sy or sx
    n = rng.random((max(2, h // sy), max(2, w // sx))).astype(np.float32)
    im = Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return (np.asarray(im, np.float32) / 255 - .5) * amp

def region(x, y, w, h): return (slice(y, y + h), slice(x, x + w))

def surface(x, y, w, h, c, var=.05, sx=8, sy=None, sm=.2, m=0.0, fine=.04):
    r = region(x, y, w, h)
    col[r] = hexc(c) * (1 + noise(h, w, sx, sy, var * 2)[..., None] + noise(h, w, 2, 2, fine)[..., None])
    smo[r] = sm; met[r] = m

def glass_strip(y0, w_m, bays, variant):
    """Una planta de vidrio: vanos con montantes, persianas, interiores y luces nocturnas."""
    H, W = 128, S; bw = W / bays
    yy = np.linspace(0, 1, H)[:, None, None]
    sky = hexc('#2c3a44') * (1 - yy) + hexc('#5d7482') * yy
    r = region(0, y0, W, H)
    col[r] = sky; smo[r] = .93; hgt[r] = -.4; ao[r] = .85
    # reflejo diagonal continuo de la fachada
    xx = np.arange(W)[None, :]; ys = np.arange(H)[:, None]
    band = (((xx * .35 + ys * 1.2 + variant * 300) % 900) < 140).astype(np.float32)
    col[r] += band[..., None] * .07
    lit_p = [.25, .55, .4, .7, .15, .5, .35, .6][variant]
    for b in range(bays):
        x0, x1 = int(b * bw), int((b + 1) * bw)
        k = rng.random()
        if k < .3:   # persiana bajada a distinta altura
            hb = int(H * rng.uniform(.25, .85))
            col[y0:y0 + hb, x0:x1] = hexc('#b9b2a2') * (1 + noise(hb, x1 - x0, 1, 3, .1)[..., None])
            for yl in range(y0 + 3, y0 + hb, 5): col[yl, x0:x1] *= .85
            smo[y0:y0 + hb, x0:x1] = .3
        elif k < .55:  # cortina clara
            col[y0:y0 + H, x0:x1] = col[y0:y0 + H, x0:x1] * .5 + hexc('#d8d2c0') * .35
        if rng.random() < lit_p:
            warm = hexc('#ffd59a') if rng.random() < .7 else hexc('#dfeaff')
            inten = rng.uniform(.45, 1)
            emi[y0 + 8:y0 + H - 4, x0 + 3:x1 - 3] = warm * inten
            col[y0 + 8:y0 + H - 4, x0 + 3:x1 - 3] = col[y0 + 8:y0 + H - 4, x0 + 3:x1 - 3] * .6 + warm * .25
        # montantes de aluminio y travesaño
        col[y0:y0 + H, x0:x0 + 4] = hexc('#3a3d40'); col[y0:y0 + H, x1 - 4:x1] = hexc('#3a3d40')
        hgt[y0:y0 + H, x0:x0 + 4] = 0; hgt[y0:y0 + H, x1 - 4:x1] = 0
        met[y0:y0 + H, x0:x0 + 4] = .9; met[y0:y0 + H, x1 - 4:x1] = .9
        col[y0 + 26:y0 + 31, x0:x1] = hexc('#3a3d40'); hgt[y0 + 26:y0 + 31, x0:x1] = 0
    col[y0:y0 + 6, :] = hexc('#2b2d30'); col[y0 + H - 5:y0 + H, :] = hexc('#2b2d30')
    emi[y0:y0 + H] *= (col[y0:y0 + H].mean(axis=2, keepdims=True) > 0) * 1.0

for v in range(8): glass_strip(v * 128, 32, 20, v)          # fachadas frontal y trasera
for v in range(8): glass_strip(1024 + v * 128, 37, 23, v)   # fachadas laterales

C = 1024
CONC = '#c9c4ba'
# aletas: concreto con marcas verticales del encofrado
surface(0, 2048, 512, C, CONC, .05, 2, 64, sm=.15)
for x in range(0, 512, 37): col[2048:3072, x:x + 2] *= .9; hgt[2048:3072, x:x + 2] = -.2
# antepechos: concreto con juntas horizontales
surface(512, 2048, 512, C, '#cfcabf', .05, 64, 2, sm=.15)
for y in range(2048, 3072, 128): col[y:y + 4, 512:1024] *= .82; hgt[y:y + 4, 512:1024] = -.4
# aguja: paneles de concreto prefabricado
surface(1024, 2048, C, C, '#d3cec4', .04, 16, sm=.18)
for k in range(0, C, 64):
    col[2048 + k:2048 + k + 3, 1024:2048] *= .8; hgt[2048 + k:2048 + k + 3, 1024:2048] = -.4
    col[2048:3072, 1024 + k:1024 + k + 3] *= .85; hgt[2048:3072, 1024 + k:1024 + k + 3] = -.4
emi[2048:3072, 1024:2048] = col[2048:3072, 1024:2048] * .16   # la aguja iluminada con reflectores de noche
# cubierta: impermeabilizante con grava
surface(2048, 2048, C, C, '#7e7b75', .3, 1, sm=.08); hgt[region(2048, 2048, C, C)] = noise(C, C, 1, 1, .7)
# pavimento de la plazoleta: losetas
surface(3072, 2048, C, C, '#a99c8c', .06, 6, sm=.2)
for k in range(0, C, 128):
    col[2048 + k:2048 + k + 4, 3072:4096] *= .75; col[2048:3072, 3072 + k:3072 + k + 4] *= .75
    hgt[2048 + k:2048 + k + 4, 3072:4096] = -.5; hgt[2048:3072, 3072 + k:3072 + k + 4] = -.5
# local comercial (vano de 6 m x 5 m)
GRAN = '#b8968a'
surface(0, 3072, C, C, GRAN, .05, 4, sm=.45)
px = C / 6
col[3072 + 90:3072 + 230, 60:C - 60] = hexc('#1f3f5b'); hgt[3072 + 90:3072 + 230, 60:C - 60] = .1  # letrero
col[3072 + 140:3072 + 180, 120:C - 120] = hexc('#f2f2f2'); emi[3072 + 140:3072 + 180, 120:C - 120] = hexc('#ffffff') * .8
gy0, gy1 = 3072 + 280, 4096 - 60
yy = np.linspace(0, 1, gy1 - gy0)[:, None, None]
col[gy0:gy1, 70:C - 70] = hexc('#34444f') * (1 - yy) + hexc('#6b7f8b') * yy; smo[gy0:gy1, 70:C - 70] = .93; hgt[gy0:gy1, 70:C - 70] = -.5
emi[gy0 + 40:gy1, 80:C - 80] = hexc('#ffe2b0') * .9
for x in (70, C // 2 - 6, C - 82): col[gy0:gy1, x:x + 12] = hexc('#2a2c2e'); met[gy0:gy1, x:x + 12] = .9; hgt[gy0:gy1, x:x + 12] = 0
# ventana corrida del podio (vano de 6 m x 5 m)
surface(1024, 3072, C, C, CONC, .05, 2, 64, sm=.15)
wy0, wy1 = 3072 + 260, 3072 + 900
yy = np.linspace(0, 1, wy1 - wy0)[:, None, None]
col[wy0:wy1, 1024 + 40:2048 - 40] = hexc('#2c3a44') * (1 - yy) + hexc('#5d7482') * yy; smo[wy0:wy1, 1024 + 40:2048 - 40] = .93; hgt[wy0:wy1, 1024 + 40:2048 - 40] = -.5
emi[wy0 + 20:wy1 - 10, 1024 + 60:1024 + 480] = hexc('#ffd59a') * .7
for x in range(1024 + 40, 2048 - 30, 155): col[wy0:wy1, x:x + 8] = hexc('#3a3d40'); met[wy0:wy1, x:x + 8] = .9; hgt[wy0:wy1, x:x + 8] = 0
# granito rosa
surface(2048, 3072, C, C, GRAN, .08, 3, sm=.5)
spk = rng.random((C, C)) < .08; col[3072:4096, 2048:3072][spk] *= .6
spk = rng.random((C, C)) < .05; col[3072:4096, 2048:3072][spk] = col[3072:4096, 2048:3072][spk] * .4 + .55
for k in range(0, C, 256): col[3072 + k:3072 + k + 4, 2048:3072] *= .8; hgt[3072 + k:3072 + k + 4, 2048:3072] = -.4
# metal, césped, luz de balizaje
surface(3072, 3072, C, 512, '#8f9498', .03, 1, 32, sm=.55, m=.9)
surface(3072, 3584, 512, 512, '#4f7f3a', .25, 1, sm=.1)
surface(3584, 3584, 256, 256, '#d0241b', .02, 8, sm=.6); emi[3584:3840, 3584:3840] = hexc('#ff2a1a') * 1.0
# banderas (256 x 168 px, proporción 3:2) con pliegues suaves de tela
def flag(x, y, bands):
    W, H = 256, 168; yy = 0
    for colr, frac in bands:
        h = round(H * frac); col[y + yy:y + yy + h, x:x + W] = hexc(colr); yy += h
    xs = np.arange(W)[None, :]; fold = (np.sin(xs / W * 2 * np.pi * 2.2) * .07)[..., None]
    col[y:y + H, x:x + W] *= 1 + fold + noise(H, W, 2, 2, .03)[..., None]
    hgt[y:y + H, x:x + W] = np.sin(xs / W * 2 * np.pi * 2.2) * .3; smo[y:y + H, x:x + W] = .15; met[y:y + H, x:x + W] = 0
surface(3840, 3584, 256, 512, '#8f9498', .03, 1, 32, sm=.55, m=.9); surface(3584, 3840, 256, 256, '#8f9498', .03, 1, 32, sm=.55, m=.9)
flag(3840, 3600, [('#fcd116', .5), ('#003893', .25), ('#ce1126', .25)])     # Colombia: amarillo, azul, rojo (2:1:1)
flag(3584, 3860, [('#ffffff', .5), ('#00843d', .5)])                         # Antioquia: blanco y verde

out, name = sys.argv[1], sys.argv[2]
hb = np.asarray(Image.fromarray(((hgt + 1) * 127).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)), np.float32) / 127
gy, gx = np.gradient(hb); k = 8.0
nrm = np.dstack([-gx * k, gy * k, np.ones_like(gx)]); nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
save = lambda a, f: Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8)).save(f"{out}/{name}_{f}.png", optimize=True)
save(col, 'BaseColor'); save(nrm * .5 + .5, 'Normal'); save(np.dstack([met, ao, np.zeros_like(met), smo]), 'MaskMap'); save(emi, 'Emissive')
print('texturas listas')
