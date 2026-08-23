package com.getpromptide.random_reminder_app

import android.content.Intent
import android.provider.Settings
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            "getpromptide.com/random_reminder/device_settings",
        ).setMethodCallHandler { call, result ->
            when (call.method) {
                "openBatteryOptimizationSettings" -> {
                    try {
                        startActivity(Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS))
                        result.success(null)
                    } catch (error: Exception) {
                        result.error("settings_unavailable", error.message, null)
                    }
                }
                else -> result.notImplemented()
            }
        }
    }
}
