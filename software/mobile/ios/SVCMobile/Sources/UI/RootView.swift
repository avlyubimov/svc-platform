import SwiftUI

struct RootView: View {
    @ObservedObject var viewModel: AppViewModel
    @StateObject private var appearance = AppearanceStore()
    @StateObject private var ridePreferences = RidePreferences()
    @State private var selectedScreen: PrimaryScreen = .dashboard
    @State private var rideModePresented = true
    @State private var rideSessionID = UUID()
    @State private var showSettings = false
    @State private var showStartup = !ProcessInfo.processInfo.arguments.contains(
        "SVC_SKIP_STARTUP"
    )
    @State private var replayToken = UUID()

    private var presentationDemo: Bool {
        ProcessInfo.processInfo.arguments.contains("SVC_TFT_DEMO")
    }

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
                                        ridePreferences: ridePreferences,
                                        telemetry: viewModel.device.telemetry,
                                        previewStartup: previewStartup
                                    )
                                }
                            } label: {
                                Image(systemName: "line.3.horizontal")
                            }
                        }
                    }
                    .overlay(alignment: .top) {
                        if !rideModePresented, let criticalWarning {
                            CriticalWarningCard(warning: criticalWarning)
                                .padding()
                        }
                    }
            }
            .tint(appearance.brandPack.accentColor)
            .preferredColorScheme(.dark)
        }
        .background(SVCTheme.background)
        .background {
            RideModePresenter(isPresented: $rideModePresented) {
                ZStack {
                    RideModeView(
                        telemetry: viewModel.device.telemetry,
                        connectionState: viewModel.device.connectionState,
                        isConnecting: viewModel.isConnecting,
                        profile: ridePreferences.vehicleProfile,
                        ridePreferences: ridePreferences,
                        reduceMotion: appearance.forceReduceMotion,
                        demoMode: presentationDemo,
                        exitRideMode: exitRideMode,
                        openSettings: openRideSettings
                    )
                    .id(rideSessionID)

                    if showStartup {
                        StartupAnimationView(
                            brandPack: appearance.brandPack,
                            timeline: appearance.startupTimeline,
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
            }
        }
        .sheet(isPresented: $showSettings) {
            NavigationStack {
                SettingsView(
                    appearance: appearance,
                    ridePreferences: ridePreferences,
                    telemetry: viewModel.device.telemetry,
                    previewStartup: previewStartup
                )
                .toolbar {
                    ToolbarItem(placement: .confirmationAction) {
                        Button("Done") { showSettings = false }
                    }
                }
            }
        }
        .onAppear {
            selectedScreen = appearance.restoredScreen()
            viewModel.beginStartupTasks()
        }
    }

    @ViewBuilder
    private var destination: some View {
        switch selectedScreen {
        case .dashboard:
            VStack(spacing: 18) {
                Image(systemName: "gauge.with.dots.needle.67percent")
                    .font(.system(size: 54))
                    .foregroundStyle(appearance.brandPack.accentColor)
                Text("Ride Mode is closed")
                    .font(.title2.weight(.semibold))
                Button("Enter Ride Mode", action: enterRideMode)
                    .buttonStyle(.borderedProminent)
                    .accessibilityIdentifier("enterRideMode")
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(SVCTheme.background)
            .navigationTitle("SVC Mobile")
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
        if screen == .dashboard {
            enterRideMode()
            return
        }
        selectedScreen = screen
        appearance.select(screen)
    }

    private func previewStartup() {
        replayToken = UUID()
        showStartup = true
        showSettings = false
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            enterRideMode()
        }
    }

    private func enterRideMode() {
        selectedScreen = .dashboard
        appearance.select(.dashboard)
        rideSessionID = UUID()
        rideModePresented = true
    }

    private func exitRideMode() {
        rideModePresented = false
    }

    private func openRideSettings() {
        rideModePresented = false
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            showSettings = true
        }
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
