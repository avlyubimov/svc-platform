import SwiftUI

struct SettingsView: View {
    @State private var telemetryRate = 2.0
    @State private var calibrationMode = false

    var body: some View {
        Form {
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
