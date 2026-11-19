package com.redwifi.gestor.data.net

/**
 * Búsqueda de fabricante a partir del prefijo OUI (primeros 3 bytes de la MAC).
 * Es un subconjunto curado de los fabricantes más comunes en redes domésticas;
 * no pretende ser la base IEEE completa. Lo que no se reconoce queda como null.
 */
object OuiDatabase {

    private val vendors: Map<String, String> = mapOf(
        "FCFBFB" to "Apple", "F0F61C" to "Apple", "A4B197" to "Apple",
        "3C0754" to "Apple", "D0817A" to "Apple", "8C8590" to "Apple",
        "001A11" to "Google", "F4F5E8" to "Google", "A47733" to "Google",
        "D83134" to "Roku", "B827EB" to "Raspberry Pi", "DCA632" to "Raspberry Pi",
        "E45F01" to "Raspberry Pi", "001D43" to "Samsung", "5001BB" to "Samsung",
        "8425DB" to "Samsung", "D0176A" to "Samsung", "001632" to "Samsung",
        "F0272D" to "Xiaomi", "64B473" to "Xiaomi", "286C07" to "Xiaomi",
        "7C1DD9" to "Xiaomi", "001788" to "Philips Hue", "D073D5" to "LIFX",
        "B4E62D" to "Espressif (ESP)", "2462AB" to "Espressif (ESP)",
        "A020A6" to "Espressif (ESP)", "001122" to "Cimsys",
        "C83A35" to "Tenda", "000C43" to "Ralink/Router", "001374" to "Amazon",
        "44650D" to "Amazon", "F0D2F1" to "Amazon", "68544C" to "TP-Link",
        "50C7BF" to "TP-Link", "A42BB0" to "TP-Link", "9C5322" to "TP-Link",
        "001E2A" to "Netgear", "2C3033" to "Netgear", "20E52A" to "Netgear",
        "0018E7" to "Cameo/Router", "001F3F" to "AVM FRITZ!Box",
        "3810D5" to "AVM FRITZ!Box", "C0A0BB" to "D-Link", "14D64D" to "D-Link",
        "001CF0" to "D-Link", "00037F" to "Atheros", "0017C2" to "Movistar",
        "F8D111" to "TP-Link", "E894F6" to "TP-Link", "001E58" to "WistronNeweb",
        "D4CA6D" to "Routerboard/MikroTik", "4C5E0C" to "MikroTik",
        "64D154" to "Huawei", "48AD08" to "Huawei", "00259E" to "Huawei",
        "AC853D" to "Huawei", "80B686" to "Huawei", "FCC233" to "Intel",
        "3C9509" to "Intel", "A0C589" to "Intel", "001B77" to "Intel",
        "001124" to "Microsoft", "C83F26" to "Sony", "FC0FE6" to "Sony",
    )

    /** @param mac en formato "aa:bb:cc:dd:ee:ff". */
    fun lookup(mac: String?): String? {
        if (mac.isNullOrBlank()) return null
        val prefix = mac.replace(":", "").replace("-", "").uppercase().take(6)
        if (prefix.length < 6) return null
        return vendors[prefix]
    }
}
