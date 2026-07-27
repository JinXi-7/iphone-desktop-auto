import SwiftUI

@main
struct DialerApp: App {
    @StateObject private var server = DialServer()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(server)
        }
    }
}
