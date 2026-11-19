package com.redwifi.gestor.ui.screens.devices

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
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.background
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Info
import androidx.compose.material.icons.rounded.OpenInNew
import androidx.compose.material.icons.rounded.Radar
import androidx.compose.material.icons.rounded.Router
import androidx.compose.material.icons.rounded.Smartphone
import androidx.compose.material3.Button
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.redwifi.gestor.data.net.RouterTools
import com.redwifi.gestor.domain.model.ConnectedDevice
import com.redwifi.gestor.ui.components.Pill
import com.redwifi.gestor.ui.theme.Amber
import com.redwifi.gestor.ui.theme.Cyan
import com.redwifi.gestor.ui.theme.Teal

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DevicesScreen(viewModel: DevicesViewModel = viewModel()) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val context = LocalContext.current

    Column(Modifier.fillMaxSize()) {
        TopAppBar(
            title = { Text("Dispositivos", fontWeight = FontWeight.Bold) },
            colors = TopAppBarDefaults.topAppBarColors(
                containerColor = Color.Transparent,
                titleContentColor = MaterialTheme.colorScheme.onBackground,
            ),
        )

        LazyColumn(
            Modifier.fillMaxSize(),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            item {
                ScanHeader(
                    subnet = state.subnet,
                    gateway = state.gatewayIp,
                    count = state.devices.size,
                    scanning = state.scanning,
                    progress = state.progress,
                    onScan = { viewModel.scan() },
                )
            }

            if (state.devices.isNotEmpty()) {
                item { DisconnectInfoCard(onOpenRouter = { RouterTools.openRouterAdmin(context, state.gatewayIp) }) }
            }

            items(state.devices, key = { it.ipAddress }) { device ->
                DeviceRow(
                    device = device,
                    onManage = { RouterTools.openRouterAdmin(context, state.gatewayIp) },
                )
            }

            if (state.hasScanned && state.devices.isEmpty() && !state.scanning) {
                item {
                    Text(
                        "No se encontraron dispositivos activos. Algunos equipos no " +
                            "responden a ping aunque estén conectados.",
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(top = 20.dp),
                    )
                }
            }
        }
    }
}

@Composable
private fun ScanHeader(
    subnet: String?,
    gateway: String?,
    count: Int,
    scanning: Boolean,
    progress: Float,
    onScan: () -> Unit,
) {
    ElevatedCard(
        Modifier.fillMaxWidth(),
        colors = CardDefaults.elevatedCardColors(containerColor = MaterialTheme.colorScheme.surface),
    ) {
        Column(Modifier.padding(18.dp)) {
            Text(
                if (count > 0) "$count dispositivos en tu red" else "Explora tu red local",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface,
            )
            Spacer(Modifier.height(4.dp))
            Text(
                buildString {
                    append("Subred: ${subnet ?: "—"}")
                    if (gateway != null) append("  ·  Router: $gateway")
                },
                fontSize = 12.sp,
                fontFamily = FontFamily.Monospace,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(14.dp))
            if (scanning) {
                LinearProgressIndicator(
                    progress = { progress },
                    modifier = Modifier.fillMaxWidth(),
                )
                Spacer(Modifier.height(8.dp))
                Text(
                    "Escaneando... ${(progress * 100).toInt()}%",
                    fontSize = 12.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            } else {
                Button(onClick = onScan, modifier = Modifier.fillMaxWidth()) {
                    Icon(Icons.Rounded.Radar, contentDescription = null, modifier = Modifier.size(18.dp))
                    Spacer(Modifier.size(8.dp))
                    Text(if (count > 0) "Escanear de nuevo" else "Escanear red")
                }
            }
        }
    }
}

@Composable
private fun DisconnectInfoCard(onOpenRouter: () -> Unit) {
    ElevatedCard(
        Modifier.fillMaxWidth(),
        colors = CardDefaults.elevatedCardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.6f),
        ),
    ) {
        Column(Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Rounded.Info, contentDescription = null, tint = MaterialTheme.colorScheme.secondary)
                Spacer(Modifier.size(8.dp))
                Text(
                    "¿Desconectar un dispositivo?",
                    fontWeight = FontWeight.SemiBold,
                    color = MaterialTheme.colorScheme.onSurface,
                )
            }
            Spacer(Modifier.height(8.dp))
            Text(
                "Android no permite expulsar a otro equipo de la red por seguridad. " +
                    "La forma real de bloquear o desconectar a alguien de TU red es " +
                    "desde el panel de tu router (filtrado MAC / lista de bloqueo).",
                fontSize = 13.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(12.dp))
            OutlinedButton(onClick = onOpenRouter) {
                Icon(Icons.Rounded.OpenInNew, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.size(8.dp))
                Text("Abrir panel del router")
            }
        }
    }
}

@Composable
private fun DeviceRow(device: ConnectedDevice, onManage: () -> Unit) {
    val (icon, accent) = when {
        device.isGateway -> Icons.Rounded.Router to Teal
        device.isThisDevice -> Icons.Rounded.Smartphone to Cyan
        else -> Icons.Rounded.Radar to Amber
    }
    ElevatedCard(
        Modifier.fillMaxWidth(),
        colors = CardDefaults.elevatedCardColors(containerColor = MaterialTheme.colorScheme.surface),
    ) {
        Row(
            Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(
                Modifier
                    .size(44.dp)
                    .clip(CircleShape)
                    .background(accent.copy(alpha = 0.15f)),
                contentAlignment = Alignment.Center,
            ) {
                Icon(icon, contentDescription = null, tint = accent, modifier = Modifier.size(22.dp))
            }
            Spacer(Modifier.size(14.dp))
            Column(Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        device.displayName,
                        fontWeight = FontWeight.SemiBold,
                        fontSize = 15.sp,
                        color = MaterialTheme.colorScheme.onSurface,
                    )
                    if (device.isGateway) {
                        Spacer(Modifier.size(6.dp))
                        Pill("Router", Teal)
                    }
                }
                Spacer(Modifier.height(3.dp))
                Text(
                    device.ipAddress + (device.macAddress?.let { "  ·  $it" } ?: ""),
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                device.vendor?.let {
                    Text(it, fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
            if (device.responseTimeMs != null) {
                Text(
                    "${device.responseTimeMs} ms",
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    color = accent,
                )
            }
        }
    }
}
