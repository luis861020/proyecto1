package com.redwifi.gestor

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.redwifi.gestor.ui.RedWifiApp
import com.redwifi.gestor.ui.theme.RedWifiTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        setContent {
            RedWifiTheme {
                RedWifiApp()
            }
        }
    }
}
