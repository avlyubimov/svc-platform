import SwiftUI

struct DeviceInfoView: View {
    let telemetry: TelemetrySnapshot

    var body: some View {
        List {
            LabeledContent("Device", value: telemetry.deviceId)
            MeasurementRow(title: "STM32", value: telemetry.versions.stm32.displayValue)
            MeasurementRow(title: "E73", value: telemetry.versions.e73.displayValue)
            MeasurementRow(title: "Protocol", value: telemetry.versions.protocolVersion.displayValue)
            MeasurementRow(title: "SD card", value: telemetry.storage.sdCardState.displayValue)
            MeasurementRow(title: "CAN logger", value: telemetry.storage.canLoggerState.displayValue)
        }
        .navigationTitle("Device")
    }
}
