package com.redwifi.gestor.ui.screens.tools

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.OpenInNew
import androidx.compose.material.icons.rounded.Refresh
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.redwifi.gestor.data.net.RouterTools
import com.redwifi.gestor.data.wifi.RiskLevel
import com.redwifi.gestor.data.wifi.SecurityIssue
import com.redwifi.gestor.ui.components.LevelBar
import com.redwifi.gestor.ui.components.Pill
import com.redwifi.gestor.ui.components.StatTile
import com.redwifi.gestor.ui.theme.Amber
import com.redwifi.gestor.ui.theme.Coral
import com.redwifi.gestor.ui.theme.Cyan
import com.redwifi.gestor.ui.theme.Teal
import com.redwifi.gestor.ui.theme.Violet

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ToolsScreen(viewModel: ToolsViewModel = viewModel()) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val context = LocalContext.current

    Column(Modifier.fillMaxSize()) {
        TopAppBar(
            title = { Text("Herramientas", fontWeight = FontWeight.Bold) },
            actions = {
                IconButton(onClick = { viewModel.refresh() }) {
                    Icon(Icons.Rounded.Refresh, contentDescription = "Actualizar")
                }
            },
            colors = TopAppBarDefaults.topAppBarColors(
                containerColor = Color.Transparent,
                titleContentColor = MaterialTheme.colorScheme.onBackground,
            ),
        )

        LazyColumn(
            Modifier.fillMaxSize(),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            item { OverviewRow(state) }
            item { BestChannelCard(state) }
            item { OccupancyCard("Ocupación 2.4 GHz", state.occupancy24, Amber) }
            if (state.occupancy5.isNotEmpty()) {
                item { OccupancyCard("Ocupación 5 GHz", state.occupancy5, Cyan) }
            }
            item { SecurityCard(state.issues) }
            item { RouterCard(onOpen = { RouterTools.openRouterAdmin(context, null) }) }
        }
    }
}

@Composable
private fun OverviewRow(state: ToolsUiState) {
    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        StatTile("Redes", "${state.totalNetworks}", Teal, Modifier.weight(1f))
        StatTile("2.4 GHz", "${state.count24}", Amber, Modifier.weight(1f))
        StatTile("5 GHz", "${state.count5}", Cyan, Modifier.weight(1f))
        if (state.count6 > 0) {
            StatTile("6 GHz", "${state.count6}", Violet, Modifier.weight(1f))
        }
    }
}

@Composable
private fun BestChannelCard(state: ToolsUiState) {
    val rec = state.recommendation
    ElevatedCard(
        Modifier.fillMaxWidth(),
        colors = CardDefaults.elevatedCardColors(containerColor = MaterialTheme.colorScheme.surface),
    ) {
        Column(Modifier.padding(18.dp)) {
            Text(
                "Mejor canal (2.4 GHz)",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface,
            )
            Spacer(Modifier.height(4.dp))
            Text(
                "De los canales no solapados (1, 6, 11), el menos congestionado:",
                fontSize = 12.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(12.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    rec?.best?.toString() ?: "—",
                    fontSize = 44.sp,
                    fontWeight = FontWeight.Bold,
                    color = Teal,
                )
                Spacer(Modifier.width(16.dp))
                Column(Modifier.weight(1f)) {
                    rec?.loads?.forEach { load ->
                        val maxScore = (rec.loads.maxOfOrNull { it.score } ?: 1.0).coerceAtLeast(0.01)
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                "Canal ${load.channel}",
                                fontSize = 12.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = Modifier.width(66.dp),
                            )
                            LevelBar(
                                fraction = (load.score / maxScore).toFloat(),
                                color = if (load.channel == rec.best) Teal else MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = Modifier.weight(1f),
                            )
                        }
                        Spacer(Modifier.height(6.dp))
                    }
                }
            }
        }
    }
}

@Composable
private fun OccupancyCard(title: String, occupancy: Map<Int, Int>, color: Color) {
    ElevatedCard(
        Modifier.fillMaxWidth(),
        colors = CardDefaults.elevatedCardColors(containerColor = MaterialTheme.colorScheme.surface),
    ) {
        Column(Modifier.padding(18.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.onSurface)
            Spacer(Modifier.height(12.dp))
            if (occupancy.isEmpty()) {
                Text("Sin datos.", fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
            } else {
                val maxCount = occupancy.values.maxOrNull() ?: 1
                occupancy.forEach { (channel, count) ->
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            "C$channel",
                            fontSize = 12.sp,
                            fontFamily = FontFamily.Monospace,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier.width(42.dp),
                        )
                        LevelBar(
                            fraction = count.toFloat() / maxCount,
                            color = color,
                            modifier = Modifier.weight(1f),
                        )
                        Spacer(Modifier.width(8.dp))
                        Text(
                            "$count",
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.onSurface,
                            modifier = Modifier.width(22.dp),
                        )
                    }
                    Spacer(Modifier.height(7.dp))
                }
            }
        }
    }
}

@Composable
private fun SecurityCard(issues: List<SecurityIssue>) {
    ElevatedCard(
        Modifier.fillMaxWidth(),
        colors = CardDefaults.elevatedCardColors(containerColor = MaterialTheme.colorScheme.surface),
    ) {
        Column(Modifier.padding(18.dp)) {
            Text(
                "Auditoría de seguridad",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface,
            )
            Spacer(Modifier.height(12.dp))
            if (issues.isEmpty()) {
                Text(
                    "No se detectaron riesgos evidentes en las redes visibles. 👍",
                    fontSize = 13.sp,
                    color = Teal,
                )
            } else {
                issues.forEach { issue ->
                    val color = when (issue.level) {
                        RiskLevel.HIGH -> Coral
                        RiskLevel.MEDIUM -> Amber
                        else -> Cyan
                    }
                    Column(Modifier.padding(vertical = 6.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                issue.network.displaySsid,
                                fontWeight = FontWeight.SemiBold,
                                color = MaterialTheme.colorScheme.onSurface,
                                modifier = Modifier.weight(1f),
                            )
                            Pill(issue.level.name, color)
                        }
                        Spacer(Modifier.height(3.dp))
                        Text(
                            issue.reason,
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun RouterCard(onOpen: () -> Unit) {
    ElevatedCard(
        Modifier.fillMaxWidth(),
        colors = CardDefaults.elevatedCardColors(containerColor = MaterialTheme.colorScheme.surface),
    ) {
        Column(Modifier.padding(18.dp)) {
            Text(
                "Panel del router",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface,
            )
            Spacer(Modifier.height(4.dp))
            Text(
                "Accede a la configuración de tu router para cambiar canal, contraseña " +
                    "o bloquear dispositivos.",
                fontSize = 12.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(12.dp))
            OutlinedButton(onClick = onOpen) {
                Icon(Icons.Rounded.OpenInNew, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.size(8.dp))
                Text("Abrir panel del router")
            }
        }
    }
}
