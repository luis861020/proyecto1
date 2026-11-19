package com.redwifi.gestor.ui.screens.radar

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Refresh
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
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.redwifi.gestor.domain.SignalMath
import com.redwifi.gestor.domain.model.WifiNetwork
import com.redwifi.gestor.ui.components.Pill
import com.redwifi.gestor.ui.components.bandColor
import kotlin.math.cos
import kotlin.math.ln
import kotlin.math.sin

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RadarScreen(viewModel: RadarViewModel = viewModel()) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    var selected by remember { mutableStateOf<WifiNetwork?>(null) }

    Column(Modifier.fillMaxSize()) {
        TopAppBar(
            title = { Text("Radar espacial", fontWeight = FontWeight.Bold) },
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

        Column(
            Modifier
                .fillMaxSize()
                .padding(16.dp),
        ) {
            Text(
                "Distancia estimada a cada red respecto a ti (centro). Es una " +
                    "aproximación basada en la intensidad de la señal.",
                fontSize = 13.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(12.dp))

            RadarCanvas(
                networks = state.networks,
                selected = selected,
                onSelect = { selected = it },
                modifier = Modifier
                    .fillMaxWidth()
                    .aspectRatio(1f),
            )

            Spacer(Modifier.height(16.dp))
            Legend()
            Spacer(Modifier.height(12.dp))

            val sel = selected
            if (sel != null) {
                SelectedCard(sel)
            } else {
                Text(
                    "Toca un punto para ver los detalles de esa red.",
                    fontSize = 13.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

private fun angleForBssid(bssid: String): Double {
    val h = Math.floorMod(bssid.hashCode(), 360)
    return Math.toRadians(h.toDouble())
}

@Composable
private fun RadarCanvas(
    networks: List<WifiNetwork>,
    selected: WifiNetwork?,
    onSelect: (WifiNetwork) -> Unit,
    modifier: Modifier = Modifier,
) {
    val ringColor = MaterialTheme.colorScheme.outline
    val sweepColor = MaterialTheme.colorScheme.primary
    val centerColor = MaterialTheme.colorScheme.primary

    val transition = rememberInfiniteTransition(label = "radar")
    val sweepAngle by transition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(4000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart,
        ),
        label = "sweep",
    )

    BoxWithConstraints(modifier) {
        val density = LocalDensity.current
        val sidePx = with(density) { maxWidth.toPx() }
        val center = Offset(sidePx / 2f, sidePx / 2f)
        val maxR = sidePx / 2f * 0.86f

        val maxMeters = (networks.maxOfOrNull { it.estimatedDistanceMeters } ?: 10.0)
            .coerceAtLeast(6.0)

        fun radiusFor(meters: Double): Float {
            val norm = (ln(meters + 1.0) / ln(maxMeters + 1.0)).coerceIn(0.0, 1.0)
            return (norm * maxR).toFloat()
        }

        // Posiciones precalculadas (red -> punto en pantalla).
        val points = remember(networks, sidePx) {
            networks.map { net ->
                val angle = angleForBssid(net.bssid) - Math.PI / 2 // 0 arriba
                val r = radiusFor(net.estimatedDistanceMeters)
                net to Offset(
                    (center.x + r * cos(angle)).toFloat(),
                    (center.y + r * sin(angle)).toFloat(),
                )
            }
        }

        val ringMeters = listOf(1, 2, 5, 10, 20, 50).filter { it <= maxMeters * 1.1 }

        Canvas(
            Modifier
                .size(maxWidth)
                .pointerInput(points) {
                    detectTapGestures { tap ->
                        val nearest = points.minByOrNull { (_, p) ->
                            val dx = p.x - tap.x
                            val dy = p.y - tap.y
                            dx * dx + dy * dy
                        }
                        if (nearest != null) {
                            val (net, p) = nearest
                            val dx = p.x - tap.x
                            val dy = p.y - tap.y
                            if (dx * dx + dy * dy < 90f * 90f) onSelect(net)
                        }
                    }
                },
        ) {
            // Anillos de distancia
            ringMeters.forEach { m ->
                drawCircle(
                    color = ringColor.copy(alpha = 0.5f),
                    radius = radiusFor(m.toDouble()),
                    center = center,
                    style = Stroke(width = 2f),
                )
            }
            // Ejes
            drawLine(ringColor.copy(alpha = 0.3f), Offset(center.x, 0f), Offset(center.x, sidePx), 2f)
            drawLine(ringColor.copy(alpha = 0.3f), Offset(0f, center.y), Offset(sidePx, center.y), 2f)

            // Barrido giratorio
            rotate(degrees = sweepAngle, pivot = center) {
                drawArc(
                    brush = Brush.sweepGradient(
                        colors = listOf(
                            Color.Transparent,
                            Color.Transparent,
                            sweepColor.copy(alpha = 0.25f),
                            sweepColor.copy(alpha = 0.0f),
                        ),
                        center = center,
                    ),
                    startAngle = 0f,
                    sweepAngle = 70f,
                    useCenter = true,
                    topLeft = Offset(center.x - maxR, center.y - maxR),
                    size = androidx.compose.ui.geometry.Size(maxR * 2, maxR * 2),
                )
                drawLine(
                    color = sweepColor,
                    start = center,
                    end = Offset(center.x + maxR, center.y),
                    strokeWidth = 3f,
                )
            }

            // Puntos de redes
            points.forEach { (net, p) ->
                val color = bandColor(net.band.label)
                val isSel = selected?.bssid == net.bssid
                val dotR = (6f + net.signalPercent / 100f * 7f)
                if (net.isCurrent || isSel) {
                    drawCircle(color.copy(alpha = 0.25f), radius = dotR + 10f, center = p)
                }
                drawCircle(color = color, radius = dotR, center = p)
                drawCircle(Color.White.copy(alpha = 0.9f), radius = dotR / 2.6f, center = p)
            }

            // Centro = tú
            drawCircle(centerColor, radius = 9f, center = center)
            drawCircle(centerColor.copy(alpha = 0.3f), radius = 18f, center = center, style = Stroke(width = 3f))
        }
    }
}

@Composable
private fun Legend() {
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        Pill("2.4 GHz", bandColor("2.4"))
        Pill("5 GHz", bandColor("5"))
        Pill("6 GHz", bandColor("6"))
        Spacer(Modifier.weight(1f))
        Text(
            "Anillos ≈ 1·2·5·10·20 m",
            fontSize = 11.sp,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun SelectedCard(net: WifiNetwork) {
    ElevatedCard(
        Modifier.fillMaxWidth(),
        colors = CardDefaults.elevatedCardColors(
            containerColor = MaterialTheme.colorScheme.surface,
        ),
    ) {
        Column(Modifier.padding(16.dp)) {
            Text(
                net.displaySsid,
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface,
            )
            Spacer(Modifier.height(4.dp))
            Text(
                "Distancia estimada ≈ ${SignalMath.formatDistance(net.estimatedDistanceMeters)}",
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.SemiBold,
            )
            Spacer(Modifier.height(10.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Pill("${net.signalPercent}%", bandColor(net.band.label))
                Pill("Canal ${net.channel}", bandColor(net.band.label))
                Pill(net.band.label, bandColor(net.band.label))
                Pill(net.security.label, MaterialTheme.colorScheme.secondary)
            }
            Spacer(Modifier.height(8.dp))
            Text(
                "${net.rssi} dBm · ${net.bssid}",
                fontSize = 11.sp,
                fontFamily = FontFamily.Monospace,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}
