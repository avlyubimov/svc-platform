import SwiftUI

struct SettingsView: View {
    @ObservedObject var appearance: AppearanceStore
    let previewStartup: () -> Void
    @State private var telemetryRate = 2.0
    @State private var calibrationMode = false

    var body: some View {
        Form {
            Section("Appearance") {
                Picker("Vehicle profile", selection: $appearance.profileId) {
                    ForEach(appearance.availableProfiles) { profile in
                        Text(profile.displayName)
                            .tag(profile.id)
                    }
                }
                Toggle("Startup animation", isOn: $appearance.animationEnabled)
                Toggle("Reduce Motion preview", isOn: $appearance.forceReduceMotion)
                Button("Preview Startup Animation", action: previewStartup)
                if appearance.brandPack.usesFallback {
                    Text("Selected manufacturer logo is absent. SVC fallback branding is active.")
                        .font(.footnote)
                        .foregroundStyle(SVCTheme.secondaryText)
                }
            }
            Section("Telemetry") {
                Slider(value: $telemetryRate, in: 1...10, step: 1)
                Text("\(telemetryRate, specifier: "%.0f") Hz")
            }
            Section("Calibration") {
                Toggle("Stage mock calibration", isOn: $calibrationMode)
                Text("Values are staged only; no hardware is changed.")
                    .font(.footnote)
            }
        }
        .navigationTitle("Settings")
    }
}
