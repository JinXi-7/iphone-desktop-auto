package com.dialer

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import java.net.NetworkInterface
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.view.View
import android.widget.Button
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import java.net.Inet4Address

class MainActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "MainActivity"
    }

    private lateinit var tvIpAddress: TextView
    private lateinit var tvPort: TextView
    private lateinit var tvStatus: TextView
    private lateinit var btnToggle: Button

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { result ->
        val callGranted = result[Manifest.permission.CALL_PHONE] == true
        if (!callGranted) {
            tvStatus.text = "需要拨号权限才能自动拨号"
            tvStatus.setTextColor(getColor(R.color.status_error))
        }
        updateUI()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        tvIpAddress = findViewById(R.id.tv_ip_address)
        tvPort = findViewById(R.id.tv_port)
        tvStatus = findViewById(R.id.tv_status)
        btnToggle = findViewById(R.id.btn_toggle)

        btnToggle.setOnClickListener {
            if (isServiceRunning()) {
                stopService(Intent(this, DialService::class.java))
            } else {
                requestPermissionsAndStart()
            }
            // 延迟刷新 UI
            btnToggle.postDelayed({ updateUI() }, 500)
        }

        requestPermissions()
        updateUI()
    }

    override fun onResume() {
        super.onResume()
        updateUI()
    }

    private fun requestPermissions() {
        val perms = mutableListOf(Manifest.permission.CALL_PHONE)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            perms.add(Manifest.permission.POST_NOTIFICATIONS)
        }
        val toRequest = perms.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        if (toRequest.isNotEmpty()) {
            permissionLauncher.launch(toRequest.toTypedArray())
        }
    }

    private fun requestPermissionsAndStart() {
        val callGranted = ContextCompat.checkSelfPermission(this, Manifest.permission.CALL_PHONE) == PackageManager.PERMISSION_GRANTED
        if (!callGranted) {
            permissionLauncher.launch(arrayOf(Manifest.permission.CALL_PHONE))
            return
        }
        startService()
    }

    private fun startService() {
        val intent = Intent(this, DialService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent)
        } else {
            startService(intent)
        }
    }

    private fun isServiceRunning(): Boolean {
        val manager = getSystemService(android.app.ActivityManager::class.java)
        return manager.getRunningServices(Int.MAX_VALUE).any { it.service.className == DialService::class.java.name }
    }

    private fun updateUI() {
        val ip = getLocalIpAddress()
        tvIpAddress.text = if (ip != "未连接WiFi") "http://$ip" else ip
        tvPort.text = DialService.HTTP_PORT.toString()

        val running = isServiceRunning()
        if (running) {
            tvStatus.text = "服务运行中"
            tvStatus.setTextColor(getColor(R.color.status_ok))
            btnToggle.text = "停止服务"
            btnToggle.setBackgroundColor(getColor(R.color.btn_stop))
        } else {
            tvStatus.text = "服务未启动"
            tvStatus.setTextColor(getColor(R.color.status_error))
            btnToggle.text = "启动服务"
            btnToggle.setBackgroundColor(getColor(R.color.btn_start))
        }
    }

    private fun getLocalIpAddress(): String {
        try {
            val interfaces = NetworkInterface.getNetworkInterfaces()
            while (interfaces.hasMoreElements()) {
                val intf = interfaces.nextElement()
                if (intf.isUp && !intf.isLoopback) {
                    val addrs = intf.inetAddresses
                    while (addrs.hasMoreElements()) {
                        val addr = addrs.nextElement()
                        if (!addr.isLoopbackAddress && addr is Inet4Address) {
                            return addr.hostAddress ?: "未知"
                        }
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "获取IP失败", e)
        }
        return "未连接WiFi"
    }
}
