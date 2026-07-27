package com.dialer

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.net.Uri
import android.os.Build
import android.os.IBinder
import android.util.Log
import fi.iki.elonen.NanoHTTPD
import org.json.JSONObject

class DialService : Service() {

    companion object {
        private const val TAG = "DialService"
        private const val NOTIFICATION_ID = 1
        private const val CHANNEL_ID = "dialer_service_channel"
        const val HTTP_PORT = 8888
    }

    private var server: DialServer? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.i(TAG, "服务启动")
        startForegroundCompat()
        try {
            server = DialServer(HTTP_PORT)
            server?.start(5000, false)
            Log.i(TAG, "HTTP 服务已启动，端口: $HTTP_PORT")
        } catch (e: Exception) {
            Log.e(TAG, "HTTP 服务启动失败", e)
            stopSelf()
            return START_NOT_STICKY
        }
        return START_STICKY
    }

    override fun onDestroy() {
        server?.stop()
        server = null
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun startForegroundCompat() {
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(CHANNEL_ID, "拨号服务", NotificationManager.IMPORTANCE_LOW)
            channel.description = "保持拨号服务在后台运行"
            channel.setShowBadge(false)
            manager.createNotificationChannel(channel)
        }
        val notification = buildNotification()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }
    }

    private fun buildNotification(): Notification {
        val pendingIntent = PendingIntent.getActivity(
            this, 0, Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )
        return androidx.core.app.NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("一键拨号服务运行中")
            .setContentText("端口: $HTTP_PORT | 等待拨号指令")
            .setSmallIcon(R.drawable.ic_phone_notify)
            .setContentIntent(pendingIntent)
            .setOngoing(true).setSilent(true).build()
    }

    inner class DialServer(port: Int) : NanoHTTPD(port) {

        override fun serve(session: IHTTPSession): Response {
            val uri = session.uri
            Log.i(TAG, "${session.method} $uri")
            return when {
                uri == "/ping" -> handlePing()
                uri == "/dial" && session.method == Method.POST -> handleDial(session)
                uri == "/" -> handleIndex()
                else -> jsonResponse(Response.Status.NOT_FOUND,
                    """{"success":false,"message":"404"}""")
            }
        }

        private fun handlePing(): Response {
            val json = JSONObject()
                .put("status", "ok")
                .put("device", Build.MODEL)
                .put("port", HTTP_PORT)
            return jsonResponse(Response.Status.OK, json.toString())
        }

        private fun handleDial(session: IHTTPSession): Response {
            val files = HashMap<String, String>()
            try {
                session.parseBody(files)
            } catch (e: Exception) {
                return jsonError(Response.Status.BAD_REQUEST, "请求体解析失败")
            }
            val body = files["postData"] ?: ""
            val phone = try {
                JSONObject(body).optString("phone", "")
            } catch (e: Exception) { "" }

            if (phone.isEmpty()) return jsonError(Response.Status.BAD_REQUEST, "号码为空")
            if (!phone.matches(Regex("^[\\d+]+$"))) return jsonError(Response.Status.BAD_REQUEST, "号码格式无效")

            return try {
                val intent = Intent(Intent.ACTION_CALL, Uri.parse("tel:$phone"))
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                startActivity(intent)
                Log.i(TAG, "拨号成功: $phone")
                val json = JSONObject().put("success", true).put("message", "正在拨打 $phone").put("phone", phone)
                jsonResponse(Response.Status.OK, json.toString())
            } catch (e: SecurityException) {
                jsonError(Response.Status.INTERNAL_ERROR, "拨号权限被拒绝")
            } catch (e: Exception) {
                jsonError(Response.Status.INTERNAL_ERROR, "拨号失败: ${e.message}")
            }
        }

        private fun handleIndex(): Response {
            val html = """<!DOCTYPE html><html><head><meta charset="utf-8">
                <meta name="viewport" content="width=device-width,initial-scale=1">
                <title>一键拨号助手</title>
                <style>body{font-family:sans-serif;text-align:center;padding:40px;background:#f0f4f8}
                .card{background:#fff;border-radius:16px;padding:32px;max-width:400px;margin:0 auto;box-shadow:0 2px 8px rgba(0,0,0,.1)}
                h1{color:#2563eb;margin-bottom:8px}
                .status{display:inline-block;padding:4px 16px;border-radius:20px;background:#dcfce7;color:#16a34a;font-weight:600}
                .info{color:#64748b;margin-top:16px}.port{font-size:2em;font-weight:700;color:#1e293b}</style>
                </head><body><div class="card"><h1>一键拨号助手</h1>
                <span class="status">服务运行中</span><p class="info">设备: ${Build.MODEL}</p>
                <p class="port">$HTTP_PORT</p><p class="info">HTTP 服务端口</p></div></body></html>""".trimIndent()
            return newFixedLengthResponse(Response.Status.OK, "text/html", html)
        }

        private fun jsonResponse(status: Response.Status, json: String): Response =
            newFixedLengthResponse(status, "application/json", json)

        private fun jsonError(status: Response.Status, message: String): Response {
            val json = JSONObject().put("success", false).put("message", message)
            return jsonResponse(status, json.toString())
        }
    }
}
