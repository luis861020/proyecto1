package com.redwifi.gestor.data.wifi

import android.annotation.SuppressLint
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.net.wifi.ScanResult
import android.net.wifi.WifiManager
import androidx.core.content.ContextCompat
import com.redwifi.gestor.domain.SignalMath
import com.redwifi.gestor.domain.model.Band
import com.redwifi.gestor.domain.model.CurrentConnection
import com.redwifi.gestor.domain.model.Security
import com.redwifi.gestor.domain.model.WifiNetwork
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

/**
 * Acceso al subsistema WiFi del dispositivo. Encapsula [WifiManager] y expone
 * resultados ya convertidos a modelos de dominio.
 */
class WifiScanner(context: Context) {

    private val appContext = context.applicationContext
    private val wifiManager =
        appContext.getSystemService(Context.WIFI_SERVICE) as WifiManager

    fun isWifiEnabled(): Boolean = wifiManager.isWifiEnabled

    /** Pide al sistema un nuevo escaneo. Puede estar limitado (throttling) por Android. */
    fun requestScan(): Boolean = try {
        @Suppress("DEPRECATION")
        wifiManager.startScan()
    } catch (e: Exception) {
        false
    }

    /** Lee el último conjunto de resultados de escaneo disponible. */
    @SuppressLint("MissingPermission")
    fun readScanResults(): List<WifiNetwork> {
        val currentBssid = currentConnection()?.bssid
        return try {
            wifiManager.scanResults
                .map { it.toWifiNetwork(currentBssid) }
                .sortedWith(compareByDescending<WifiNetwork> { it.isCurrent }.thenByDescending { it.rssi })
        } catch (e: SecurityException) {
            emptyList()
        } catch (e: Exception) {
            emptyList()
        }
    }

    /** Información de la red a la que estamos conectados ahora mismo. */
    @SuppressLint("MissingPermission")
    @Suppress("DEPRECATION")
    fun currentConnection(): CurrentConnection? {
        return try {
            val info = wifiManager.connectionInfo ?: return null
            val rawSsid = info.ssid?.removeSurrounding("\"") ?: ""
            if (info.networkId == -1 && (info.bssid == null || info.bssid == "02:00:00:00:00:00")) {
                return null
            }
            CurrentConnection(
                ssid = if (rawSsid == "<unknown ssid>") "" else rawSsid,
                bssid = info.bssid,
                rssi = info.rssi,
                linkSpeedMbps = info.linkSpeed,
                frequencyMhz = info.frequency,
                ipAddress = formatIp(info.ipAddress),
            )
        } catch (e: Exception) {
            null
        }
    }

    /**
     * Flujo reactivo que emite la lista de redes. Se refresca cuando el sistema
     * avisa de un nuevo escaneo y fuerza re-escaneos periódicos.
     */
    fun networksFlow(intervalMs: Long = 10_000L): Flow<List<WifiNetwork>> = callbackFlow {
        val receiver = object : BroadcastReceiver() {
            override fun onReceive(c: Context?, intent: Intent?) {
                trySend(readScanResults())
            }
        }
        val filter = IntentFilter(WifiManager.SCAN_RESULTS_AVAILABLE_ACTION)
        ContextCompat.registerReceiver(
            appContext, receiver, filter, ContextCompat.RECEIVER_NOT_EXPORTED
        )

        trySend(readScanResults())
        requestScan()

        val ticker = launch {
            while (isActive) {
                delay(intervalMs)
                requestScan()
                trySend(readScanResults())
            }
        }

        awaitClose {
            runCatching { appContext.unregisterReceiver(receiver) }
            ticker.cancel()
        }
    }

    @Suppress("DEPRECATION")
    private fun ScanResult.toWifiNetwork(currentBssid: String?): WifiNetwork {
        val freq = frequency
        val caps = capabilities ?: ""
        return WifiNetwork(
            ssid = SSID ?: "",
            bssid = BSSID ?: "",
            rssi = level,
            frequencyMhz = freq,
            channel = SignalMath.channelFromFrequency(freq),
            band = Band.fromFrequency(freq),
            security = Security.fromCapabilities(caps),
            hasWps = Security.hasWps(caps),
            capabilities = caps,
            isCurrent = currentBssid != null && currentBssid == BSSID,
        )
    }

    private fun formatIp(ip: Int): String? {
        if (ip == 0) return null
        return "%d.%d.%d.%d".format(
            ip and 0xff,
            ip shr 8 and 0xff,
            ip shr 16 and 0xff,
            ip shr 24 and 0xff,
        )
    }
}
