import SwiftUI

struct DashboardView: View {
    let telemetry: TelemetrySnapshot
    var isConnecting = false

    var body: some View {
        List {
            if isConnecting {
                Label("Connecting to SVC", systemImage: "antenna.radiowaves.left.and.right")
                    .font(.footnote)
                    .foregroundStyle(SVCTheme.secondaryText)
            }
            MeasurementRow(
                title: "Battery",
                value: telemetry.batteryVoltage.displayValue
            )
            MeasurementRow(
                title: "Total current",
                value: telemetry.totalCurrent.displayValue
            )
            MeasurementRow(
                title: "Speed",
                value: telemetry.vehicle.speed.displayValue
            )
            MeasurementRow(
                title: "Engine RPM",
                value: telemetry.vehicle.engineRpm.displayValue
            )
            MeasurementRow(
                title: "Lean",
                value: telemetry.leanAngle.displayValue
            )
        }
        .scrollContentBackground(.hidden)
        .background(SVCTheme.background)
        .navigationTitle("Dashboard")
    }
}

struct MeasurementRow: View {
    let title: String
    let value: String

    var body: some View {
        LabeledContent(title, value: value)
            .monospacedDigit()
    }
}

extension Measurement where Value == Double {
    var displayValue: String {
        guard isUsable, let value else { return "Unavailable" }
        return "\(value.formatted(.number.precision(.fractionLength(0...2)))) \(unit)"
    }
}

extension Measurement where Value == String {
    var displayValue: String {
        guard isUsable, let value else { return "Unavailable" }
        return "\(value) \(unit == "state" || unit == "fault" ? "" : unit)"
            .trimmingCharacters(in: .whitespaces)
    }
}
