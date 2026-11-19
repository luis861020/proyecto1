package com.redwifi.gestor.ui.screens.tools

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.redwifi.gestor.data.wifi.ChannelAnalyzer
import com.redwifi.gestor.data.wifi.ChannelRecommendation
import com.redwifi.gestor.data.wifi.SecurityAudit
import com.redwifi.gestor.data.wifi.SecurityIssue
import com.redwifi.gestor.data.wifi.WifiScanner
import com.redwifi.gestor.domain.model.Band
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class ToolsUiState(
    val totalNetworks: Int = 0,
    val count24: Int = 0,
    val count5: Int = 0,
    val count6: Int = 0,
    val recommendation: ChannelRecommendation? = null,
    val occupancy24: Map<Int, Int> = emptyMap(),
    val occupancy5: Map<Int, Int> = emptyMap(),
    val issues: List<SecurityIssue> = emptyList(),
)

class ToolsViewModel(app: Application) : AndroidViewModel(app) {

    private val scanner = WifiScanner(app)
    private val _state = MutableStateFlow(ToolsUiState())
    val state = _state.asStateFlow()

    init {
        viewModelScope.launch {
            scanner.networksFlow().collect { nets ->
                _state.update {
                    it.copy(
                        totalNetworks = nets.size,
                        count24 = nets.count { n -> n.band == Band.GHZ_2_4 },
                        count5 = nets.count { n -> n.band == Band.GHZ_5 },
                        count6 = nets.count { n -> n.band == Band.GHZ_6 },
                        recommendation = ChannelAnalyzer.recommend24GHz(nets),
                        occupancy24 = ChannelAnalyzer.occupancy(nets, Band.GHZ_2_4),
                        occupancy5 = ChannelAnalyzer.occupancy(nets, Band.GHZ_5),
                        issues = SecurityAudit.audit(nets),
                    )
                }
            }
        }
    }

    fun refresh() = scanner.requestScan()
}
