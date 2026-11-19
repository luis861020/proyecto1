package com.redwifi.gestor.ui.screens.signal

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.redwifi.gestor.data.wifi.WifiScanner
import com.redwifi.gestor.domain.model.CurrentConnection
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

data class SignalUiState(
    val current: CurrentConnection? = null,
    val history: List<Int> = emptyList(),
)

class SignalViewModel(app: Application) : AndroidViewModel(app) {

    private val scanner = WifiScanner(app)
    private val _state = MutableStateFlow(SignalUiState())
    val state = _state.asStateFlow()

    init {
        viewModelScope.launch {
            while (isActive) {
                val conn = scanner.currentConnection()
                _state.update {
                    val newHistory = if (conn != null) {
                        (it.history + conn.rssi).takeLast(MAX_POINTS)
                    } else it.history
                    it.copy(current = conn, history = newHistory)
                }
                delay(1000)
            }
        }
    }

    companion object {
        private const val MAX_POINTS = 60
    }
}
