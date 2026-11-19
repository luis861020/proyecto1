package com.redwifi.gestor.ui.screens.networks

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.redwifi.gestor.data.wifi.WifiScanner
import com.redwifi.gestor.domain.model.CurrentConnection
import com.redwifi.gestor.domain.model.WifiNetwork
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

data class NetworksUiState(
    val networks: List<WifiNetwork> = emptyList(),
    val current: CurrentConnection? = null,
    val wifiEnabled: Boolean = true,
    val loading: Boolean = true,
)

class NetworksViewModel(app: Application) : AndroidViewModel(app) {

    private val scanner = WifiScanner(app)

    private val _state = MutableStateFlow(NetworksUiState())
    val state = _state.asStateFlow()

    init {
        viewModelScope.launch {
            scanner.networksFlow().collect { nets ->
                _state.update {
                    it.copy(
                        networks = nets,
                        loading = false,
                        wifiEnabled = scanner.isWifiEnabled(),
                    )
                }
            }
        }
        viewModelScope.launch {
            while (isActive) {
                _state.update {
                    it.copy(
                        current = scanner.currentConnection(),
                        wifiEnabled = scanner.isWifiEnabled(),
                    )
                }
                delay(2500)
            }
        }
    }

    fun refresh() {
        scanner.requestScan()
    }
}
