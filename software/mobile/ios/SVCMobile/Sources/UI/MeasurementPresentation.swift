import SwiftUI

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
