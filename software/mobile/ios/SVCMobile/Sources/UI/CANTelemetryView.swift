import SwiftUI

struct CANTelemetryView: View {
    let telemetry: TelemetrySnapshot

    var body: some View {
        List {
            MeasurementRow(title: "CAN1", value: telemetry.can1.state.displayValue)
            MeasurementRow(title: "Speed", value: telemetry.vehicle.speed.displayValue)
            MeasurementRow(title: "RPM", value: telemetry.vehicle.engineRpm.displayValue)
            MeasurementRow(
                title: "Engine temperature",
                value: telemetry.vehicle.engineTemperature.displayValue
            )
            MeasurementRow(
                title: "Instant fuel",
                value: telemetry.vehicle.instantFuelConsumption.displayValue
            )
            MeasurementRow(
                title: "Average fuel",
                value: telemetry.vehicle.averageFuelConsumption.displayValue
            )
            MeasurementRow(
                title: "Fuel level",
                value: telemetry.vehicle.fuelLevel.displayValue
            )
        }
        .navigationTitle("CAN Telemetry")
    }
}
