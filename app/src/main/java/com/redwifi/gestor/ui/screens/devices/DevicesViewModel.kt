package com.redwifi.gestor.ui.screens.devices

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.redwifi.gestor.data.net.DeviceScanner
import com.redwifi.gestor.domain.model.ConnectedDevice
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class DevicesUiState(
    val scanning: Boolean = false,
    val progress: Float = 0f,
    val subnet: String? = null,
    val gatewayIp: String? = null,
    val devices: List<ConnectedDevice> = emptyList(),
    val hasScanned: Boolean = false,
)

class DevicesViewModel(app: Application) : AndroidViewModel(app) {

    private val scanner = DeviceScanner(app)
    private val _state = MutableStateFlow(DevicesUiState())
    val state = _state.asStateFlow()

    fun scan() {
        if (_state.value.scanning) return
        _state.update { it.copy(scanning = true, progress = 0f, devices = emptyList()) }
        viewModelScope.launch {
            val outcome = scanner.scan(
                onProgress = { done, total ->
                    if (done % 8 == 0 || done == total) {
                        _state.update { it.copy(progress = done.toFloat() / total) }
                    }
                },
            )
            _state.update {
                it.copy(
                    scanning = false,
                    progress = 1f,
                    subnet = outcome.subnet,
                    gatewayIp = outcome.gatewayIp,
                    devices = outcome.devices,
                    hasScanned = true,
                )
            }
        }
    }
}
