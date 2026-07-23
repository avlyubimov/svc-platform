import SwiftUI

struct RootView: View {
    @ObservedObject var viewModel: AppViewModel

    var body: some View {
        NavigationStack {
            List {
                Section("Connection") {
                    NavigationLink("Search and pair") {
                        PairingView(viewModel: viewModel)
                    }
                    LabeledContent("State", value: viewModel.device.connectionState.rawValue)
                }
                Section("SVC") {
                    NavigationLink("Dashboard") {
                        DashboardView(telemetry: viewModel.device.telemetry)
                    }
                    NavigationLink("Power channels") {
                        ChannelsView(channels: viewModel.device.telemetry.channels)
                    }
                    NavigationLink("Diagnostics") {
                        DiagnosticsView(telemetry: viewModel.device.telemetry)
                    }
                    NavigationLink("CAN telemetry") {
                        CANTelemetryView(telemetry: viewModel.device.telemetry)
                    }
                    NavigationLink("Event log") {
                        EventLogView(events: viewModel.device.events)
                    }
                    NavigationLink("Device information") {
                        DeviceInfoView(telemetry: viewModel.device.telemetry)
                    }
                    NavigationLink("Firmware update") {
                        FirmwareUpdateView(viewModel: viewModel)
                    }
                    NavigationLink("Settings and calibration") {
                        SettingsView()
                    }
                }
            }
            .navigationTitle("SVC Mobile")
        }
    }
}
