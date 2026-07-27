import Foundation
import Swifter
import UIKit
import AVFoundation

/// HTTP 服务器 + 拨号逻辑（与安卓版功能对等）
class DialServer: ObservableObject {

    @Published var isRunning = false

    private var server: HttpServer?
    private var audioPlayer: AVAudioPlayer?

    // MARK: - 启动/停止

    func start() {
        server = HttpServer()

        // GET /ping - 健康检查
        server?["/ping"] = { [weak self] _ in
            let device = self?.deviceModel ?? "iPhone"
            return .ok(.json([
                "status": "ok",
                "device": device,
            ]))
        }

        // POST /dial - 拨号
        server?["/dial"] = { request in
            // 解析请求体（Swifter body 为 [UInt8] 类型）
            let data = Data(request.body)
            guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let phone = json["phone"] as? String
            else {
                return .badRequest(.json([
                    "status": "error",
                    "message": "缺少 phone 参数",
                ]))
            }

            // 校验电话号码（仅允许数字和 +）
            let cleaned = phone.filter { $0.isNumber || $0 == "+" }
            guard !cleaned.isEmpty else {
                return .badRequest(.json([
                    "status": "error",
                    "message": "无效的电话号码",
                ]))
            }

            // 在主线程发起拨号
            DispatchQueue.main.async {
                if let url = URL(string: "tel://\(cleaned)") {
                    UIApplication.shared.open(url) { success in
                        print("拨号结果: \(success) - \(cleaned)")
                    }
                }
            }

            return .ok(.json([
                "status": "ok",
                "message": "正在拨号: \(cleaned)",
            ]))
        }

        // GET / - 浏览器状态页
        server?["/"] = { [weak self] _ in
            let device = self?.deviceModel ?? "iPhone"
            return .ok(.html("""
            <html>
            <head><meta charset="utf-8"><title>一键拨号助手</title></head>
            <body style="font-family: -apple-system, sans-serif; text-align: center; padding: 50px;">
            <h1>一键拨号助手</h1>
            <p>HTTP 服务运行中</p>
            <p>设备: \(device)</p>
            </body>
            </html>
            """))
        }

        do {
            try server?.start(8888)
            DispatchQueue.main.async {
                self.isRunning = true
            }
            // 播放静音音频，保持后台运行
            startBackgroundAudio()
            print("DialServer started on port 8888")
        } catch {
            print("Failed to start server: \(error)")
        }
    }

    func stop() {
        server?.stop()
        server = nil
        stopBackgroundAudio()
        DispatchQueue.main.async {
            self.isRunning = false
        }
        print("DialServer stopped")
    }

    // MARK: - 设备信息

    private var deviceModel: String {
        var systemInfo = utsname()
        uname(&systemInfo)
        return withUnsafePointer(to: &systemInfo.machine) { ptr in
            String(cString: UnsafeRawPointer(ptr).assumingMemoryBound(to: CChar.self))
        }
    }

    // MARK: - 后台保活（静音音频）

    /// 播放无声音频，利用 audio 后台模式保持 App 存活
    private func startBackgroundAudio() {
        let session = AVAudioSession.sharedInstance()
        try? session.setCategory(.playback, mode: .default, options: [.mixWithOthers])
        try? session.setActive(true)

        audioPlayer = try? AVAudioPlayer(data: SilentAudioGenerator.wavData())
        audioPlayer?.numberOfLoops = -1   // 无限循环
        audioPlayer?.volume = 0            // 静音
        audioPlayer?.play()
    }

    private func stopBackgroundAudio() {
        audioPlayer?.stop()
        audioPlayer = nil
        try? AVAudioSession.sharedInstance().setActive(false, options: [.notifyOthersOnDeactivation])
    }
}

/// 生成 1 秒静音 WAV 文件数据
enum SilentAudioGenerator {
    static func wavData(sampleRate: Int = 44100, durationSeconds: Int = 1) -> Data {
        let numSamples = sampleRate * durationSeconds
        let dataSize = numSamples * 2  // 16-bit = 2 bytes/sample
        var data = Data()

        // RIFF header
        data.append(Data("RIFF".utf8))
        appendUInt32(&data, UInt32(36 + dataSize))
        data.append(Data("WAVE".utf8))

        // fmt chunk
        data.append(Data("fmt ".utf8))
        appendUInt32(&data, 16)              // subchunk1 size
        appendUInt16(&data, 1)               // PCM
        appendUInt16(&data, 1)               // mono
        appendUInt32(&data, UInt32(sampleRate))
        appendUInt32(&data, UInt32(sampleRate * 2))  // byte rate
        appendUInt16(&data, 2)               // block align
        appendUInt16(&data, 16)              // bits per sample

        // data chunk
        data.append(Data("data".utf8))
        appendUInt32(&data, UInt32(dataSize))
        data.append(Data(count: dataSize))  // 全零 = 静音

        return data
    }

    private static func appendUInt16(_ data: inout Data, _ value: UInt16) {
        data.append(contentsOf: [
            UInt8(value & 0xFF),
            UInt8((value >> 8) & 0xFF),
        ])
    }

    private static func appendUInt32(_ data: inout Data, _ value: UInt32) {
        data.append(contentsOf: [
            UInt8(value & 0xFF),
            UInt8((value >> 8) & 0xFF),
            UInt8((value >> 16) & 0xFF),
            UInt8((value >> 24) & 0xFF),
        ])
    }
}
