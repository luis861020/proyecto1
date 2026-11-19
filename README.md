# RedWiFi — Gestor y analizador de redes WiFi

Aplicación Android nativa (**Kotlin + Jetpack Compose + Material 3**) para analizar y
gestionar tu red WiFi con una interfaz moderna. Pensada para administrar **tu propia
red** (uso legítimo de inventario y diagnóstico).

## ✨ Funciones

| Módulo | Qué hace |
|--------|----------|
| 📶 **Redes** | Escanea redes cercanas: SSID, canal, banda (2.4/5/6 GHz), tipo de seguridad, intensidad (RSSI en dBm y %), distancia estimada y BSSID. Muestra la red conectada. |
| 📈 **Medidor de señal** | Medidor circular animado en vivo con historial de RSSI, velocidad de enlace, canal, banda e IP. |
| 📡 **Radar espacial** | Ubica cada red alrededor de ti según su **distancia estimada** respecto al punto central, con anillos de distancia y barrido animado. Toca un punto para ver detalles. |
| 🖥️ **Dispositivos** | Descubre los equipos conectados a tu red local (barrido de subred con ping + ARP): IP, nombre, MAC y fabricante. |
| 📊 **Herramientas** | Recomendador del mejor canal 2.4 GHz (1/6/11), histograma de ocupación de canales y auditoría de seguridad (redes abiertas, WEP, WPS). |

## 📐 Cómo se estima la distancia

Se usa el modelo log-distancia de pérdida de propagación:

```
d = 10 ^ ((P@1m − RSSI) / (10 · n))
```

donde `P@1m` es la potencia de referencia a 1 m y `n` el exponente de pérdida
(~2.8 en interiores). **Es una aproximación**: paredes e interferencias alteran el
resultado. Sirve para ubicar de forma relativa, no como un metro exacto.

## ⚠️ Nota honesta sobre "desconectar dispositivos"

Una app Android normal **no puede expulsar por la fuerza** a otro equipo de una red
WiFi: eso requeriría enviar tramas de *de-autenticación*, que el sistema bloquea por
seguridad (sólo posible con root y hardware especial). La forma **real y legítima** de
bloquear o desconectar a alguien de *tu* red es desde el **panel de administración del
router** (filtrado MAC / lista de bloqueo). La app lo explica y te lleva directamente
a ese panel.

## 🔐 Permisos

- `ACCESS_FINE_LOCATION` / `NEARBY_WIFI_DEVICES` (Android 13+): **exigidos por Android**
  para leer los resultados del escaneo WiFi. La app no rastrea tu ubicación.
- `ACCESS_WIFI_STATE`, `CHANGE_WIFI_STATE`, `INTERNET`: escanear y sondear la red local.

## 🏗️ Compilar el APK

### Opción A — Automático con GitHub Actions (sin instalar nada)
Cada push ejecuta el workflow `.github/workflows/android.yml`, que compila el APK de
depuración y lo publica como **artefacto descargable**:
1. Entra en la pestaña **Actions** del repositorio.
2. Abre la última ejecución de *"Compilar APK"*.
3. Descarga el artefacto **`RedWiFi-debug-apk`**.
4. Copia el `.apk` a tu teléfono e instálalo (activa "orígenes desconocidos").

### Opción B — Local con Android Studio
Abre el proyecto en Android Studio (Ladybug o superior) y pulsa *Run*, o por terminal:

```bash
./gradlew assembleDebug
# APK en: app/build/outputs/apk/debug/app-debug.apk
```

## 🧱 Arquitectura

```
domain/        Modelos y matemática de señal (puro Kotlin, sin Android)
data/wifi/     WifiScanner, analizador de canales, auditoría de seguridad
data/net/      Escáner de dispositivos (subred), OUI de fabricantes, router
ui/            Tema Material 3, navegación y pantallas (MVVM con ViewModels)
```

- **Requisitos:** Android 7.0 (API 24) o superior. `compileSdk` 35.
- **UI:** Jetpack Compose + Material 3 (con color dinámico / Material You en Android 12+).

## 📄 Licencia

Ver [LICENSE](LICENSE).
