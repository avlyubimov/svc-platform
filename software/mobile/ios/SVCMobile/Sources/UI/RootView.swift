import SwiftUI

struct RootView: View {
    @ObservedObject var viewModel: AppViewModel
    @StateObject private var appearance = AppearanceStore()
    @State private var selectedScreen: PrimaryScreen = .dashboard
    @State private var showStartup = true
    @State private var replayToken = UUID()

    private var criticalWarning: DeviceWarning? {
        viewModel.device.telemetry.warnings.first {
            $0.active && $0.severity.lowercased() == "critical"
        }
    }

    var body: some View {
        ZStack {
            NavigationStack {
                destination
                    .toolbar {
                        ToolbarItem(placement: .topBarTrailing) {
                            Menu {
                                ForEach(PrimaryScreen.allCases) { screen in
                                    Button(screen.title) { select(screen) }
                                }
                                Divider()
                                NavigationLink("Search and pair") {
                                    PairingView(viewModel: viewModel)
                                }
                                NavigationLink("Settings") {
                                    SettingsView(
                                        appearance: appearance,
                                        previewStartup: previewStartup
                                    )
                                }
                            } label: {
                                Image(systemName: "line.3.horizontal")
                            }
                        }
                    }
                    .overlay(alignment: .top) {
                        if !showStartup, let criticalWarning {
                            CriticalWarningCard(warning: criticalWarning)
                                .padding()
                        }
                    }
            }
            .tint(appearance.brandPack.accentColor)
            .preferredColorScheme(.dark)

            if showStartup {
                StartupAnimationView(
                    brandPack: appearance.brandPack,
                    animationEnabled: appearance.animationEnabled,
                    reduceMotion: appearance.forceReduceMotion,
                    critical: criticalWarning != nil,
                    replayToken: replayToken
                ) {
                    showStartup = false
                }
                .transition(.identity)
                .zIndex(10)
            }
        }
        .background(SVCTheme.background)
        .onAppear {
            selectedScreen = appearance.restoredScreen()
            viewModel.beginStartupTasks()
        }
    }

    @ViewBuilder
    private var destination: some View {
        switch selectedScreen {
        case .dashboard:
            DashboardView(
                telemetry: viewModel.device.telemetry,
                isConnecting: viewModel.isConnecting
            )
        case .channels:
            ChannelsView(channels: viewModel.device.telemetry.channels)
        case .canTelemetry:
            CANTelemetryView(telemetry: viewModel.device.telemetry)
        case .navigation:
            ContentUnavailableView(
                "Navigation unavailable",
                systemImage: "location.slash",
                description: Text("No navigation provider is configured.")
            )
            .navigationTitle("Navigation status")
        case .diagnostics:
            DiagnosticsView(telemetry: viewModel.device.telemetry)
        }
    }

    private func select(_ screen: PrimaryScreen) {
        selectedScreen = screen
        appearance.select(screen)
    }

    private func previewStartup() {
        replayToken = UUID()
        showStartup = true
    }
}

private struct CriticalWarningCard: View {
    let warning: DeviceWarning

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: "exclamationmark.triangle.fill")
            Text(warning.message)
                .font(.headline)
            Spacer()
        }
        .foregroundStyle(.white)
        .padding()
        .background(SVCTheme.critical, in: RoundedRectangle(cornerRadius: 12))
    }
}
