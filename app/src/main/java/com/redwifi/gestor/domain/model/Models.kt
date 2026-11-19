package com.redwifi.gestor.domain.model

import com.redwifi.gestor.domain.SignalMath

/** Banda de frecuencia de una red. */
enum class Band(val label: String) {
    GHZ_2_4("2.4 GHz"),
    GHZ_5("5 GHz"),
    GHZ_6("6 GHz"),
    UNKNOWN("—");

    companion object {
        fun fromFrequency(freqMhz: Int): Band = when {
            freqMhz in 2400..2500 -> GHZ_2_4
            freqMhz in 4900..5900 -> GHZ_5
            freqMhz in 5925..7125 -> GHZ_6
            else -> UNKNOWN
        }
    }
}

/** Tipo de seguridad detectado en las capacidades de la red. */
enum class Security(val label: String, val isSecure: Boolean) {
    OPEN("Abierta", false),
    WEP("WEP", false),
    WPA("WPA", true),
    WPA2("WPA2", true),
    WPA3("WPA3", true),
    ENTERPRISE("Empresarial", true),
    UNKNOWN("—", true);

    companion object {
        fun fromCapabilities(capabilities: String): Security {
            val c = capabilities.uppercase()
            return when {
                c.contains("WPA3") || c.contains("SAE") -> WPA3
                c.contains("EAP") -> ENTERPRISE
                c.contains("WPA2") || c.contains("RSN") -> WPA2
                c.contains("WPA") -> WPA
                c.contains("WEP") -> WEP
                else -> OPEN
            }
        }

        fun hasWps(capabilities: String): Boolean =
            capabilities.uppercase().contains("WPS")
    }
}

/** Una red WiFi detectada en un escaneo. */
data class WifiNetwork(
    val ssid: String,
    val bssid: String,
    val rssi: Int,
    val frequencyMhz: Int,
    val channel: Int,
    val band: Band,
    val security: Security,
    val hasWps: Boolean,
    val capabilities: String,
    val isCurrent: Boolean = false,
) {
    val displaySsid: String get() = ssid.ifBlank { "(Red oculta)" }
    val signalPercent: Int get() = SignalMath.rssiToPercent(rssi)
    val bars: Int get() = SignalMath.rssiToBars(rssi)
    val estimatedDistanceMeters: Double
        get() = SignalMath.rssiToDistanceMeters(rssi, frequencyMhz)
}

/** Tipo de dispositivo inferido (celular, computador, TV, etc.). */
enum class DeviceType(val label: String) {
    ROUTER("Router"),
    THIS_PHONE("Este teléfono"),
    PHONE("Teléfono / Celular"),
    COMPUTER("Computador"),
    TV("TV / Streaming"),
    CONSOLE("Consola"),
    PRINTER("Impresora"),
    IOT("Smart / IoT"),
    UNKNOWN("Dispositivo"),
}

/** Dispositivo encontrado en la red local (misma subred). */
data class ConnectedDevice(
    val ipAddress: String,
    val hostName: String?,
    val macAddress: String?,
    val vendor: String?,
    val isGateway: Boolean = false,
    val isThisDevice: Boolean = false,
    val responseTimeMs: Long? = null,
    val type: DeviceType = DeviceType.UNKNOWN,
) {
    /** Nombre de host sin sufijos de red (.lan/.local/.home). */
    val cleanHostName: String?
        get() = hostName
            ?.removeSuffix(".lan")
            ?.removeSuffix(".local")
            ?.removeSuffix(".home")
            ?.takeIf { it.isNotBlank() && it != ipAddress }

    val displayName: String
        get() = when {
            isGateway -> "Router / Puerta de enlace"
            isThisDevice -> "Este teléfono"
            !cleanHostName.isNullOrBlank() -> cleanHostName!!
            !vendor.isNullOrBlank() -> vendor!!
            else -> type.label
        }
}

/** Datos de la conexión WiFi activa, para el medidor en vivo. */
data class CurrentConnection(
    val ssid: String,
    val bssid: String?,
    val rssi: Int,
    val linkSpeedMbps: Int,
    val frequencyMhz: Int,
    val ipAddress: String?,
) {
    val channel: Int get() = SignalMath.channelFromFrequency(frequencyMhz)
    val band: Band get() = Band.fromFrequency(frequencyMhz)
    val signalPercent: Int get() = SignalMath.rssiToPercent(rssi)
}
