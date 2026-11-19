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

/** Dispositivo encontrado en la red local (misma subred). */
data class ConnectedDevice(
    val ipAddress: String,
    val hostName: String?,
    val macAddress: String?,
    val vendor: String?,
    val isGateway: Boolean = false,
    val isThisDevice: Boolean = false,
    val responseTimeMs: Long? = null,
) {
    val displayName: String
        get() = when {
            isGateway -> "Router / Puerta de enlace"
            isThisDevice -> "Este teléfono"
            !hostName.isNullOrBlank() && hostName != ipAddress -> hostName
            !vendor.isNullOrBlank() -> vendor
            else -> "Dispositivo"
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
