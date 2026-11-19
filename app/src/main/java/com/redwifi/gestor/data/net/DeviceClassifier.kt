package com.redwifi.gestor.data.net

import com.redwifi.gestor.domain.model.DeviceType

/**
 * Deduce el tipo de dispositivo (celular, computador, TV, etc.) a partir del
 * nombre de host y del fabricante (OUI). Es heurístico: acierta con nombres
 * reconocibles (iPhone, DESKTOP-xxx, Roku...) pero los nombres crípticos de
 * algunos equipos quedan como "Dispositivo".
 */
object DeviceClassifier {

    fun classify(
        hostName: String?,
        vendor: String?,
        isGateway: Boolean,
        isThisDevice: Boolean,
    ): DeviceType {
        if (isThisDevice) return DeviceType.THIS_PHONE
        if (isGateway) return DeviceType.ROUTER

        val s = ("${hostName.orEmpty()} ${vendor.orEmpty()}").lowercase()
        fun has(vararg keys: String) = keys.any { s.contains(it) }

        return when {
            has(
                "iphone", "ipad", "ipod", "android", "galaxy", "redmi", "poco",
                "xiaomi", "huawei", "honor", "oneplus", "pixel", "moto", "motorola",
                "oppo", "vivo", "realme", "nokia", "sm-g", "sm-a", "sm-n", "sm-s",
                "-phone", "celular", "phone", "mobile",
            ) -> DeviceType.PHONE

            has(
                "macbook", "imac", "mac-", "desktop", "laptop", "-pc", "pc-", "_pc",
                "thinkpad", "dell", "hp-", "lenovo", "asus", "msi", "surface",
                "windows", "ubuntu", "linux", "fedora", "debian", "computer",
                "notebook", "workstation",
            ) -> DeviceType.COMPUTER

            has(
                "tv", "roku", "chromecast", "firestick", "fire-tv", "firetv",
                "appletv", "apple-tv", "bravia", "shield", "smarttv", "smart-tv",
                "webos", "mibox", "mi-box", "android-tv", "googlehome", "google-home",
                "nest", "vizio", "hisense", "tcl", "streaming",
            ) -> DeviceType.TV

            has("playstation", "ps4", "ps5", "xbox", "nintendo", "switch") ->
                DeviceType.CONSOLE

            has("printer", "epson", "canon", "brother", "-print", "officejet", "laserjet") ->
                DeviceType.PRINTER

            has(
                "esp-", "esp_", "espressif", "tuya", "sonoff", "shelly", "tasmota",
                "smartplug", "smart-plug", "bulb", "lifx", "hue", "camera", "ipcam",
                "-cam", "webcam", "ring-", "echo", "alexa", "sonos", "lumi", "smart",
            ) -> DeviceType.IOT

            else -> DeviceType.UNKNOWN
        }
    }
}
