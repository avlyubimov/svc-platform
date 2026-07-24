import SwiftUI

struct SettingsView: View {
    @ObservedObject var appearance: AppearanceStore
    @ObservedObject var ridePreferences: RidePreferences
    let telemetry: TelemetrySnapshot
    let previewStartup: () -> Void
    @State private var telemetryRate = 2.0

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
            Section("Ride Dashboard") {
                Picker(
                    "Performance profile",
                    selection: $ridePreferences.vehicleProfileId
                ) {
                    ForEach(ridePreferences.availableProfiles) { profile in
                        Text(profile.displayName)
                            .tag(profile.id)
                    }
                }
                Text("Technical limits are independent of startup branding.")
                    .font(.footnote)
                    .foregroundStyle(SVCTheme.secondaryText)

                Picker("Theme", selection: $ridePreferences.themeMode) {
                    ForEach(RideThemeMode.allCases) { mode in
                        Text(mode.title).tag(mode)
                    }
                }
                Toggle(
                    "Ride page indicator",
                    isOn: $ridePreferences.pageIndicatorEnabled
                )
                if ridePreferences.themeMode == .automatic {
                    VStack(alignment: .leading) {
                        Text(
                            "Enter night below \(ridePreferences.nightEnterLux, specifier: "%.0f") lux"
                        )
                        Slider(
                            value: $ridePreferences.nightEnterLux,
                            in: 50...600,
                            step: 25
                        )
                        Text(
                            "Enter day above \(ridePreferences.dayEnterLux, specifier: "%.0f") lux"
                        )
                        Slider(
                            value: $ridePreferences.dayEnterLux,
                            in: 200...1_500,
                            step: 25
                        )
                    }
                }
            }
            Section("Telemetry") {
                Slider(value: $telemetryRate, in: 1...10, step: 1)
                Text("\(telemetryRate, specifier: "%.0f") Hz")
            }
            Section("Motorcycle level") {
                Button("Calibrate motorcycle level") {}
                    .disabled(true)
                Text(calibrationExplanation)
                    .font(.footnote)
            }
        }
        .navigationTitle("Settings")
    }

    private var calibrationExplanation: String {
        let speed = telemetry.vehicle.speed.rideValue
        if speed.displayValue != 0 {
            return "Calibration requires confirmed speed 0 km/h."
        }
        return "Available only in Dashboard Demo Mode until a real BLE command is defined."
    }
}
