package com.redwifi.gestor.data.net

import android.annotation.SuppressLint
import android.content.Context
import android.net.wifi.WifiManager
import com.redwifi.gestor.domain.model.ConnectedDevice
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withPermit
import kotlinx.coroutines.withContext
import java.io.File
import java.net.InetAddress
import java.net.NetworkInterface

/** Resultado del descubrimiento de la red local. */
data class ScanOutcome(
    val subnet: String,
    val gatewayIp: String?,
    val devices: List<ConnectedDevice>,
)

/**
 * Descubre los dispositivos conectados a la MISMA red local que este teléfono.
 * Técnica estándar de inventario de red: barrido de la subred con ping (ICMP/TCP
 * echo vía [InetAddress.isReachable]) y resolución de MAC leyendo la tabla ARP.
 *
 * Nota de realidad: en Android 10+ la tabla ARP (/proc/net/arp) suele estar
 * restringida, así que la MAC y el fabricante pueden no estar disponibles; en ese
 * caso igualmente listamos la IP y el nombre de host si responde.
 */
class DeviceScanner(context: Context) {

    private val appContext = context.applicationContext
    private val wifiManager =
        appContext.getSystemService(Context.WIFI_SERVICE) as WifiManager

    suspend fun scan(
        timeoutMs: Int = 400,
        onProgress: (done: Int, total: Int) -> Unit = { _, _ -> },
    ): ScanOutcome = withContext(Dispatchers.IO) {
        val local = localIpv4() ?: return@withContext ScanOutcome("—", null, emptyList())
        val base = local.substringBeforeLast('.')      // asume /24
        val gateway = gatewayIp()
        val myIp = local
        val arpTable = readArpTable()
        val semaphore = Semaphore(48)
        var done = 0
        val total = 254

        val results = coroutineScope {
            (1..254).map { host ->
                async {
                    val ip = "$base.$host"
                    val device = probe(ip, myIp, gateway, arpTable, timeoutMs)
                    synchronized(this@DeviceScanner) {
                        done++
                        onProgress(done, total)
                    }
                    device
                }
            }.awaitAll()
        }

        val devices = results.filterNotNull()
            .sortedWith(compareByDescending<ConnectedDevice> { it.isGateway }
                .thenByDescending { it.isThisDevice }
                .thenBy { ipSortKey(it.ipAddress) })

        ScanOutcome("$base.0/24", gateway, devices)
    }

    private fun probe(
        ip: String,
        myIp: String,
        gateway: String?,
        arp: Map<String, String>,
        timeoutMs: Int,
    ): ConnectedDevice? {
        val isMe = ip == myIp
        val addr = runCatching { InetAddress.getByName(ip) }.getOrNull() ?: return null
        val start = System.currentTimeMillis()
        val reachable = isMe || runCatching { addr.isReachable(timeoutMs) }.getOrDefault(false)
        val elapsed = System.currentTimeMillis() - start
        val mac = arp[ip]
        // Lo incluimos si respondió, si es este equipo, o si aparece en la tabla ARP.
        if (!reachable && mac == null && !isMe) return null

        val host = runCatching {
            addr.canonicalHostName.takeIf { it != ip }
        }.getOrNull()

        return ConnectedDevice(
            ipAddress = ip,
            hostName = host,
            macAddress = mac,
            vendor = OuiDatabase.lookup(mac),
            isGateway = gateway != null && ip == gateway,
            isThisDevice = isMe,
            responseTimeMs = if (reachable && !isMe) elapsed else null,
        )
    }

    /** IPv4 privada de la interfaz activa (típicamente wlan0). */
    private fun localIpv4(): String? {
        runCatching {
            NetworkInterface.getNetworkInterfaces().toList().forEach { nif ->
                if (!nif.isUp || nif.isLoopback) return@forEach
                nif.inetAddresses.toList().forEach { addr ->
                    if (!addr.isLoopbackAddress && addr.address.size == 4 && addr.isSiteLocalAddress) {
                        return addr.hostAddress
                    }
                }
            }
        }
        // Respaldo: DHCP info del WifiManager.
        @Suppress("DEPRECATION")
        val ip = runCatching { wifiManager.dhcpInfo?.ipAddress ?: 0 }.getOrDefault(0)
        return if (ip != 0) intToIp(ip) else null
    }

    @SuppressLint("MissingPermission")
    private fun gatewayIp(): String? {
        @Suppress("DEPRECATION")
        val gw = runCatching { wifiManager.dhcpInfo?.gateway ?: 0 }.getOrDefault(0)
        return if (gw != 0) intToIp(gw) else null
    }

    /** Lee /proc/net/arp -> mapa IP:MAC. Puede venir vacío en Android reciente. */
    private fun readArpTable(): Map<String, String> {
        val map = mutableMapOf<String, String>()
        runCatching {
            File("/proc/net/arp").readLines().drop(1).forEach { line ->
                val parts = line.split(Regex("\\s+")).filter { it.isNotBlank() }
                if (parts.size >= 4) {
                    val ip = parts[0]
                    val mac = parts[3]
                    if (mac != "00:00:00:00:00:00" && mac.count { it == ':' } == 5) {
                        map[ip] = mac.lowercase()
                    }
                }
            }
        }
        return map
    }

    private fun intToIp(addr: Int): String = "%d.%d.%d.%d".format(
        addr and 0xff, addr shr 8 and 0xff, addr shr 16 and 0xff, addr shr 24 and 0xff
    )

    private fun ipSortKey(ip: String): Int =
        ip.substringAfterLast('.').toIntOrNull() ?: 0
}
