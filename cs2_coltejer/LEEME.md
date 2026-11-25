# Edificio Coltejer (Medellín): asset para Cities: Skylines II

![Día, aguja y noche](vistas.jpg)

Rascacielos emblemático de Medellín: torre de oficinas de concreto con aletas verticales continuas, coronada por la "aguja" con su ojo, sobre un podio comercial con soportal de granito.

## Qué es dato y qué es interpretación

| Elemento | Valor | Origen |
|---|---|---|
| Altura total | 175 m | Dato publicado |
| Plantas | 36 (2 de podio + 34 de torre) | Dato publicado (algunas fuentes dicen 37) |
| Remate en forma de aguja con ojo | Sí | Dato publicado |
| Estilo brutalista, de concreto, con líneas verticales | Sí | Descrito en fuentes turísticas |
| Granito rosa en el podio | Sí | Fuente turística, sin confirmar |
| Planta de la torre de 45 × 20 m, plantas de 3,75 m | — | **Aproximación** (cuadra con los ~42.000 m² construidos) |
| Aguja: arco ojival de 45 m de luz y 12 m de espesor, desde 139,3 m | — | **Aproximación** |
| Forma y tamaño del ojo, podio de 60 × 44 m con soportal, terraza | — | **Aproximación** |

No he tenido acceso a planos ni a fotos. Si me pasas imágenes de referencia o medidas (por ejemplo, la planta real o el ancho de las fachadas), ajusto el modelo. Todas las cotas están al principio de `fuente/modelo_coltejer.py`.

## Detalles del modelo

| | |
|---|---|
| Parcela | 8 × 6 celdas (64 m × 48 m); calle en el lado de los locales |
| LOD0 | 3.042 triángulos: aletas, antepechos, pilares de esquina, aguja con ojo, pararrayos, baliza roja, soportal, marquesina, jardineras y claraboyas |
| LOD1 | 1.134 triángulos: fachadas planas, aguja simplificada, sin aletas |
| LOD2 | 148 triángulos: volúmenes básicos |
| Texturas | Atlas de 4096 × 4096 px |
| Noche | `_Emissive` con luz en ~45 % de las oficinas (8 variantes por planta para que no se repita), locales y letreros encendidos, aguja iluminada y baliza roja en la punta |

## Archivos

```
CO_EdificioColtejer_8x6/
  CO_EdificioColtejer_8x6.fbx  /  _LOD1.fbx  /  _LOD2.fbx
  CO_EdificioColtejer_8x6_BaseColor.png
  CO_EdificioColtejer_8x6_Normal.png     (OpenGL, Y+)
  CO_EdificioColtejer_8x6_MaskMap.png    (R metálico, G oclusión, B 0, A suavidad)
  CO_EdificioColtejer_8x6_Emissive.png
fuente/
  texturas_coltejer.py   genera el atlas
  modelo_coltejer.py     construye el modelo, exporta los FBX y hace los renders
```

Las mallas están en metros con Y hacia arriba y el origen en el centro de la parcela, a ras de suelo.

## Importarlo en el juego

1. Copia la carpeta `CO_EdificioColtejer_8x6` a tu carpeta de proyecto del importador de assets.
2. En el **editor de assets**, abre **Asset Importer**, selecciona la carpeta e impórtala. Las texturas se asignan por el nombre, y los sufijos distinguen mayúsculas.
3. Úsalo como **edificio emblemático (signature)** o como **oficinas de alta densidad**, con parcela de 8 × 6.
4. Comprueba que los locales miran a la calle (si no, gíralo 180°) y que los LOD1 y LOD2 quedan asociados.
5. Guárdalo, pruébalo de día y de noche, y publícalo en **Paradox Mods** si quieres compartirlo.

**Por revisar en el juego:**
- **MaskMap:** sigue la convención de Unity HDRP. No he podido confirmar cuál espera CS2.
- **Emissive:** no sé qué intensidad aplica CS2 a esta textura. Si de noche brilla demasiado o muy poco, cambia la intensidad de las luces en `texturas_coltejer.py`.

## Regenerar

Necesitas `pip install bpy numpy pillow` (Python 3.11+).

```
python fuente/texturas_coltejer.py CO_EdificioColtejer_8x6 CO_EdificioColtejer_8x6
python fuente/modelo_coltejer.py   CO_EdificioColtejer_8x6 CO_EdificioColtejer_8x6 render
```
