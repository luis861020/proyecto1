package com.redwifi.gestor.ui.components

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.redwifi.gestor.ui.theme.Amber
import com.redwifi.gestor.ui.theme.Coral
import com.redwifi.gestor.ui.theme.Cyan
import com.redwifi.gestor.ui.theme.Teal
import com.redwifi.gestor.ui.theme.Violet
import kotlin.math.max
import kotlin.math.min

/** Color según la calidad de señal (verde-ámbar-rojo). */
fun signalColor(percent: Int): Color = when {
    percent >= 70 -> Teal
    percent >= 45 -> Cyan
    percent >= 25 -> Amber
    else -> Coral
}

fun bandColor(bandLabel: String): Color = when {
    bandLabel.startsWith("2.4") -> Amber
    bandLabel.startsWith("5") -> Cyan
    bandLabel.startsWith("6") -> Violet
    else -> Color.Gray
}

/** Cuatro barras de señal al estilo del sistema. */
@Composable
fun SignalBars(bars: Int, modifier: Modifier = Modifier, color: Color = Teal) {
    val heights = listOf(6.dp, 10.dp, 14.dp, 18.dp)
    Row(modifier = modifier, verticalAlignment = Alignment.Bottom) {
        heights.forEachIndexed { i, h ->
            Box(
                Modifier
                    .padding(end = 2.dp)
                    .width(4.dp)
                    .height(h)
                    .clip(RoundedCornerShape(2.dp))
                    .background(if (i < bars) color else color.copy(alpha = 0.18f))
            )
        }
    }
}

/** Píldora con texto y color. */
@Composable
fun Pill(text: String, color: Color, modifier: Modifier = Modifier) {
    Box(
        modifier
            .clip(RoundedCornerShape(50))
            .background(color.copy(alpha = 0.16f))
            .padding(horizontal = 10.dp, vertical = 4.dp)
    ) {
        Text(
            text = text,
            color = color,
            fontSize = 11.sp,
            fontWeight = FontWeight.SemiBold,
        )
    }
}

/** Medidor circular animado de intensidad (0-100%). */
@Composable
fun SignalGauge(
    percent: Int,
    rssi: Int,
    modifier: Modifier = Modifier,
    size: Dp = 180.dp,
) {
    val target = percent.coerceIn(0, 100) / 100f
    val animated by animateFloatAsState(
        targetValue = target,
        animationSpec = tween(700),
        label = "gauge",
    )
    val arcColor by animateColorAsState(signalColor(percent), label = "gaugeColor")
    val track = MaterialTheme.colorScheme.surfaceVariant

    Box(modifier.size(size), contentAlignment = Alignment.Center) {
        Canvas(Modifier.size(size)) {
            val stroke = Stroke(width = 22f, cap = StrokeCap.Round)
            val inset = 26f
            val arcSize = Size(this.size.width - inset * 2, this.size.height - inset * 2)
            val topLeft = Offset(inset, inset)
            // Pista
            drawArc(
                color = track,
                startAngle = 135f,
                sweepAngle = 270f,
                useCenter = false,
                topLeft = topLeft,
                size = arcSize,
                style = stroke,
            )
            // Progreso
            drawArc(
                brush = Brush.sweepGradient(listOf(arcColor.copy(alpha = 0.6f), arcColor)),
                startAngle = 135f,
                sweepAngle = 270f * animated,
                useCenter = false,
                topLeft = topLeft,
                size = arcSize,
                style = stroke,
            )
        }
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(
                text = "$percent%",
                fontSize = 40.sp,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurface,
            )
            Text(
                text = "$rssi dBm",
                fontFamily = FontFamily.Monospace,
                fontSize = 14.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

/** Gráfica de línea (sparkline) para el histórico de RSSI. */
@Composable
fun Sparkline(
    values: List<Int>,
    modifier: Modifier = Modifier,
    minValue: Int = -100,
    maxValue: Int = -30,
    lineColor: Color = Teal,
) {
    Canvas(modifier) {
        if (values.size < 2) return@Canvas
        val w = size.width
        val h = size.height
        val range = (maxValue - minValue).toFloat().coerceAtLeast(1f)
        val stepX = w / (values.size - 1).toFloat()

        fun yFor(v: Int): Float {
            val clamped = v.coerceIn(minValue, maxValue)
            val norm = (clamped - minValue) / range
            return h - norm * h
        }

        val line = Path()
        val fill = Path()
        values.forEachIndexed { i, v ->
            val x = i * stepX
            val y = yFor(v)
            if (i == 0) {
                line.moveTo(x, y)
                fill.moveTo(x, h)
                fill.lineTo(x, y)
            } else {
                line.lineTo(x, y)
                fill.lineTo(x, y)
            }
        }
        fill.lineTo(w, h)
        fill.close()

        drawPath(
            path = fill,
            brush = Brush.verticalGradient(
                listOf(lineColor.copy(alpha = 0.30f), lineColor.copy(alpha = 0f))
            ),
        )
        drawPath(
            path = line,
            color = lineColor,
            style = Stroke(width = 4f, cap = StrokeCap.Round),
        )
    }
}

/** Barra de nivel horizontal (para histogramas de canales). */
@Composable
fun LevelBar(
    fraction: Float,
    color: Color,
    modifier: Modifier = Modifier,
    height: Dp = 8.dp,
) {
    Box(
        modifier
            .height(height)
            .clip(RoundedCornerShape(50))
            .background(color.copy(alpha = 0.15f))
    ) {
        Box(
            Modifier
                .fillMaxWidth(min(1f, max(0f, fraction)))
                .height(height)
                .clip(RoundedCornerShape(50))
                .background(color)
        )
    }
}

/** Casilla de estadística compacta. */
@Composable
fun StatTile(label: String, value: String, accent: Color, modifier: Modifier = Modifier) {
    Column(
        modifier
            .clip(RoundedCornerShape(16.dp))
            .background(MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f))
            .padding(14.dp)
    ) {
        Text(value, fontSize = 20.sp, fontWeight = FontWeight.Bold, color = accent)
        Spacer(Modifier.height(2.dp))
        Text(
            label,
            fontSize = 12.sp,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}
