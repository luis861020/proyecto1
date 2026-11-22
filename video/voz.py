#!/usr/bin/env python3
"""Genera la locución con ElevenLabs (voz Lina), la ubica por escena y retemporiza el SRT.

Uso: python3 video/voz.py <carpeta salida>
La clave la inyecta el proxy del entorno (encabezado xi-api-key); no se guarda aquí.
Produce: voz-XX.mp3, voz.wav (pista completa de 70 s) y Subtitulos-LaMulta-voz.srt
"""
import base64, json, re, subprocess, sys, urllib.request
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
VOICE = "yfUfwZTRubVrsUZWqzwp"  # Lina - Colombian Warm & Confident
SRT = Path(__file__).with_name("Subtitulos-LaMulta.srt")
DUR = 70.0

# (inicio escena, fin escena, bloques SRT, texto hablado)
SCENES = [
    (0, 7, [1, 2], None), (7, 16, [3, 4], None), (16, 24, [5], None), (24, 39, [6, 7, 8], None),
    (39, 54, [9, 10], None), (54, 64, [11, 12], None),
    (64, 70, [13], "Empieza con tu documento en lamulta punto com punto co."),
]
LEAD = 0.35  # silencio al inicio de cada escena

def parse_srt(p):
    out = []
    for b in re.split(r"\n\s*\n", p.read_text(encoding="utf-8").strip()):
        L = b.strip().splitlines(); out.append(L[2:])
    return out

def fmt(t):
    ms = int(round(t * 1000)); return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

def tts(text):
    body = json.dumps({"text": text, "model_id": "eleven_multilingual_v2", "language_code": "es",
                       "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.2}}).encode()
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}/with-timestamps?output_format=mp3_44100_128",
                                 data=body, headers={"Content-Type": "application/json", "xi-api-key": "proxy-injected"})
    d = json.load(urllib.request.urlopen(req, timeout=120))
    return base64.b64decode(d["audio_base64"]), d["alignment"]

def dur(f): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]))

blocks = parse_srt(SRT); srt_out = []; inputs = []; filt = []
for i, (a, b, ids, spoken) in enumerate(SCENES, 1):
    lines = [blocks[k - 1] for k in ids]
    text = spoken or " ".join(" ".join(l) for l in lines)
    mp3 = OUT / f"voz-{i:02d}.mp3"; al_f = OUT / f"voz-{i:02d}.json"
    if not mp3.exists():
        audio, al = tts(text); mp3.write_bytes(audio); al_f.write_text(json.dumps(al))
    al = json.loads(al_f.read_text()); d = dur(mp3)
    slot = (b - a) - LEAD - 0.25
    tempo = max(1.0, d / slot)  # acelera solo si no cabe
    if tempo > 1.12: print(f"AVISO escena {i}: requiere tempo {tempo:.2f}")
    starts, ends = al["character_start_times_seconds"], al["character_end_times_seconds"]
    # tiempo de cada bloque SRT según el carácter donde empieza
    pos = 0; t0s = []
    for l in lines:
        t0s.append(starts[min(pos, len(starts) - 1)]); pos += len(" ".join(l)) + 1
    for j, l in enumerate(lines):
        s = a + LEAD + t0s[j] / tempo - (0.05 if j else LEAD)
        e = a + LEAD + (t0s[j + 1] / tempo - 0.05 if j + 1 < len(lines) else max(ends) / tempo + 0.4)
        e = b if j + 1 == len(lines) else e
        srt_out.append((s, e, l))
    print(f"escena {i}: {d:.2f}s en hueco de {slot:.2f}s, tempo {tempo:.2f}")
    inputs += ["-i", str(mp3)]
    filt.append(f"[{i - 1}:a]atempo={tempo:.4f},aresample=48000,adelay={int((a + LEAD) * 1000)}:all=1[v{i}]")

(OUT / "Subtitulos-LaMulta-voz.srt").write_text(
    "\n".join(f"{n}\n{fmt(s)} --> {fmt(e)}\n" + "\n".join(l) + "\n" for n, (s, e, l) in enumerate(srt_out, 1)), encoding="utf-8")
mix = "".join(f"[v{i}]" for i in range(1, len(SCENES) + 1))
filt.append(f"{mix}amix=inputs={len(SCENES)}:normalize=0,pan=stereo|c0=c0|c1=c0,apad,atrim=0:{DUR},loudnorm=I=-16:TP=-1.5:LRA=11[out]")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filt), "-map", "[out]", "-ar", "48000", str(OUT / "voz.wav")], check=True)
print("voz.wav listo")
