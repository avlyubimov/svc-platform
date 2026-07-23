import SwiftUI

struct DashboardView: View {
    let telemetry: TelemetrySnapshot

    var body: some View {
        List {
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
        .navigationTitle("Dashboard")
    }
}

struct MeasurementRow: View {
    let title: String
    let value: String

    var body: some View {
        LabeledContent(title, value: value)
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
