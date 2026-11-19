package com.redwifi.gestor.domain

import kotlin.math.pow
import kotlin.math.roundToInt

/**
 * Funciones puras (sin dependencias de Android) para interpretar señales WiFi.
 * Al ser puras, son fáciles de probar y razonar.
 */
object SignalMath {

    /** Convierte RSSI (dBm) a un porcentaje 0-100 con un mapeo lineal estándar. */
    fun rssiToPercent(rssi: Int): Int = when {
        rssi <= -100 -> 0
        rssi >= -50 -> 100
        else -> 2 * (rssi + 100)
    }

    /** Cuatro niveles de barras (0-4) a partir del RSSI. */
    fun rssiToBars(rssi: Int): Int = when {
        rssi >= -55 -> 4
        rssi >= -67 -> 3
        rssi >= -78 -> 2
        rssi >= -88 -> 1
        else -> 0
    }

    /**
     * Estima la distancia al emisor con el modelo log-distancia de pérdida de propagación:
     *   d = 10 ^ ((TxPower@1m - RSSI) / (10 * n))
     *
     * Es una APROXIMACIÓN: paredes, interferencias y la potencia real del router
     * cambian el resultado. Sirve para ubicar relativamente, no como metro láser.
     *
     * @param txPowerAt1m potencia de referencia medida a 1 metro (dBm).
     * @param n exponente de pérdida (2.0 espacio libre, 2.7-3.5 interiores).
     */
    fun rssiToDistanceMeters(
        rssi: Int,
        frequencyMhz: Int,
        txPowerAt1m: Int = defaultTxPower(frequencyMhz),
        n: Double = 2.8,
    ): Double {
        val exponent = (txPowerAt1m - rssi) / (10.0 * n)
        val d = 10.0.pow(exponent)
        return d.coerceIn(0.1, 500.0)
    }

    /** Referencia a 1 m: la banda de 5/6 GHz se atenúa algo más que 2.4 GHz. */
    private fun defaultTxPower(frequencyMhz: Int): Int = when {
        frequencyMhz >= 5925 -> -45
        frequencyMhz >= 4900 -> -43
        else -> -40
    }

    /** Número de canal a partir de la frecuencia central en MHz. */
    fun channelFromFrequency(freqMhz: Int): Int = when {
        freqMhz == 2484 -> 14
        freqMhz in 2412..2472 -> (freqMhz - 2407) / 5
        freqMhz in 5160..5900 -> (freqMhz - 5000) / 5
        freqMhz in 5925..7125 -> (freqMhz - 5950) / 5
        else -> -1
    }

    fun formatDistance(meters: Double): String = when {
        meters < 1.0 -> "< 1 m"
        meters < 10.0 -> "${(meters * 10).roundToInt() / 10.0} m"
        else -> "${meters.roundToInt()} m"
    }
}
