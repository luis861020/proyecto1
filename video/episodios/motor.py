#!/usr/bin/env python3
"""Motor de episodios explicativos de LaMulta (guía + voz Lina).

Uso: python3 video/episodios/motor.py <episodio.json> <carpeta LaMulta-video> <carpeta salida> [--stills]
Tipos de segmento: guia (pose 0-2), tarjeta (grande/texto/pose), linea (línea de tiempo de 3 años),
lupa, carpeta, cierre. Cada segmento lleva "voz" y opcionalmente "chip".
La clave de ElevenLabs la inyecta el proxy del entorno.
"""
import base64, json, math, subprocess, sys, urllib.request, wave
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
EP, PKG, OUT = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]); OUT.mkdir(parents=True, exist_ok=True)
STILLS = "--stills" in sys.argv
sys.argv = ["render.py", PKG, str(OUT)]
__file__ = str(HERE.parent / "render.py")
exec(open(HERE.parent / "render.py", encoding="utf-8").read().split('if __name__ == "__main__":')[0])

VOICE = "yfUfwZTRubVrsUZWqzwp"  # Lina
ep = json.loads(EP.read_text(encoding="utf-8")); SEGS = ep["segmentos"]; slug = EP.stem
LEAD, GAP, HOLD = 0.35, 0.45, 2.6
DISCLAIMER = "Información general. Cada caso depende de sus fechas y documentos."

# ---------- voz (una sola llamada para prosodia natural) ----------
full = " ".join(s["voz"] for s in SEGS)
mp3, alf = OUT / f"{slug}-voz.mp3", OUT / f"{slug}-voz.json"
if not mp3.exists() or json.loads(alf.read_text()).get("text") != full:
    body = json.dumps({"text": full, "model_id": "eleven_multilingual_v2", "language_code": "es",
                       "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.2}}).encode()
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}/with-timestamps?output_format=mp3_44100_128",
                                 data=body, headers={"Content-Type": "application/json", "xi-api-key": "proxy-injected"})
    d = json.load(urllib.request.urlopen(req, timeout=180))
    mp3.write_bytes(base64.b64decode(d["audio_base64"])); al = d["alignment"]; al["text"] = full; alf.write_text(json.dumps(al))
al = json.loads(alf.read_text()); CS, CE = al["character_start_times_seconds"], al["character_end_times_seconds"]

# segmentos en el audio: [inicio, fin] por caracteres
pos, sa = 0, []
for s in SEGS:
    a, b = pos, pos + len(s["voz"]) - 1; sa.append((CS[a], CE[b])); pos = b + 2
# línea de tiempo del video: cada segmento = su voz + pausa; la voz se recorta por segmento
TL, t = [], 0.0
for i, (s, (va, vb)) in enumerate(zip(SEGS, sa)):
    st = t; vstart = st + (LEAD if i == 0 else 0.12); en = vstart + (vb - va) + (HOLD if s["tipo"] == "cierre" else GAP)
    TL.append(dict(seg=s, a=st, b=en, vstart=vstart, va=va, vb=vb)); t = en
NDUR = round(t, 2)
def amap(ta):  # tiempo de audio original -> tiempo de video
    for x in TL:
        if ta <= x["vb"] + 0.2: return x["vstart"] + max(ta - x["va"], 0)
    return TL[-1]["vstart"] + ta - TL[-1]["va"]

# ---------- subtítulos por fragmentos (≤2 líneas de 34 car.) ----------
words, cur, st0 = [], "", None
for i, ch in enumerate(full + " "):
    if ch == " ":
        if cur: words.append((cur, st0, CE[i - 1])); cur = ""
    else:
        if not cur: st0 = CS[i]
        cur += ch
def chunks():
    out, line, lines, start = [], "", [], None
    for w, a, b in words:
        if start is None: start = a
        if len(line) + len(w) + 1 > 34 and line:
            lines.append(line); line = ""
            if len(lines) == 2: out.append((start, prev_end, lines)); lines, start = [], a
        line = (line + " " + w).strip(); prev_end = b
        if (w[-1] in ".?!:" and (lines or len(line) > 18)) or (w[-1] in ",;" and lines and len(line) > 12):
            lines.append(line); out.append((start, b, lines)); line, lines, start = "", [], None
    if line or lines: out.append((start, prev_end, lines + ([line] if line else [])))
    return out
SUBS2 = [(amap(a), amap(b) + 0.25, ls) for a, b, ls in chunks()]
for k in range(len(SUBS2) - 1): SUBS2[k] = (SUBS2[k][0], min(SUBS2[k][1], SUBS2[k + 1][0]), SUBS2[k][2])

# ---------- dibujo ----------
def wrap(d, text, fnt, maxw):
    out, line = [], ""
    for w in text.split():
        if d.textlength((line + " " + w).strip(), font=fnt) > maxw and line: out.append(line); line = w
        else: line = (line + " " + w).strip()
    return out + [line]

def chip(d, s, k, y=120):
    fnt = font("b", 46); tw = d.textlength(s, font=fnt); y0 = y - 20 * (1 - k)
    rr(d, [W / 2 - tw / 2 - 40, y0, W / 2 + tw / 2 + 40, y0 + 96], 48, fill=MINT + (int(245 * k),))
    d.text((W / 2 - tw / 2, y0 + 22), s, font=fnt, fill=PET + (int(255 * k),))

# ---------- animación del personaje ----------
import random
_FC = {}
def F(w, s):
    k_ = (w, int(s))
    if k_ not in _FC: _FC[k_] = font(w, int(s))
    return _FC[k_]

ENV = None
def env_at(tt):  # intensidad de la voz (0-1) para que la guía "hable"
    global ENV
    if ENV is None:
        wv = OUT / f"{slug}-voz.wav"
        if not wv.exists(): voice(wv)
        with wave.open(str(wv)) as w_: a_ = np.frombuffer(w_.readframes(w_.getnframes()), dtype="<i2").reshape(-1, 2)[:, 0].astype(np.float32) / 32768
        hop = 48000 // FPS; n_ = len(a_) // hop; r_ = np.sqrt((a_[:n_ * hop].reshape(n_, hop) ** 2).mean(1))
        r_ = np.clip(r_ / (np.percentile(r_, 95) + 1e-6), 0, 1); sm = np.zeros_like(r_); v_ = 0.0
        for j_, q_ in enumerate(r_): v_ += (q_ - v_) * (0.45 if q_ > v_ else 0.12); sm[j_] = v_
        ENV = sm
    return float(ENV[min(max(int(tt * FPS), 0), len(ENV) - 1)])

# pausas de frase dentro de cada segmento -> cambios de gesto
_pos = 0
for x_ in TL:
    L_ = len(x_["seg"]["voz"]); idx = [j for j in range(_pos, _pos + L_ - 1) if full[j] in ".?!,:" and j - _pos > 8]
    x_["beats"] = [amap(CE[j]) for j in idx]; _pos += L_ + 1

RNG = random.Random(slug)
GUIA_SHOTS = [("medio", W / 2, 1600, 1250), ("primer", W / 2 + 30, 2120, 1850), ("izq", 410, 1680, 1420), ("der", 670, 1680, 1420)]
last = None
for i_, x_ in enumerate(TL):
    ty_ = x_["seg"]["tipo"]
    if ty_ == "guia":
        opts = [s_ for s_ in GUIA_SHOTS if s_[0] != last and not (i_ == 0 and s_[0] == "primer")]; x_["shot"] = RNG.choice(opts); last = x_["shot"][0]
    elif ty_ in ("lupa", "carpeta"):
        x_["shot"] = RNG.choice([("medio", W / 2, 1580, 1200), ("primer", W / 2, 1900, 1650)])
    x_["layout"] = RNG.choice(["arriba", "lado"]) if ty_ == "tarjeta" else None
    x_["side"] = RNG.choice([-1, 1]); x_["cam"] = RNG.choice(["in", "out"]); x_["trans"] = RNG.choice(["punch", "barrido"]) if i_ else None
for i_ in range(1, len(TL)):  # evita dos tarjetas seguidas con el mismo diseño
    if TL[i_]["layout"] and TL[i_]["layout"] == TL[i_ - 1].get("layout"): TL[i_]["layout"] = "lado" if TL[i_]["layout"] == "arriba" else "arriba"

_GC = {}
def _scaled(im, h):
    key = (id(im), int(h / 8))
    if key not in _GC:
        if len(_GC) > 60: _GC.clear()
        s_ = h / im.height; _GC[key] = fade_bottom(im.resize((int(im.width * s_), int(im.height * s_)), Image.LANCZOS))
    return _GC[key]

def guide(f, ims, cx, bottom, height, tt, k=9.0, slide=0, seed=0.0, talk=True):
    """ims: [(imagen, peso)] para fundir entre gestos o cuadros."""
    e = env_at(tt) if talk else 0.0
    h = height * (1 + 0.012 * e + 0.004 * math.sin(tt * 2.1 + seed))
    ang = 0.7 * math.sin(tt * 0.7 + seed) + 1.1 * e * math.sin(tt * 5.3 + seed)
    dx = slide * (1 - ease(k / 0.55)) * W * 0.75; dy = -14 * e + 5 * math.sin(tt * 1.3 + seed)
    for im, wgt in ims:
        if wgt <= 0.01: continue
        g = _scaled(im, h).rotate(ang, Image.BICUBIC, expand=True)
        m = g.getchannel("A") if wgt >= 0.99 else g.getchannel("A").point(lambda v, w_=wgt: int(v * w_))
        f.paste(g, (int(cx - g.width / 2 + dx), int(bottom - g.height + dy)), m)

def gesture(x, tt, base=0):
    n = sum(1 for b in x["beats"] if b < tt); prev = [b for b in x["beats"] if b < tt]
    a = ease((tt - prev[-1]) / 0.14) if prev else 1.0
    cur, old = POSE[[0, 2][(base + n) % 2]], POSE[[0, 2][(base + n - 1) % 2]]
    return [(old, 1 - a), (cur, a)] if a < 1 else [(cur, 1.0)]

def anim_frames(fr, tt, fps=5.0):
    seq = [0, 1, 2, 3, 2, 1]; u = tt * fps; i0 = int(u) % 6; a = ease((u - int(u) - 0.8) / 0.2)
    return [(fr[seq[i0]], 1 - a), (fr[seq[(i0 + 1) % 6]], a)]

def pop(k):  # escala con rebote para textos grandes
    return 1 + 0.22 * math.exp(-k * 7) * math.cos(k * 13)

def card_big(d, s, cx, y, maxw, k, a):
    big = s["grande"]; fs = 210
    while d.textlength(big, font=F("b", fs)) > maxw and fs > 70: fs -= 6
    fs2 = fs * pop(k); fb = F("b", fs2); bw = d.textlength(big, font=fb)
    d.text((cx - bw / 2, y + (fs - fs2) * 0.5), big, font=fb, fill=YEL + (int(255 * a),)); return fs

def draw_seg(x, tt):
    s = x["seg"]; k = tt - x["a"]; p = k / (x["b"] - x["a"]); f = bg(tt); ty = s["tipo"]; sd = x["side"]; seed = sum(map(ord, slug)) % 7 + x["a"]
    first = x is TL[0]
    if ty == "guia":
        _, cx, bt, hh = x["shot"]
        guide(f, gesture(x, tt, s.get("pose", 0) // 2), cx, bt, hh, tt, k, slide=sd if first else 0, seed=seed)
        if first and 0.5 < k < 4.2:
            a = min(ease((k - 0.5) / 0.4), 1 - ease((k - 3.8) / 0.4)); d = ImageDraw.Draw(f, "RGBA"); tx_ = "Tu guía digital · LaMulta"; fn = F("s", 38)
            tw = d.textlength(tx_, font=fn); x0 = 60 - 40 * (1 - a)
            rr(d, [x0, 1440, x0 + tw + 70, 1516], 38, fill=YEL + (int(240 * a),)); d.text((x0 + 35, 1458), tx_, font=fn, fill=PET + (int(255 * a),))
    elif ty in ("lupa", "carpeta"):
        _, cx, bt, hh = x["shot"]
        guide(f, anim_frames(LUPA if ty == "lupa" else CARP, tt), cx, bt, hh, tt, k, seed=seed, talk=False)
    elif ty == "tarjeta":
        lay = x["layout"]; d = ImageDraw.Draw(f, "RGBA"); a = ease(k / 0.35); off = sd * 180 * (1 - ease(k / 0.45))
        if lay == "arriba":
            guide(f, [(POSE[s.get("pose", 1)], 1)], W / 2 + 40 * sd, 1590, 930, tt, k, seed=seed)
            d = ImageDraw.Draw(f, "RGBA"); X0, X1, Y0, Y1 = 70 + off, W - 70 + off, 250, 820
        else:
            guide(f, [(POSE[s.get("pose", 1)], 1)], (790 if sd > 0 else 290), 1640, 1250, tt, k, seed=seed)
            d = ImageDraw.Draw(f, "RGBA"); X0, X1, Y0, Y1 = (60 if sd > 0 else 380) + off, (700 if sd > 0 else 1020) + off, 260, 900
        rr(d, [X0, Y0, X1, Y1], 48, fill=SURF + (int(238 * a),), outline=LINE + (int(255 * a),), width=3)
        cxx = (X0 + X1) / 2; fs = card_big(d, s, cxx, Y0 + 60, X1 - X0 - 90, k, a)
        fl = F("s", 50 if lay == "arriba" else 44); ls = wrap(d, s["texto"], fl, X1 - X0 - 100); ta = ease((k - 0.25) / 0.4)
        for j, l in enumerate(ls[:4]):
            lw = d.textlength(l, font=fl); d.text((cxx - lw / 2, Y0 + 90 + fs + j * 60 + 20 * (1 - ta)), l, font=fl, fill=WHITE + (int(255 * ta),))
    elif ty == "linea":
        guide(f, [(POSE[1], 1)], (780 if sd > 0 else 300), 1600, 900, tt, k, seed=seed)
        d = ImageDraw.Draw(f, "RGBA"); a = ease(k / 0.35); rr(d, [60, 260, W - 60, 900], 48, fill=SURF + (int(238 * a),), outline=LINE, width=3)
        x0, x1, y = 140, W - 140, 560
        d.line([(x0, y), (x1, y)], fill=LINE, width=14)
        g = ease(p / 0.45); mid = x0 + (x1 - x0) * 0.55; reset = ease((p - 0.5) / 0.35)
        if reset <= 0: d.line([(x0, y), (x0 + (x1 - x0) * g * 0.55, y)], fill=MINT, width=14)
        else:
            d.line([(x0, y), (mid, y)], fill=(90, 120, 128), width=14); d.line([(mid, y), (mid + (x1 - mid) * reset, y)], fill=MINT, width=14)
        fl = F("s", 40)
        d.ellipse([x0 - 22, y - 22, x0 + 22, y + 22], fill=MINT); d.text((x0 - 40, y + 44), "Infracción", font=fl, fill=WHITE)
        d.text((x1 - 150, y - 110), "3 años", font=F("b", 58 * (pop(k - 0.3) if k > 0.3 else 1)), fill=YEL)
        if p > 0.38:
            a2 = ease((p - 0.38) / 0.12); r_ = 26 * (1 + 0.6 * math.exp(-(p - 0.38) * 25))
            d.ellipse([mid - r_, y - r_, mid + r_, y + r_], fill=YEL + (int(255 * a2),))
            for j, l in enumerate(["Mandamiento", "de pago", "notificado"]):
                lw = d.textlength(l, font=fl); d.text((mid - lw / 2, y + 44 + j * 50), l, font=fl, fill=YEL + (int(255 * a2),))
        if reset > 0: d.text((W / 2 - 220, 800), "↻ el conteo vuelve a empezar", font=F("r", 34), fill=MINT + (int(255 * min(reset * 2, 1)),))
        d.text((140, 320), "Prescripción", font=F("b", 62), fill=WHITE)
    elif ty == "cierre":
        guide(f, [(POSE[2], 1)], W / 2 + 60, 1560, 1000, tt, k, slide=1, seed=seed)
        a = ease(k / 0.6); lg = LOGO.resize((int(LOGO.width * 1.9 * pop(k)), int(LOGO.height * 1.9 * pop(k))), Image.BILINEAR)
        d = ImageDraw.Draw(f, "RGBA"); rr(d, [W / 2 - 360, 250, W / 2 + 360, 250 + int(LOGO.height * 1.9) + 40], 40, fill=PET + (int(225 * a),))
        f.paste(lg.convert("RGB"), (int(W / 2 - lg.width / 2), 270 + int((LOGO.height * 1.9 - lg.height) / 2)), lg.getchannel("A").point(lambda v: int(v * a)))
    d = ImageDraw.Draw(f, "RGBA")
    if s.get("chip") and ty != "cierre": chip(d, s["chip"], min(ease(k / 0.35), 1 - ease((tt - x["b"] + 0.25) / 0.25)))
    return f

def zoom(img, z, cy=0.45):
    if abs(z - 1) < 1e-4: return img
    w, h = int(W / z), int(H / z); x = (W - w) // 2; y = int((H - h) * cy)
    return img.crop((x, y, x + w, y + h)).resize((W, H), Image.BILINEAR)

def cam(x, tt):
    p = (tt - x["a"]) / (x["b"] - x["a"]); return 1 + 0.045 * (p if x["cam"] == "in" else 1 - p)

XF = 0.2
def frame(tt):
    i = next(j for j, x in enumerate(TL) if tt < x["b"] or j == len(TL) - 1); x = TL[i]; k = tt - x["a"]
    f = zoom(draw_seg(x, tt), cam(x, tt) + (0.07 * (1 - ease(k / 0.35)) if i and x["trans"] == "punch" else 0))
    if i and x["trans"] == "punch" and k < XF:
        f = Image.blend(zoom(draw_seg(TL[i - 1], tt), cam(TL[i - 1], TL[i - 1]["b"]) + 0.04 * ease(k / XF)), f, ease(k / XF))
    elif i and x["trans"] == "barrido" and k < 0.3:
        e = ease(k / 0.3); prev = zoom(draw_seg(TL[i - 1], tt), cam(TL[i - 1], TL[i - 1]["b"])); c = Image.new("RGB", (W, H))
        c.paste(prev, (int(-W * e), 0)); c.paste(f, (int(W * (1 - e)), 0)); f = c
    d = ImageDraw.Draw(f, "RGBA")
    if x["seg"]["tipo"] == "cierre":
        a = ease((tt - x["vstart"]) / 0.5); fnt = font("b", 92); s = "lamulta.com.co"; tw = d.textlength(s, font=fnt)
        rr(d, [W / 2 - tw / 2 - 50, 1570, W / 2 + tw / 2 + 50, 1720], 34, fill=YEL + (int(255 * a),))
        d.text((W / 2 - tw / 2, 1595), s, font=fnt, fill=PET + (int(255 * a),))
        fd = font("r", 28); dw = d.textlength(DISCLAIMER, font=fd); d.text((W / 2 - dw / 2, 1770), DISCLAIMER, font=fd, fill=MUTED + (int(255 * a),))
        return f
    for a, b, lines in SUBS2:
        if a <= tt < b:
            fnt = font("s", 50); y = 1600 if len(lines) == 2 else 1636
            mw = max(d.textlength(l, font=fnt) for l in lines)
            rr(d, [W / 2 - mw / 2 - 34, y - 22, W / 2 + mw / 2 + 34, y + 66 * len(lines) + 12], 26, fill=(5, 20, 27, 205))
            for j, l in enumerate(lines):
                lw = d.textlength(l, font=fnt); d.text((W / 2 - lw / 2, y + j * 66), l, font=fnt, fill=(255, 255, 255, 255))
    return f

# ---------- audio ----------
def music(path, sr=48000):
    n = int(NDUR * sr); tt = np.arange(n) / sr; L = np.zeros(n); R = np.zeros(n)
    prog = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]; beat = 60 / 100; bar = 4 * beat
    for kb in range(int(NDUR / bar) + 1):
        ch = prog[kb % 4]; s0 = int(kb * bar * sr)
        if s0 >= n: break
        s1 = min(n, int((kb + 1) * bar * sr + 0.8 * sr)); u = tt[s0:s1] - kb * bar
        env = np.minimum(u / 0.3, 1) * np.exp(-np.maximum(u - bar, 0) * 4)
        for j, m in enumerate(ch + [ch[0] - 12]):
            fq = 440 * 2 ** ((m - 69) / 12); w = (np.sin(2 * np.pi * fq * u) + 0.2 * np.sin(4 * np.pi * fq * u)) * env * 0.035
            L[s0:s1] += w * (0.7 if j % 2 else 1); R[s0:s1] += w * (1 if j % 2 else 0.7)
        for q in range(8):
            a0 = s0 + int(q * beat / 2 * sr); a1 = min(n, a0 + int(0.5 * sr))
            if a0 >= n: break
            u2 = tt[a0:a1] - tt[a0]; m = ch[[0, 1, 2, 1][q % 4]] + 12; fq = 440 * 2 ** ((m - 69) / 12)
            pp = np.sin(2 * np.pi * fq * u2) * np.exp(-u2 * 9) * 0.03; L[a0:a1] += pp * (1 - q % 2 * .4); R[a0:a1] += pp * (.6 + q % 2 * .4)
        for q in range(4):
            a0 = s0 + int(q * beat * sr); a1 = min(n, a0 + int(0.25 * sr))
            if a0 >= n: break
            u3 = tt[a0:a1] - tt[a0]; fk = 50 + 70 * np.exp(-u3 * 30)
            kk = np.sin(2 * np.pi * np.cumsum(fk) / sr) * np.exp(-u3 * 14) * 0.08; L[a0:a1] += kk; R[a0:a1] += kk
    rng = np.random.default_rng(1)
    for x in TL[1:]:
        m = int(0.45 * sr); a0 = min(int(max(x["a"] - 0.25, 0) * sr), n - m); u = np.linspace(0, 1, m)
        nz = np.convolve(rng.standard_normal(m), np.ones(24) / 24, "same") * np.sin(np.pi * u) ** 2 * 0.1
        L[a0:a0 + m] += nz * (0.6 + 0.4 * u); R[a0:a0 + m] += nz * (1 - 0.4 * u)
    fade = np.ones(n); fi, fo = int(0.3 * sr), int(1.8 * sr); fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0, fo)
    st = np.stack([L * fade, R * fade], 1); st = st / np.abs(st).max() * 0.3
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((st * 32767).astype("<i2").tobytes())

def voice(path):
    fl = [f"[0:a]asplit={len(TL)}" + "".join(f"[s{k}]" for k in range(len(TL)))]
    for k, x in enumerate(TL):
        a = x["va"] - (0.06 if k else 0); b = x["vb"] + 0.12
        fl.append(f"[s{k}]atrim={max(a, 0):.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=out:st={b - a - 0.05:.3f}:d=0.05,aresample=48000,adelay={int(x['vstart'] * 1000)}:all=1[v{k}]")
    fl.append("".join(f"[v{k}]" for k in range(len(TL))) + f"amix=inputs={len(TL)}:normalize=0:duration=longest,pan=stereo|c0=c0|c1=c0,apad[o]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3), "-filter_complex", ";".join(fl),
                    "-map", "[o]", "-t", f"{NDUR}", "-ar", "48000", str(path)], check=True, timeout=120)

def srt(path):
    fm = lambda x: f"{int(x // 3600):02d}:{int(x // 60 % 60):02d}:{int(x % 60):02d},{int(round(x * 1000)) % 1000:03d}"
    Path(path).write_text("\n".join(f"{n}\n{fm(a)} --> {fm(b)}\n" + "\n".join(l) + "\n" for n, (a, b, l) in enumerate(SUBS2, 1)), encoding="utf-8")

if __name__ == "__main__":
    print(f"{slug}: {NDUR:.1f}s, {len(SUBS2)} subtítulos")
    if STILLS:
        from PIL import Image as I
        ts = [x["a"] + (x["b"] - x["a"]) * 0.6 for x in TL]; ims = [frame(t).resize((270, 480)) for t in ts]
        c = I.new("RGB", (270 * len(ims), 480))
        for j, im in enumerate(ims): c.paste(im, (j * 270, 0))
        c.save(OUT / f"{slug}-contact.jpg"); sys.exit()
    music(OUT / f"{slug}-musica.wav"); voice(OUT / f"{slug}-voz.wav"); srt(OUT / f"{slug}.srt")
    vid = OUT / f"{slug}-noaudio.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high", str(vid)], stdin=subprocess.PIPE)
    for k in range(int(NDUR * FPS)): p.stdin.write(frame(k / FPS).tobytes())
    p.stdin.close(); p.wait()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(vid), "-i", str(OUT / f"{slug}-musica.wav"), "-i", str(OUT / f"{slug}-voz.wav"), "-filter_complex",
                    "[1:a]volume=0.6[m];[2:a]asplit=2[v][sc];[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=30:release=300[md];"
                    "[md][v]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart",
                    str(OUT / f"{slug}.mp4")], check=True)
    vid.unlink(); print("listo", OUT / f"{slug}.mp4")
