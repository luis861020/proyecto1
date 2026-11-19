package com.redwifi.gestor.data.wifi

import com.redwifi.gestor.domain.model.Security
import com.redwifi.gestor.domain.model.WifiNetwork

enum class RiskLevel { HIGH, MEDIUM, LOW, OK }

data class SecurityIssue(
    val network: WifiNetwork,
    val level: RiskLevel,
    val reason: String,
)

/** Revisa las redes visibles y señala riesgos de seguridad comunes. */
object SecurityAudit {

    fun audit(networks: List<WifiNetwork>): List<SecurityIssue> =
        networks.mapNotNull { net ->
            when {
                net.security == Security.OPEN -> SecurityIssue(
                    net, RiskLevel.HIGH,
                    "Red abierta: el tráfico viaja sin cifrar y cualquiera puede unirse.",
                )
                net.security == Security.WEP -> SecurityIssue(
                    net, RiskLevel.HIGH,
                    "WEP está obsoleto y se rompe en minutos. Cambia a WPA2/WPA3.",
                )
                net.hasWps -> SecurityIssue(
                    net, RiskLevel.MEDIUM,
                    "WPS activo: vulnerable a ataques de PIN por fuerza bruta. Desactívalo.",
                )
                net.security == Security.WPA -> SecurityIssue(
                    net, RiskLevel.MEDIUM,
                    "WPA (v1) es débil frente a WPA2/WPA3. Actualiza si puedes.",
                )
                else -> null
            }
        }.sortedBy { it.level.ordinal }
}
