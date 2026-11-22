#!/usr/bin/env python3
"""Renderiza el video vertical de LaMulta (1080x1920, 30 fps, ~70 s).

Uso: python3 video/render.py <carpeta LaMulta-video> <carpeta salida>
Produce: lamulta-vertical.mp4, musica.wav y una miniatura por escena.
"""
import math, re, subprocess, sys, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

PKG = Path(sys.argv[1]); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
SRT = Path(__file__).with_name("Subtitulos-LaMulta.srt")
W, H, FPS, DUR = 1080, 1920, 30, 70.0

PET = (11, 38, 51); SURF = (18, 49, 62); MINT = (185, 223, 203); YEL = (246, 211, 74)
WHITE = (240, 246, 247); MUTED = (170, 196, 204); LINE = (52, 92, 106)

FD = "/usr/share/fonts/opentype/inter/"
def font(w, s): return ImageFont.truetype(FD + {"r": "Inter-Regular.otf", "m": "Inter-Medium.otf", "s": "Inter-SemiBold.otf", "b": "Inter-Bold.otf"}[w], s)

def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def seg(t, a, b): return ease((t - a) / (b - a)) if b > a else float(t >= a)

# ---------- recursos ----------
office = Image.open(PKG / "maestros/oficina-lamulta.png").convert("RGB")
oc = office.crop((880, 0, 880 + 576, 1024)).resize((W + 120, H + 214), Image.LANCZOS)
oc = Image.blend(oc.filter(ImageFilter.GaussianBlur(4)), Image.new("RGB", oc.size, PET), 0.30)

def trim(im):
    return im.crop(im.getchannel("A").point(lambda a: 255 if a > 20 else 0).getbbox())

poses = Image.open(PKG / "maestros/guia-lamulta-poses-alpha.png").convert("RGBA")
POSE = [trim(poses.crop(b)) for b in [(0, 0, 515, 1024), (515, 0, 1025, 1024), (1025, 0, 1536, 1024)]]
waits = Image.open(PKG / "maestros/guia-lamulta-cuadros-espera-alpha.png").convert("RGBA")
LUPA = [waits.crop((i * 384, 0, i * 384 + 384, 512)) for i in range(4)]
CARP = [waits.crop((i * 384, 512, i * 384 + 384, 1024)) for i in range(4)]
logo = Image.open(PKG / "maestros/logo-lamulta.webp").convert("L")
LOGO = Image.new("RGBA", logo.size, (255, 255, 255, 0)); LOGO.putalpha(logo)
def shot(n): return Image.open(PKG / f"pantallas/celular-oscuro-{n}.png").convert("RGB")

def fade_bottom(im, frac=0.18):
    im = im.copy(); a = np.array(im.getchannel("A"), dtype=np.float32); h = a.shape[0]; n = int(h * frac)
    a[h - n:] *= np.linspace(1, 0, n)[:, None]; im.putalpha(Image.fromarray(a.astype(np.uint8))); return im

def bg(t, zoom=0.0):
    z = 1.0 + 0.04 * (t / DUR) + zoom
    w, h = int(W * z), int(H * z)
    im = oc.resize((w, h), Image.BILINEAR) if z != 1 else oc
    x = int((im.width - W) * (0.5 + 0.3 * math.sin(t / 9))); y = int((im.height - H) * 0.5)
    return im.crop((x, y, x + W, y + H)).copy()

def paste_guide(frame, im, cx, bottom, height, t, breathe=True):
    s = height / im.height * (1 + (0.006 * math.sin(t * 2.1) if breathe else 0))
    g = fade_bottom(im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS))
    frame.paste(g, (int(cx - g.width / 2), int(bottom - g.height + 4 * math.sin(t * 1.3))), g)

def rr(d, box, r, **kw): d.rounded_rectangle(box, r, **kw)

# ---------- marco de celular con captura ----------
PX, PY, PW, PH = 66, 268, 948, 1270
SC = PW / 390

def phone(frame, src, scroll, hl=(), extra=None, alpha=1.0, dy=0):
    s = src.resize((PW, int(src.height * SC)), Image.LANCZOS) if src.width == 390 else src
    view = s.crop((0, int(scroll * SC), PW, int(scroll * SC) + PH)).convert("RGBA")
    d = ImageDraw.Draw(view)
    if extra: extra(view, d, scroll)
    for (x0, y0, x1, y1, a) in hl:
        if a <= 0: continue
        box = [x0 * SC - 8, (y0 - scroll) * SC - 8, x1 * SC + 8, (y1 - scroll) * SC + 8]
        lay = Image.new("RGBA", view.size, (0, 0, 0, 0)); ImageDraw.Draw(lay).rounded_rectangle(box, 22, outline=YEL + (int(255 * a),), width=7)
        view = Image.alpha_composite(view, lay)
    m = Image.new("L", view.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, PW - 1, PH - 1], 44, fill=int(255 * alpha))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([PX + 6, PY + 24 + dy, PX + PW + 6, PY + PH + 30 + dy], 48, fill=(0, 0, 0, int(140 * alpha)))
    frame.paste(Image.new("RGB", (W, H)), (0, 0), sh.filter(ImageFilter.GaussianBlur(24)).getchannel("A"))
    frame.paste(view.convert("RGB"), (PX, PY + dy), m)
    o = ImageDraw.Draw(frame); o.rounded_rectangle([PX - 2, PY - 2 + dy, PX + PW + 1, PY + PH + 1 + dy], 46, outline=LINE, width=3)

def pick(img, x, y): return img.getpixel((x, y))[:3]

# ---------- pantallas simuladas (datos ficticios, estilo de la interfaz real) ----------
S = SC
def mock_canvas(h=PH + int(320 * S)):
    c = Image.new("RGB", (PW, h), PET); d = ImageDraw.Draw(c)
    hdr = shot("simit").resize((PW, int(844 * S)), Image.LANCZOS).crop((0, 0, PW, int(100 * S)))
    c.paste(hdr, (0, 0)); return c, d

def tabs(d, y, active):
    names = ["Consulta gratuita", "Tu plan", "Documentos y\nseguimiento"]; xs = [30, 142, 255]
    for i, n in enumerate(names):
        col = MINT if i <= active else LINE
        d.rectangle([xs[i] * S, y * S, (xs[i] + 104) * S, (y + 3) * S], fill=col)
        d.multiline_text((xs[i] * S, (y + 12) * S), n, font=font("b" if i == active else "m", int(13 * S)), fill=WHITE, spacing=6)

def card(d, x0, y0, x1, y1, fill=SURF, outline=LINE, r=14, w=2): rr(d, [x0 * S, y0 * S, x1 * S, y1 * S], int(r * S), fill=fill, outline=outline, width=w)
def tx(d, x, y, s, size, w="r", fill=WHITE): d.text((x * S, y * S), s, font=font(w, int(size * S)), fill=fill)
def button(d, x0, y0, x1, y1, label, yellow=True, press=0.0):
    inset = 2 * press
    rr(d, [(x0 + inset) * S, (y0 + inset) * S, (x1 - inset) * S, (y1 - inset) * S], int(14 * S), fill=YEL if yellow else SURF, outline=None if yellow else MINT, width=3)
    f = font("b", int(15 * S)); tw = d.textlength(label, font=f)
    d.text(((x0 + x1) / 2 * S - tw / 2, ((y0 + y1) / 2 - 9) * S), label, font=f, fill=(20, 30, 30) if yellow else WHITE)
def check(d, x, y, on=True, col=MINT):
    d.ellipse([x * S, y * S, (x + 22) * S, (y + 22) * S], fill=col if on else None, outline=col, width=4)
    if on: d.line([((x + 6) * S, (y + 11) * S), ((x + 10) * S, (y + 15) * S), ((x + 17) * S, (y + 7) * S)], fill=PET, width=6)

def typed(s, p): return s[: int(len(s) * min(max(p, 0), 1))]

def mock_correo(t):
    c, d = mock_canvas()
    sim = shot("simit").resize((PW, int(844 * S)), Image.LANCZOS).crop((0, int(100 * S), PW, int(292 * S)))
    c.paste(sim, (0, int(100 * S)))
    card(d, 14, 320, 376, 650)
    tx(d, 32, 338, "▼ Recibir el resultado por correo", 16, "m")
    tx(d, 32, 380, "Correo electrónico", 14, "r", MUTED)
    card(d, 32, 404, 358, 452, fill=PET, outline=LINE, r=10)
    tx(d, 46, 418, typed("persona.prueba@ejemplo.co", (t - 16.6) / 2.0) or "tu@correo.com", 16, "r", WHITE if t > 16.6 else MUTED)
    button(d, 32, 466, 358, 516, "Enviar código", press=float(18.9 < t < 19.2))
    if t > 19.4:
        a = seg(t, 19.4, 19.9)
        tx(d, 32, 536, "Escribe el código de 6 dígitos", 14, "m", MUTED)
        for i in range(6):
            x = 32 + i * 55; card(d, x, 562, x + 47, 618, fill=PET, outline=MINT if a > .5 else LINE, r=10)
            if t > 20.2 + i * 0.35: d.ellipse([(x + 17) * S, 584 * S, (x + 30) * S, 597 * S], fill=WHITE)
    if t > 22.6:
        card(d, 14, 664, 376, 716, fill=(24, 70, 62), outline=MINT); check(d, 30, 679); tx(d, 62, 679, "Correo confirmado", 16, "s")
    return c

def mock_escrito(t):
    c, d = mock_canvas(); card(d, 14, 112, 376, 640); tabs(d, 128, 1)
    tx(d, 32, 200, "TU EXPEDIENTE · DEMO-001", 13, "b", MUTED)
    tx(d, 32, 228, "Revisa tu escrito", 24, "b")
    rows = [("Nombre", "Persona De Prueba"), ("Documento", "CC ••••••001"), ("Multas incluidas", "2"), ("Entrega", "Por correo electrónico")]
    for i, (k, v) in enumerate(rows):
        y = 280 + i * 62; card(d, 32, y, 358, y + 52, r=10)
        tx(d, 46, y + 8, k, 12, "r", MUTED); tx(d, 46, y + 26, v, 15, "s")
        if t > 39.6 + i * 0.5: check(d, 324, y + 15)
    button(d, 32, 548, 358, 600, "Los datos están correctos", press=float(42.0 < t < 42.3))
    return c

def mock_plan(t):
    c, d = mock_canvas(); card(d, 14, 112, 376, 700); tabs(d, 128, 1)
    tx(d, 32, 200, "Elige tu plan", 24, "b")
    tx(d, 32, 236, "El valor se muestra antes de pagar.", 14, "r", MUTED)
    for i, (n, s) in enumerate([("Plan de ejemplo A", "Escrito revisado por un abogado"), ("Plan de ejemplo B", "Incluye seguimiento del caso")]):
        y = 272 + i * 104; sel = (i == 0 and t > 43.6)
        card(d, 32, y, 358, y + 90, outline=MINT if sel else LINE, w=4 if sel else 2)
        d.ellipse([46 * S, (y + 33) * S, 68 * S, (y + 55) * S], outline=MINT, width=4)
        if sel: d.ellipse([51 * S, (y + 38) * S, 63 * S, (y + 50) * S], fill=MINT)
        tx(d, 82, y + 22, n, 17, "s"); tx(d, 82, y + 50, s, 13, "r", MUTED)
    button(d, 32, 500, 358, 556, "Pagar con Wompi", press=float(45.2 < t < 45.5))
    tx(d, 32, 572, "Pago en entorno de pruebas · datos ficticios", 12, "r", MUTED)
    return c

def mock_estado(t):
    c, d = mock_canvas(); card(d, 14, 112, 376, 640); tabs(d, 128, 2)
    tx(d, 32, 200, "TU EXPEDIENTE · DEMO-001", 13, "b", MUTED)
    tx(d, 32, 228, "Estado de tu documento", 24, "b")
    steps = [("Pago confirmado", "Entorno de pruebas", 46.4), ("Revisión jurídica", "Un abogado revisa tu documento", 48.0), ("Entrega por correo", "Recibirás el documento revisado", 99)]
    for i, (n, s, ton) in enumerate(steps):
        y = 290 + i * 96
        if i < 2: d.line([(43 * S, (y + 26) * S), (43 * S, (y + 96) * S)], fill=LINE, width=5)
        on = t > ton; act = (i == 1 and on)
        if act: card(d, 24, y - 12, 368, y + 66, fill=(24, 62, 72), outline=YEL, w=4)
        check(d, 32, y, on=on and i == 0, col=MINT if i == 0 else (YEL if act else LINE))
        if act: d.ellipse([39 * S, (y + 7) * S, 47 * S, (y + 15) * S], fill=YEL)
        tx(d, 68, y - 2, n, 18, "s", WHITE if (on or i == 2) else MUTED); tx(d, 68, y + 26, ("En curso · " if act else "") + s, 13, "r", MUTED)
    return c

def mock_expediente(t):
    c, d = mock_canvas(); card(d, 14, 112, 376, 720); tabs(d, 128, 2)
    tx(d, 32, 200, "Mi expediente", 26, "b"); tx(d, 32, 240, "Expediente DEMO-001 · datos ficticios", 13, "r", MUTED)
    card(d, 32, 272, 358, 340, fill=(24, 70, 62), outline=MINT); check(d, 46, 295)
    tx(d, 80, 284, "Documento aprobado", 16, "s"); tx(d, 80, 308, "escrito-demo-001.pdf", 13, "r", MUTED)
    tx(d, 32, 362, "Número de radicado", 14, "m", MUTED)
    card(d, 32, 386, 358, 432, fill=PET, r=10)
    tx(d, 46, 399, typed("RAD-PRUEBA-0001", (t - 55.5) / 1.6) or "Ej. 2026-000000", 16, "r", WHITE if t > 55.5 else MUTED)
    button(d, 32, 446, 358, 496, "Registrar radicado", press=float(57.6 < t < 57.9))
    if t > 58.0: tx(d, 32, 506, "✓ Radicado guardado", 13, "s", MINT)
    tx(d, 32, 548, "¿Llegó una respuesta?", 16, "s")
    button(d, 32, 578, 358, 628, "Adjuntar respuesta de la autoridad", yellow=False, press=float(61.5 < t < 61.8))
    if t > 62.0: tx(d, 32, 640, "respuesta-autoridad-demo.pdf · en evaluación", 12, "r", MINT)
    return c

def hl_mock(t, a, b): return 0.0 if t < a or t > b else 0.55 + 0.45 * math.sin((t - a) * 6)

# ---------- escenas ----------
BIEN, SIMIT, ANAL, ORI = shot("bienvenida"), shot("simit"), shot("analisis"), shot("orientacion")
SEL_BG = pick(BIEN, 200, 450); NUM_BG = pick(BIEN, 300, 545)

def bien_extra(view, d, scroll):
    t = bien_extra.t
    def at(x, y): return (x * SC, (y - scroll) * SC)
    if t > 8.4:
        d.rectangle([*at(30, 447), *at(340, 484)], fill=SEL_BG); d.text(at(37, 456), "Cédula de ciudadanía", font=font("r", int(16.5 * SC)), fill=WHITE)
    if t > 9.6:
        d.rectangle([*at(30, 537), *at(355, 575)], fill=NUM_BG); d.text(at(37, 546), "•" * min(10, int((t - 9.6) * 9)), font=font("r", int(16.5 * SC)), fill=WHITE)
    if t > 11.0:
        d.rounded_rectangle([*at(25, 599), *at(46, 620)], 6, fill=MINT); d.line([at(29, 610), at(34, 615), at(42, 604)], fill=PET, width=7)

def sc_intro(t):
    f = bg(t, 0.06 * (1 - seg(t, 0, 3)))
    if t < 3.6: paste_guide(f, POSE[0], W / 2, 1600, 1250, t)
    a = seg(t, 3.3, 4.1)
    if a > 0:
        bien_extra.t = t; phone(f, BIEN, 0, alpha=a, dy=int(60 * (1 - a)))
    k = 1 - seg(t, 0, 1.4)
    if k > 0: f = Image.blend(f, Image.new("RGB", (W, H), PET), k)
    return f

def sc_form(t):
    f = bg(t); bien_extra.t = t
    scroll = 336 * seg(t, 7.0, 8.2)
    hls = [(22, 440, 368, 490, hl_mock(t, 7.9, 9.5)), (22, 530, 368, 581, hl_mock(t, 9.3, 10.9)),
           (18, 594, 372, 668, hl_mock(t, 10.7, 11.5)), (22, 687, 368, 742, hl_mock(t, 11.4, 12.4))]
    phone(f, BIEN, scroll, hls, extra=bien_extra)
    return f

def sc_lupa(t):
    f = bg(t); paste_guide(f, LUPA[int(t * 3.2) % 4], W / 2, 1560, 1180, t, breathe=False)
    d = ImageDraw.Draw(f); rr(d, [230, 300, 850, 392], 46, fill=SURF, outline=LINE, width=3)
    dots = "." * (1 + int(t * 2.5) % 3); fnt = font("s", 40); s = "Consultando SIMIT" + dots
    d.text((270, 324), s, font=fnt, fill=WHITE)
    return f

def sc_correo(t):
    f = bg(t); phone(f, mock_correo(t), 230 * seg(t, 19.2, 20.0), [(32, 404, 358, 452, hl_mock(t, 16.4, 18.7)), (32, 562, 358, 618, hl_mock(t, 19.6, 22.5))]); return f

def sc_carpeta(t):
    f = bg(t); paste_guide(f, CARP[int(t * 2.6) % 4], W / 2, 1560, 1180, t, breathe=False); return f

def sc_analisis(t):
    f = bg(t); phone(f, ANAL, 300 * seg(t, 28.4, 30.0), [(31, 698, 359, 820, hl_mock(t, 29.8, 31.6))]); return f

def ori_extra(view, d, scroll):
    if ori_extra.t > 35.6:
        cx, cy = 54 * SC, (1220 - scroll) * SC; d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=MINT)

def sc_orient(t):
    f = bg(t); ori_extra.t = t
    scroll = 500 + 330 * seg(t, 33.6, 34.8)
    phone(f, ORI, scroll, [(31, 700, 359, 1030, hl_mock(t, 31.8, 33.8)), (31, 1198, 359, 1244, hl_mock(t, 34.8, 38.6))], extra=ori_extra)
    return f

def sc_escrito(t):
    f = bg(t); src = mock_escrito(t) if t < 42.6 else mock_plan(t)
    phone(f, src, 90 * seg(t, 44.2, 45.0) if t >= 42.6 else 0, [(32, 272, 358, 362, hl_mock(t, 43.4, 44.6)), (32, 500, 358, 556, hl_mock(t, 44.6, 45.9))] if t >= 42.6 else [])
    return f

def sc_estado(t):
    f = bg(t); phone(f, mock_estado(t), 70 * seg(t, 49.0, 50.0)); return f

def sc_exp(t):
    f = bg(t); phone(f, mock_expediente(t), 150 * seg(t, 58.6, 59.6), [(32, 386, 358, 496, hl_mock(t, 55.0, 59.2)), (32, 578, 358, 628, hl_mock(t, 59.8, 63.6))]); return f

def sc_cierre(t):
    f = bg(t); paste_guide(f, POSE[2], W / 2 + 60, 1560, 1000, t)
    a = seg(t, 64.6, 65.4)
    lg = LOGO.resize((int(LOGO.width * 1.9), int(LOGO.height * 1.9)), Image.LANCZOS)
    m = lg.getchannel("A").point(lambda v: int(v * a))
    d = ImageDraw.Draw(f, "RGBA"); rr(d, [W / 2 - 360, 250, W / 2 + 360, 250 + lg.height + 40], 40, fill=PET + (int(225 * a),))
    f.paste(lg.convert("RGB"), (int(W / 2 - lg.width / 2), 270), m)
    return f

SCENES = [(0, 7, sc_intro), (7, 12.15, sc_form), (12.15, 16, sc_lupa), (16, 24, sc_correo), (24, 28.2, sc_carpeta),
          (28.2, 31.6, sc_analisis), (31.6, 39, sc_orient), (39, 46.05, sc_escrito), (46.05, 54, sc_estado),
          (54, 64, sc_exp), (64, 70.01, sc_cierre)]
CHIPS = [(0.6, 7, "Análisis inicial gratis"), (7, 16, "Consulta en el SIMIT"), (16, 24, "Confirma tu correo"),
         (24, 39, "Entiende qué puedes hacer"), (39, 54, "Revisión jurídica antes de la entrega"), (54, 64, "Mi expediente")]

def parse_srt(p):
    out = []
    for b in re.split(r"\n\s*\n", p.read_text(encoding="utf-8").strip()):
        L = b.strip().splitlines(); a, c = L[1].split(" --> ")
        ts = lambda s: (lambda h, m, x: int(h) * 3600 + int(m) * 60 + float(x.replace(",", ".")))(*s.strip().split(":"))
        out.append((ts(a), ts(c), L[2:]))
    return out
SUBS = parse_srt(SRT)

def overlays(f, t):
    d = ImageDraw.Draw(f, "RGBA")
    for a, b, s in CHIPS:
        if a <= t < b:
            k = min(seg(t, a, a + 0.35), 1 - seg(t, b - 0.25, b)); fnt = font("b", 46); tw = d.textlength(s, font=fnt)
            x0 = W / 2 - tw / 2 - 40; y0 = 120 - 20 * (1 - k)
            rr(d, [x0, y0, W / 2 + tw / 2 + 40, y0 + 96], 48, fill=MINT + (int(245 * k),))
            d.text((W / 2 - tw / 2, y0 + 22), s, font=fnt, fill=PET + (int(255 * k),))
    if t >= 64.5:  # dominio fijo al cierre (más de 2 s)
        k = seg(t, 64.5, 65.2); fnt = font("b", 92); s = "lamulta.com.co"; tw = d.textlength(s, font=fnt)
        rr(d, [W / 2 - tw / 2 - 50, 1590, W / 2 + tw / 2 + 50, 1740], 34, fill=YEL + (int(255 * k),))
        d.text((W / 2 - tw / 2, 1615), s, font=fnt, fill=PET + (int(255 * k),))
        return
    for a, b, lines in SUBS:
        if a <= t < b:
            fnt = font("s", 46); y = 1600 if len(lines) == 2 else 1632
            mw = max(d.textlength(l, font=fnt) for l in lines)
            rr(d, [W / 2 - mw / 2 - 34, y - 22, W / 2 + mw / 2 + 34, y + 62 * len(lines) + 14], 26, fill=(5, 20, 27, 205))
            for i, l in enumerate(lines):
                lw = d.textlength(l, font=fnt); d.text((W / 2 - lw / 2, y + i * 62), l, font=fnt, fill=(255, 255, 255, 255))

def frame_at(t):
    for i, (a, b, fn) in enumerate(SCENES):
        if a <= t < b: break
    f = fn(t)
    if i > 0 and t < a + 0.4:
        f = Image.blend(SCENES[i - 1][2](t), f, ease((t - a) / 0.4))
    overlays(f, t); return f

# ---------- música instrumental discreta ----------
def music(path, sr=48000):
    n = int(DUR * sr); tt = np.arange(n) / sr; L = np.zeros(n); R = np.zeros(n)
    prog = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
    bar = 4.0
    for k in range(int(DUR / bar) + 1):
        ch = prog[k % 4]; s0 = int(k * bar * sr); s1 = min(n, int((k + 1) * bar * sr + 1.5 * sr))
        if s0 >= n: break
        u = tt[s0:s1] - k * bar; env = np.minimum(u / 1.2, 1) * np.exp(-np.maximum(u - bar, 0) * 2.5)
        for j, m in enumerate(ch + [ch[0] - 12]):
            fq = 440 * 2 ** ((m - 69) / 12); w = (np.sin(2 * np.pi * fq * u) + 0.25 * np.sin(4 * np.pi * fq * u)) * env * 0.05
            L[s0:s1] += w * (0.7 if j % 2 else 1.0); R[s0:s1] += w * (1.0 if j % 2 else 0.7)
        for q in range(8):  # arpegio suave
            a0 = s0 + int(q * 0.5 * sr); a1 = min(n, a0 + int(1.2 * sr))
            if a0 >= n: break
            u2 = tt[a0:a1] - tt[a0]; m = ch[q % 3] + 12; fq = 440 * 2 ** ((m - 69) / 12)
            p = np.sin(2 * np.pi * fq * u2) * np.exp(-u2 * 4) * 0.025
            L[a0:a1] += p * (1 - q % 2 * 0.4); R[a0:a1] += p * (0.6 + q % 2 * 0.4)
    for at, fq in [(12.15, 1800), (24.0, 900)]:  # lupa y carpeta: sonido puntual leve
        a0 = int(at * sr); u = tt[a0:a0 + int(0.25 * sr)] - at
        s = np.sin(2 * np.pi * fq * u) * np.exp(-u * 30) * 0.08; L[a0:a0 + len(s)] += s; R[a0:a0 + len(s)] += s
    fade = np.ones(n); fi = int(1.5 * sr); fo = int(2.5 * sr); fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0, fo)
    st = np.stack([L * fade, R * fade], 1); st = st / np.abs(st).max() * 0.22  # muy por debajo de la voz
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((st * 32767).astype("<i2").tobytes())

if __name__ == "__main__":
    music(OUT / "musica.wav")
    for i, (a, b, _) in enumerate(SCENES):
        frame_at(min(b - 0.5, a + (b - a) * 0.6)).save(OUT / f"escena-{i + 1:02d}.jpg", quality=85)
    if "--stills" in sys.argv: sys.exit()
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", str(OUT / "musica.wav"), "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-profile:v", "high",
                          "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", "-shortest", str(OUT / "lamulta-vertical.mp4")], stdin=subprocess.PIPE)
    for k in range(int(DUR * FPS)):
        p.stdin.write(frame_at(k / FPS).tobytes())
        if k % 300 == 0: print(f"{k / FPS:.0f}s", flush=True)
    p.stdin.close(); p.wait(); print("listo", p.returncode)
