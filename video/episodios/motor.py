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

def draw_seg(x, tt):
    s = x["seg"]; k = tt - x["a"]; p = k / (x["b"] - x["a"]); f = bg(tt); ty = s["tipo"]
    if ty == "guia":
        paste_guide(f, POSE[s.get("pose", 0)], W / 2, 1600, 1250, tt)
    elif ty in ("lupa", "carpeta"):
        fr = LUPA if ty == "lupa" else CARP
        paste_guide(f, fr[int(tt * 3) % 4], W / 2, 1580, 1200, tt, breathe=False)
    elif ty == "tarjeta":
        paste_guide(f, POSE[s.get("pose", 1)], W / 2 + 40, 1580, 900, tt)
        d = ImageDraw.Draw(f, "RGBA"); a = ease(k / 0.4)
        y0 = 260 + 40 * (1 - a); rr(d, [70, y0, W - 70, y0 + 560], 48, fill=SURF + (int(238 * a),), outline=LINE + (int(255 * a),), width=3)
        big = s["grande"]; fs = 200 if len(big) <= 8 else (150 if len(big) <= 12 else 116)
        fb = font("b", fs); bw = d.textlength(big, font=fb)
        sc = 1 + 0.12 * (1 - ease(k / 0.5))
        d.text((W / 2 - bw / 2, y0 + 70 + (200 - fs) * 0.4), big, font=fb, fill=YEL + (int(255 * a),))
        fl = font("s", 52); ls = wrap(d, s["texto"], fl, W - 220)
        for j, l in enumerate(ls[:3]):
            lw = d.textlength(l, font=fl); d.text((W / 2 - lw / 2, y0 + 330 + j * 68), l, font=fl, fill=WHITE + (int(255 * a),))
    elif ty == "linea":
        paste_guide(f, POSE[1], W / 2 + 40, 1580, 820, tt)
        d = ImageDraw.Draw(f, "RGBA"); rr(d, [60, 260, W - 60, 900], 48, fill=SURF + (238,), outline=LINE, width=3)
        x0, x1, y = 140, W - 140, 560
        d.line([(x0, y), (x1, y)], fill=LINE, width=14)
        g = ease(p / 0.45); mid = x0 + (x1 - x0) * 0.55
        reset = ease((p - 0.5) / 0.35)
        if reset <= 0:
            d.line([(x0, y), (x0 + (x1 - x0) * g * 0.55, y)], fill=MINT, width=14)
        else:
            d.line([(x0, y), (mid, y)], fill=(90, 120, 128), width=14)
            d.line([(mid, y), (mid + (x1 - mid) * reset, y)], fill=MINT, width=14)
        fl, fs_ = font("s", 40), font("r", 34)
        d.ellipse([x0 - 22, y - 22, x0 + 22, y + 22], fill=MINT); d.text((x0 - 40, y + 44), "Infracción", font=fl, fill=WHITE)
        d.text((x1 - 150, y - 110), "3 años", font=font("b", 58), fill=YEL)
        if p > 0.38:
            a2 = ease((p - 0.38) / 0.12)
            d.ellipse([mid - 26, y - 26, mid + 26, y + 26], fill=YEL + (int(255 * a2),))
            for j, l in enumerate(["Mandamiento", "de pago", "notificado"]):
                lw = d.textlength(l, font=fl); d.text((mid - lw / 2, y + 44 + j * 50), l, font=fl, fill=YEL + (int(255 * a2),))
        if reset > 0:
            d.text((W / 2 - 220, 800), "↻ el conteo vuelve a empezar", font=fs_, fill=MINT + (int(255 * min(reset * 2, 1)),))
        d.text((140, 320), "Prescripción", font=font("b", 62), fill=WHITE)
    elif ty == "cierre":
        paste_guide(f, POSE[2], W / 2 + 60, 1560, 1000, tt)
        a = ease(k / 0.6); lg = LOGO.resize((int(LOGO.width * 1.9), int(LOGO.height * 1.9)), Image.LANCZOS)
        d = ImageDraw.Draw(f, "RGBA"); rr(d, [W / 2 - 360, 250, W / 2 + 360, 250 + lg.height + 40], 40, fill=PET + (int(225 * a),))
        f.paste(lg.convert("RGB"), (int(W / 2 - lg.width / 2), 270), lg.getchannel("A").point(lambda v: int(v * a)))
    d = ImageDraw.Draw(f, "RGBA")
    if s.get("chip") and ty != "cierre": chip(d, s["chip"], min(ease(k / 0.35), 1 - ease((tt - x["b"] + 0.25) / 0.25)))
    return f

def zoom(img, z, cy=0.45):
    if abs(z - 1) < 1e-4: return img
    w, h = int(W / z), int(H / z); x = (W - w) // 2; y = int((H - h) * cy)
    return img.crop((x, y, x + w, y + h)).resize((W, H), Image.BILINEAR)

XF = 0.2
def frame(tt):
    i = next(j for j, x in enumerate(TL) if tt < x["b"] or j == len(TL) - 1); x = TL[i]; k = tt - x["a"]
    p = k / (x["b"] - x["a"])
    f = zoom(draw_seg(x, tt), 1 + 0.03 * p + (0.07 * (1 - ease(k / 0.35)) if i else 0))
    if i and k < XF: f = Image.blend(zoom(draw_seg(TL[i - 1], tt), 1.03 + 0.04 * ease(k / XF)), f, ease(k / XF))
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
    fl = []
    for k, x in enumerate(TL):
        a = x["va"] - (0.06 if k else 0); b = x["vb"] + 0.12
        fl.append(f"[0:a]atrim={max(a, 0):.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=out:st={b - a - 0.05:.3f}:d=0.05,aresample=48000,adelay={int(x['vstart'] * 1000)}:all=1[v{k}]")
    fl.append("".join(f"[v{k}]" for k in range(len(TL))) + f"amix=inputs={len(TL)}:normalize=0,pan=stereo|c0=c0|c1=c0,apad,atrim=0:{NDUR}[o]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3), "-filter_complex", ";".join(fl),
                    "-map", "[o]", "-ar", "48000", str(path)], check=True)

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
