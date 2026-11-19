package com.redwifi.gestor.data.wifi

import com.redwifi.gestor.domain.model.Band
import com.redwifi.gestor.domain.model.WifiNetwork
import kotlin.math.abs

/** Ocupación de un canal concreto. */
data class ChannelLoad(
    val channel: Int,
    val networkCount: Int,
    val score: Double,
)

/** Recomendación de canal para una banda. */
data class ChannelRecommendation(
    val band: Band,
    val best: Int,
    val loads: List<ChannelLoad>,
)

/**
 * Analiza la congestión de canales. En 2.4 GHz los canales se solapan, por eso
 * se penaliza a los vecinos; los canales no solapados recomendados son 1, 6 y 11.
 */
object ChannelAnalyzer {

    private val NON_OVERLAP_24 = listOf(1, 6, 11)

    fun recommend24GHz(networks: List<WifiNetwork>): ChannelRecommendation {
        val nets = networks.filter { it.band == Band.GHZ_2_4 && it.channel in 1..14 }
        val loads = NON_OVERLAP_24.map { candidate ->
            var score = 0.0
            var count = 0
            for (n in nets) {
                val distance = abs(n.channel - candidate)
                if (distance <= 4) {
                    // Peso por solape (más cerca = peor) y por intensidad de la señal.
                    val overlapWeight = (5 - distance) / 5.0
                    val signalWeight = (n.signalPercent / 100.0).coerceIn(0.05, 1.0)
                    score += overlapWeight * signalWeight
                    if (distance == 0) count++
                }
            }
            ChannelLoad(candidate, count, score)
        }
        val best = loads.minByOrNull { it.score }?.channel ?: 1
        return ChannelRecommendation(Band.GHZ_2_4, best, loads)
    }

    /** Histograma simple: cuántas redes hay en cada canal de una banda. */
    fun occupancy(networks: List<WifiNetwork>, band: Band): Map<Int, Int> =
        networks.filter { it.band == band && it.channel > 0 }
            .groupingBy { it.channel }
            .eachCount()
            .toSortedMap()
}
