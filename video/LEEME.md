# Video LaMulta (vertical, 70 s)

- `lamulta-vertical.mp4`: 1080×1920, 9:16, 30 fps, H.264 + AAC estéreo 48 kHz. Subtítulos y rótulos incrustados, música instrumental discreta.
- `musica.wav`: pista de música sola, para mezclar con la locución.
- `render.py`: regenera el video. `python3 video/render.py <carpeta LaMulta-video> <salida>` (requiere Pillow, numpy y ffmpeg).
- `Subtitulos-LaMulta.srt` y `Guion-grafico-LaMulta.md`: material original del paquete.

## Pendiente antes de publicar

1. **Locución**: el video aún no tiene voz. Grabar la voz (español de Colombia, 125–140 ppm) siguiendo el SRT y mezclar:
   `ffmpeg -i lamulta-vertical.mp4 -i voz.wav -filter_complex "[0:a]volume=0.6[m];[m][1:a]amix=inputs=2:duration=first[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -ar 48000 final.mp4`
2. **Pantallas simuladas** (datos ficticios, estilo de la interfaz real): correo y código, revisión del escrito, elección de plan/Wompi, estado de revisión jurídica y Mi expediente. Reemplazar por capturas reales del entorno de pruebas cuando existan. Los nombres de plan son de ejemplo y no se muestra importe.
3. Revisar el MP4 completo en celular y computador.
