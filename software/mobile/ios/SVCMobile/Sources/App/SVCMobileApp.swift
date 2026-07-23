import SwiftUI

@main
struct SVCMobileApp: App {
    @StateObject private var viewModel = AppViewModel(
        repository: MockDeviceRepository()
    )

    var body: some Scene {
        WindowGroup {
            RootView(viewModel: viewModel)
        }
    }
}
