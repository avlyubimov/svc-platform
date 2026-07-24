import SwiftUI

struct DiagnosticsView: View {
    let telemetry: TelemetrySnapshot

    var body: some View {
        List {
            Section("Warnings") {
                if telemetry.warnings.isEmpty {
                    Text("No active warnings")
                }
                ForEach(telemetry.warnings) { warning in
                    VStack(alignment: .leading) {
                        Text(warning.code).font(.headline)
                        Text(warning.message)
                        Text(warning.severity.capitalized)
                            .foregroundStyle(warning.severity == "critical" ? .red : .orange)
                    }
                }
            }
            Section("Thermal zones") {
                ForEach(telemetry.powerZoneTemperatures, id: \.id) { zone in
                    LabeledContent(
                        zone.id,
                        value: zone.valid && !zone.stale
                            ? "\((zone.value ?? 0).formatted(.number.precision(.fractionLength(1)))) \(zone.unit)"
                            : "Unavailable"
                    )
                }
            }
        }
        .navigationTitle("Diagnostics")
    }
}
