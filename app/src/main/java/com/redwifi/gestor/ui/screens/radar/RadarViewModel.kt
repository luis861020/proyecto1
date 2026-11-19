package com.redwifi.gestor.ui.screens.radar

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.redwifi.gestor.data.wifi.WifiScanner
import com.redwifi.gestor.domain.model.WifiNetwork
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class RadarUiState(
    val networks: List<WifiNetwork> = emptyList(),
    val loading: Boolean = true,
)

class RadarViewModel(app: Application) : AndroidViewModel(app) {

    private val scanner = WifiScanner(app)
    private val _state = MutableStateFlow(RadarUiState())
    val state = _state.asStateFlow()

    init {
        viewModelScope.launch {
            scanner.networksFlow().collect { nets ->
                _state.update { it.copy(networks = nets, loading = false) }
            }
        }
    }

    fun refresh() = scanner.requestScan()
}
