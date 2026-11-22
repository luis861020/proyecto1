#!/usr/bin/env python3
"""Versión dinámica (≤60 s) del video de LaMulta.

Reutiliza las escenas de render.py y remapea su tiempo a la locución acelerada.
Uso: python3 video/render60.py <carpeta LaMulta-video> <carpeta voz (voz-XX.mp3/.json)> <salida>
"""
import json, math, subprocess, sys, wave
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
PKG, VOZ, OUT = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]); OUT.mkdir(parents=True, exist_ok=True)
sys.argv = ["render.py", PKG, str(OUT), str(HERE / "Subtitulos-LaMulta-voz.srt")]
__file__ = str(HERE / "render.py")
exec(open(HERE / "render.py", encoding="utf-8").read().split('if __name__ == "__main__":')[0])

TEMPO, LEAD, TAIL, HOLD = 1.05, 0.15, 0.30, 2.7
OLD = [(0, 7, 1.07), (7, 16, 1.0), (16, 24, 1.0), (24, 39, 1.0), (39, 54, 1.0), (54, 64, 1.0), (64, 70, 1.0)]
NBLK = [2, 2, 1, 3, 2, 2, 1]
OLD_LEAD = 0.35
blocks = parse_srt(SRT)

def dur(f): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]))

# --- nueva línea de tiempo + anclas (nuevo -> viejo) ---
anchors = [(0.0, 0.0)]; voice_at = []; cuts = []; t = 0.0; bi = 0
for i, (a, b, otempo) in enumerate(OLD, 1):
    mp3 = VOZ / f"voz-{i:02d}.mp3"; al = json.loads((VOZ / f"voz-{i:02d}.json").read_text())
    d = dur(mp3); st = al["character_start_times_seconds"]
    s0 = t; vs = s0 + LEAD; voice_at.append((mp3, vs))
    if i > 1: anchors.append((s0, a)); cuts.append(s0)
    pos = 0
    for j in range(NBLK[i - 1]):
        line = " ".join(blocks[bi + j][2]); t0 = st[min(pos, len(st) - 1)]; pos += len(line) + 1
        if j: anchors.append((vs + t0 / TEMPO - 0.05, a + OLD_LEAD + t0 / otempo - 0.05))
    bi += NBLK[i - 1]
    ve_new, ve_old = vs + d / TEMPO, a + OLD_LEAD + d / otempo
    if i < len(OLD):
        anchors.append((ve_new, ve_old)); t = ve_new + TAIL
        anchors.append((t - 0.001, b - 0.001))
    else:
        anchors.append((vs + 0.3, 64.6)); t = max(ve_new, vs + 0.3) + HOLD; anchors.append((t, 70.0))
NDUR = round(t, 2)
AN = np.array(anchors); assert np.all(np.diff(AN[:, 0]) > 0) and np.all(np.diff(AN[:, 1]) > 0), anchors
def old_t(tn): return float(np.interp(tn, AN[:, 0], AN[:, 1]))
print(f"duración nueva {NDUR:.2f}s, cortes {[round(c, 2) for c in cuts]}")

def scene_of(to):
    for i, (a, b, fn) in enumerate(SCENES):
        if a <= to < b: return i
    return len(SCENES) - 1
NEW_CUTS = [0.0] + [None] * (len(SCENES) - 1)
for k in range(1, len(SCENES)):  # momento (nuevo) en que empieza cada escena visual
    a = SCENES[k][0]; NEW_CUTS[k] = float(np.interp(a, AN[:, 1], AN[:, 0]))

def zoom(img, z, cx=0.5, cy=0.45):
    if abs(z - 1) < 1e-4: return img
    w, h = int(W / z), int(H / z); x = int((W - w) * cx); y = int((H - h) * cy)
    return img.crop((x, y, x + w, y + h)).resize((W, H), Image.BILINEAR)

XF = 0.18
def frame60(tn):
    to = old_t(tn); i = scene_of(to); a_new = NEW_CUTS[i]
    nxt = NEW_CUTS[i + 1] if i + 1 < len(SCENES) else NDUR
    prog = (tn - a_new) / max(nxt - a_new, 0.1)
    f = SCENES[i][2](to)
    k = tn - a_new
    z = 1 + 0.03 * prog + (0.07 * (1 - ease(k / 0.35)) if i > 0 else 0)
    f = zoom(f, z)
    if i > 0 and k < XF:
        prev = zoom(SCENES[i - 1][2](min(to, SCENES[i][0] - 1e-3)), 1.03 + 0.04 * ease(k / XF))
        f = Image.blend(prev, f, ease(k / XF))
    overlays(f, to); return f

def music60(path, sr=48000):
    n = int(NDUR * sr); tt = np.arange(n) / sr; L = np.zeros(n); R = np.zeros(n)
    prog = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]; bpm = 104; beat = 60 / bpm; bar = 4 * beat
    for k in range(int(NDUR / bar) + 1):
        ch = prog[k % 4]; s0 = int(k * bar * sr)
        if s0 >= n: break
        s1 = min(n, int((k + 1) * bar * sr + 0.8 * sr)); u = tt[s0:s1] - k * bar
        env = np.minimum(u / 0.3, 1) * np.exp(-np.maximum(u - bar, 0) * 4)
        for j, m in enumerate(ch + [ch[0] - 12]):
            fq = 440 * 2 ** ((m - 69) / 12); w = (np.sin(2 * np.pi * fq * u) + 0.2 * np.sin(4 * np.pi * fq * u)) * env * 0.035
            L[s0:s1] += w * (0.7 if j % 2 else 1); R[s0:s1] += w * (1 if j % 2 else 0.7)
        for q in range(8):  # arpegio en corcheas
            a0 = s0 + int(q * beat / 2 * sr); a1 = min(n, a0 + int(0.5 * sr))
            if a0 >= n: break
            u2 = tt[a0:a1] - tt[a0]; m = ch[[0, 1, 2, 1][q % 4]] + 12; fq = 440 * 2 ** ((m - 69) / 12)
            p = np.sin(2 * np.pi * fq * u2) * np.exp(-u2 * 9) * 0.03; L[a0:a1] += p * (1 - q % 2 * .4); R[a0:a1] += p * (.6 + q % 2 * .4)
        for q in range(4):  # pulso suave (bombo) en cada tiempo
            a0 = s0 + int(q * beat * sr); a1 = min(n, a0 + int(0.25 * sr))
            if a0 >= n: break
            u3 = tt[a0:a1] - tt[a0]; fk = 50 + 70 * np.exp(-u3 * 30)
            kk = np.sin(2 * np.pi * np.cumsum(fk) / sr) * np.exp(-u3 * 14) * 0.09; L[a0:a1] += kk; R[a0:a1] += kk
    rng = np.random.default_rng(1)
    for c in NEW_CUTS[1:]:  # "whoosh" leve en cada transición
        a0 = int(max(c - 0.25, 0) * sr); m = int(0.45 * sr); a0 = min(a0, n - m)
        u = np.linspace(0, 1, m); env = np.sin(np.pi * u) ** 2
        nz = np.convolve(rng.standard_normal(m), np.ones(24) / 24, "same") * env * 0.10
        L[a0:a0 + m] += nz * (0.6 + 0.4 * u); R[a0:a0 + m] += nz * (1 - 0.4 * u)
    fade = np.ones(n); fi, fo = int(0.3 * sr), int(1.8 * sr); fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0, fo)
    st = np.stack([L * fade, R * fade], 1); st = st / np.abs(st).max() * 0.3
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((st * 32767).astype("<i2").tobytes())

def voice60(path):
    ins, fl = [], []
    for k, (mp3, vs) in enumerate(voice_at):
        ins += ["-i", str(mp3)]; fl.append(f"[{k}:a]atempo={TEMPO},aresample=48000,adelay={int(vs * 1000)}:all=1[v{k}]")
    fl.append("".join(f"[v{k}]" for k in range(len(voice_at))) + f"amix=inputs={len(voice_at)}:normalize=0,pan=stereo|c0=c0|c1=c0,apad,atrim=0:{NDUR}[o]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", ";".join(fl), "-map", "[o]", "-ar", "48000", str(path)], check=True)

def write_srt(path):  # SRT en la nueva línea de tiempo
    tn = np.linspace(0, NDUR, int(NDUR * 100) + 1); to = np.array([old_t(x) for x in tn]); out = []
    for n, (a, b, lines) in enumerate(SUBS, 1):
        s = float(np.interp(a, to, tn)); e = float(np.interp(b, to, tn))
        f = lambda x: f"{int(x // 3600):02d}:{int(x // 60 % 60):02d}:{int(x % 60):02d},{int(round(x * 1000)) % 1000:03d}"
        out.append(f"{n}\n{f(s)} --> {f(e)}\n" + "\n".join(lines) + "\n")
    Path(path).write_text("\n".join(out), encoding="utf-8")

if __name__ == "__main__":
    music60(OUT / "musica60.wav"); voice60(OUT / "voz60.wav"); write_srt(OUT / "Subtitulos-LaMulta-60s.srt")
    if "--stills" in sys.argv[4:] or "--stills" in sys.argv:
        pass
    vid = OUT / "v60-noaudio.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-profile:v", "high", str(vid)], stdin=subprocess.PIPE)
    for k in range(int(NDUR * FPS)):
        p.stdin.write(frame60(k / FPS).tobytes())
        if k % 300 == 0: print(f"{k / FPS:.0f}s", flush=True)
    p.stdin.close(); p.wait()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(vid), "-i", str(OUT / "musica60.wav"), "-i", str(OUT / "voz60.wav"), "-filter_complex",
                    "[1:a]volume=0.6[m];[2:a]asplit=2[v][sc];[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=30:release=300[md];"
                    "[md][v]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart",
                    str(OUT / "lamulta-vertical-60s.mp4")], check=True)
    vid.unlink(); print("listo")
