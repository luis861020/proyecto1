package com.redwifi.gestor.ui

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Devices
import androidx.compose.material.icons.rounded.TrackChanges
import androidx.compose.material.icons.rounded.Tune
import androidx.compose.material.icons.rounded.Wifi
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.redwifi.gestor.ui.permissions.PermissionGate
import com.redwifi.gestor.ui.screens.devices.DevicesScreen
import com.redwifi.gestor.ui.screens.networks.NetworksScreen
import com.redwifi.gestor.ui.screens.radar.RadarScreen
import com.redwifi.gestor.ui.screens.signal.SignalScreen
import com.redwifi.gestor.ui.screens.tools.ToolsScreen

enum class TopDest(val route: String, val label: String, val icon: ImageVector) {
    REDES("redes", "Redes", Icons.Rounded.Wifi),
    RADAR("radar", "Radar", Icons.Rounded.TrackChanges),
    DISPOSITIVOS("dispositivos", "Dispositivos", Icons.Rounded.Devices),
    HERRAMIENTAS("herramientas", "Herramientas", Icons.Rounded.Tune),
}

object Routes {
    const val SIGNAL = "senal"
}

@Composable
fun RedWifiApp() {
    PermissionGate {
        val navController = rememberNavController()
        val backStack by navController.currentBackStackEntryAsState()
        val currentRoute = backStack?.destination

        Scaffold(
            containerColor = MaterialTheme.colorScheme.background,
            bottomBar = {
                NavigationBar(containerColor = MaterialTheme.colorScheme.surface) {
                    TopDest.entries.forEach { dest ->
                        val selected = currentRoute?.hierarchy?.any { it.route == dest.route } == true
                        NavigationBarItem(
                            selected = selected,
                            onClick = {
                                navController.navigate(dest.route) {
                                    popUpTo(navController.graph.findStartDestination().id) {
                                        saveState = true
                                    }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            },
                            icon = { Icon(dest.icon, contentDescription = dest.label) },
                            label = { Text(dest.label) },
                            colors = NavigationBarItemDefaults.colors(
                                selectedIconColor = MaterialTheme.colorScheme.onPrimaryContainer,
                                indicatorColor = MaterialTheme.colorScheme.primaryContainer,
                            ),
                        )
                    }
                }
            },
        ) { inner ->
            NavHost(
                navController = navController,
                startDestination = TopDest.REDES.route,
                modifier = androidx.compose.ui.Modifier.padding(inner),
            ) {
                composable(TopDest.REDES.route) {
                    NetworksScreen(onOpenSignal = { navController.navigate(Routes.SIGNAL) })
                }
                composable(TopDest.RADAR.route) { RadarScreen() }
                composable(TopDest.DISPOSITIVOS.route) { DevicesScreen() }
                composable(TopDest.HERRAMIENTAS.route) { ToolsScreen() }
                composable(Routes.SIGNAL) {
                    SignalScreen(onBack = { navController.popBackStack() })
                }
            }
        }
    }
}
