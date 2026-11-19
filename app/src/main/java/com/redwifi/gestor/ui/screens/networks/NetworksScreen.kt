package com.redwifi.gestor.ui.screens.networks

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.ChevronRight
import androidx.compose.material.icons.rounded.Lock
import androidx.compose.material.icons.rounded.LockOpen
import androidx.compose.material.icons.rounded.Refresh
import androidx.compose.material.icons.rounded.WifiOff
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.redwifi.gestor.domain.SignalMath
import com.redwifi.gestor.domain.model.CurrentConnection
import com.redwifi.gestor.domain.model.Security
import com.redwifi.gestor.domain.model.WifiNetwork
import com.redwifi.gestor.ui.components.Pill
import com.redwifi.gestor.ui.components.SignalBars
import com.redwifi.gestor.ui.components.bandColor
import com.redwifi.gestor.ui.components.signalColor

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NetworksScreen(
    onOpenSignal: () -> Unit,
    viewModel: NetworksViewModel = viewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    Column(Modifier.fillMaxSize()) {
        TopAppBar(
            title = { Text("Redes WiFi", fontWeight = FontWeight.Bold) },
            actions = {
                IconButton(onClick = { viewModel.refresh() }) {
                    Icon(Icons.Rounded.Refresh, contentDescription = "Reescanear")
                }
            },
            colors = TopAppBarDefaults.topAppBarColors(
                containerColor = Color.Transparent,
                titleContentColor = MaterialTheme.colorScheme.onBackground,
            ),
        )

        if (!state.wifiEnabled) {
            WifiOffBanner()
        }

        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            state.current?.let { current ->
                item { CurrentConnectionCard(current, state.networks.size, onOpenSignal) }
            }
            item {
                Text(
                    "Redes cercanas (${state.networks.size})",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onBackground,
                    modifier = Modifier.padding(top = 6.dp, bottom = 2.dp),
                )
            }
            items(state.networks, key = { it.bssid + it.frequencyMhz }) { net ->
                NetworkRow(net)
            }
            if (state.networks.isEmpty() && !state.loading) {
                item { EmptyNetworks() }
            }
        }
    }
}

@Composable
private fun CurrentConnectionCard(
    current: CurrentConnection,
    nearbyCount: Int,
    onOpenSignal: () -> Unit,
) {
    ElevatedCard(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onOpenSignal),
        colors = CardDefaults.elevatedCardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer,
        ),
    ) {
        Column(Modifier.padding(18.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text(
                        "CONECTADO A",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f),
                    )
                    Spacer(Modifier.height(2.dp))
                    Text(
                        current.ssid.ifBlank { "Red WiFi" },
                        style = MaterialTheme.typography.headlineSmall,
                        color = MaterialTheme.colorScheme.onPrimaryContainer,
                    )
                }
                SignalBars(
                    bars = SignalMath.rssiToBars(current.rssi),
                    color = MaterialTheme.colorScheme.onPrimaryContainer,
                )
            }
            Spacer(Modifier.height(14.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(20.dp)) {
                MiniStat("${current.signalPercent}%", "Señal")
                MiniStat("${current.rssi} dBm", "Potencia")
                MiniStat("${current.linkSpeedMbps} Mbps", "Enlace")
                MiniStat(current.band.label, "Banda")
            }
            Spacer(Modifier.height(12.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    "Toca para ver el medidor en vivo",
                    fontSize = 13.sp,
                    color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.85f),
                    modifier = Modifier.weight(1f),
                )
                Icon(
                    Icons.Rounded.ChevronRight,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.onPrimaryContainer,
                )
            }
        }
    }
}

@Composable
private fun MiniStat(value: String, label: String) {
    Column {
        Text(
            value,
            fontWeight = FontWeight.Bold,
            fontSize = 15.sp,
            color = MaterialTheme.colorScheme.onPrimaryContainer,
        )
        Text(
            label,
            fontSize = 11.sp,
            color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f),
        )
    }
}

@Composable
private fun NetworkRow(net: WifiNetwork) {
    ElevatedCard(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.elevatedCardColors(
            containerColor = MaterialTheme.colorScheme.surface,
        ),
    ) {
        Row(
            Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(contentAlignment = Alignment.Center) {
                SignalBars(bars = net.bars, color = signalColor(net.signalPercent))
            }
            Spacer(Modifier.width(14.dp))
            Column(Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        net.displaySsid,
                        fontWeight = FontWeight.SemiBold,
                        fontSize = 16.sp,
                        color = MaterialTheme.colorScheme.onSurface,
                    )
                    if (net.isCurrent) {
                        Spacer(Modifier.width(8.dp))
                        Pill("Conectado", MaterialTheme.colorScheme.primary)
                    }
                }
                Spacer(Modifier.height(6.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    Pill("Canal ${net.channel}", bandColor(net.band.label))
                    Pill(net.band.label, bandColor(net.band.label))
                    SecurityPill(net.security)
                }
                Spacer(Modifier.height(6.dp))
                Text(
                    "≈ ${SignalMath.formatDistance(net.estimatedDistanceMeters)} · ${net.bssid}",
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Spacer(Modifier.width(10.dp))
            Column(horizontalAlignment = Alignment.End) {
                Text(
                    "${net.signalPercent}%",
                    fontWeight = FontWeight.Bold,
                    fontSize = 18.sp,
                    color = signalColor(net.signalPercent),
                )
                Text(
                    "${net.rssi} dBm",
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
private fun SecurityPill(security: Security) {
    val color = if (security.isSecure) MaterialTheme.colorScheme.secondary else MaterialTheme.colorScheme.error
    Row(verticalAlignment = Alignment.CenterVertically) {
        Icon(
            if (security.isSecure) Icons.Rounded.Lock else Icons.Rounded.LockOpen,
            contentDescription = null,
            tint = color,
            modifier = Modifier.size(13.dp),
        )
        Spacer(Modifier.width(3.dp))
        Pill(security.label, color)
    }
}

@Composable
private fun WifiOffBanner() {
    Row(
        Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp)
            .height(48.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(Icons.Rounded.WifiOff, contentDescription = null, tint = MaterialTheme.colorScheme.error)
        Spacer(Modifier.width(10.dp))
        Text(
            "El WiFi está apagado. Actívalo para escanear redes.",
            color = MaterialTheme.colorScheme.error,
            fontSize = 14.sp,
        )
    }
}

@Composable
private fun EmptyNetworks() {
    Column(
        Modifier
            .fillMaxWidth()
            .padding(top = 60.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Icon(
            Icons.Rounded.WifiOff,
            contentDescription = null,
            modifier = Modifier.size(48.dp),
            tint = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(12.dp))
        Text(
            "Sin redes todavía. Pulsa actualizar.",
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}
