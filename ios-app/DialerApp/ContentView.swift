import SwiftUI
import Network

struct ContentView: View {
    @EnvironmentObject var server: DialServer
    @State private var ipAddress = ""

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // App 图标
                Image(systemName: "phone.circle.fill")
                    .font(.system(size: 72))
                    .foregroundColor(.blue)

                Text("一键拨号助手")
                    .font(.title)
                    .bold()

                // 状态卡片
                VStack(spacing: 16) {
                    statusRow(label: "服务状态", value: server.isRunning ? "运行中" : "已停止",
                              color: server.isRunning ? .green : .red)

                    Divider()

                    statusRow(label: "IP 地址", value: ipAddress.isEmpty ? "获取中..." : ipAddress,
                              color: .primary)

                    statusRow(label: "端口", value: "8888", color: .primary)

                    Divider()

                    if server.isRunning {
                        HStack {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.green)
                            Text("服务运行中，可正常拨号")
                                .foregroundColor(.green)
                                .font(.subheadline)
                        }
                    } else {
                        HStack {
                            Image(systemName: "exclamationmark.circle.fill")
                                .foregroundColor(.orange)
                            Text("服务未启动")
                                .foregroundColor(.orange)
                                .font(.subheadline)
                        }
                    }
                }
                .padding()
                .background(Color(.secondarySystemBackground))
                .cornerRadius(16)

                // 启动/停止按钮
                Button(action: {
                    if server.isRunning {
                        server.stop()
                    } else {
                        server.start()
                    }
                }) {
                    HStack {
                        Image(systemName: server.isRunning ? "stop.fill" : "play.fill")
                        Text(server.isRunning ? "停止服务" : "启动服务")
                            .font(.headline)
                    }
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(server.isRunning ? Color.red : Color.blue)
                    .cornerRadius(12)
                }

                // 使用说明
                VStack(alignment: .leading, spacing: 10) {
                    Text("使用说明")
                        .font(.headline)

                    Label("点击「启动服务」开启 HTTP 服务", systemImage: "1.circle")
                    Label("在电脑端 .env 填入上面的 IP 地址", systemImage: "2.circle")
                    Label("电脑端点击联系人即可拨号", systemImage: "3.circle")
                    Label("请保持 App 在前台运行", systemImage: "4.circle")
                }
                .font(.caption)
                .foregroundColor(.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .padding()
        }
        .onAppear {
            ipAddress = getIPAddress()
        }
    }

    private func statusRow(label: String, value: String, color: Color) -> some View {
        HStack {
            Text(label)
                .foregroundColor(.secondary)
            Spacer()
            Text(value)
                .foregroundColor(color)
                .font(.system(.body, design: .monospaced))
        }
    }

    /// 获取本机 WiFi IP 地址
    private func getIPAddress() -> String {
        var address = ""

        // 优先获取 WiFi 地址
        let getWiFiAddress: String? = {
            var ifaddr: UnsafeMutablePointer<ifaddrs>?
            guard getifaddrs(&ifaddr) == 0 else { return nil }
            defer { freeifaddrs(ifaddr) }

            var ptr = ifaddr
            while ptr != nil {
                let interface = ptr!.pointee
                let addrFamily = interface.ifa_addr.pointee.sa_family
                if addrFamily == UInt8(AF_INET) {
                    let name = String(cString: interface.ifa_name)
                    if name.hasPrefix("en") || name.hasPrefix("pdp_ip") {
                        var hostname = [CChar](repeating: 0, count: Int(NI_MAXHOST))
                        getnameinfo(
                            interface.ifa_addr,
                            socklen_t(interface.ifa_addr.pointee.sa_len),
                            &hostname, socklen_t(hostname.count),
                            nil, 0, NI_NUMERICHOST
                        )
                        let ip = String(cString: hostname)
                        if !ip.isEmpty && ip != "127.0.0.1" {
                            return ip
                        }
                    }
                }
                ptr = interface.ifa_next
            }
            return nil
        }()

        if let wifi = getWiFiAddress, !wifi.isEmpty {
            address = wifi
        }

        return address
    }
}
