package com.redwifi.gestor.data.net

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.widget.Toast

/**
 * Herramientas relacionadas con el router.
 *
 * IMPORTANTE (honestidad técnica): una app Android normal NO puede expulsar por la
 * fuerza a un dispositivo de una red WiFi (eso requeriría enviar tramas de
 * de-autenticación, que el sistema bloquea, y sólo es posible con root/hardware
 * especial). La forma legítima de desconectar a alguien de TU red es desde el
 * panel de administración del router. Esta utilidad lleva al usuario allí.
 */
object RouterTools {

    fun openRouterAdmin(context: Context, gatewayIp: String?) {
        val ip = gatewayIp?.takeIf { it.isNotBlank() } ?: "192.168.1.1"
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse("http://$ip")).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        runCatching { context.startActivity(intent) }.onFailure {
            Toast.makeText(
                context,
                "No se pudo abrir el navegador. Panel del router: http://$ip",
                Toast.LENGTH_LONG,
            ).show()
        }
    }
}
