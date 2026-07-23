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
                    Text("BMW R1200GS K25 · 2007")
                        .tag("bmw-r1200gs-k25-personal")
                    Text("Generic Automotive")
                        .tag("generic-automotive")
                }
                Toggle("Startup animation", isOn: $appearance.animationEnabled)
                Toggle("Reduce Motion preview", isOn: $appearance.forceReduceMotion)
                Button("Preview Startup Animation", action: previewStartup)
                if appearance.brandPack.id == "generic-automotive",
                   appearance.profileId == "bmw-r1200gs-k25-personal" {
                    Text("BMW assets are absent. SVC fallback branding is active.")
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
