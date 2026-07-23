import SwiftUI

struct FirmwareUpdateView: View {
    @ObservedObject var viewModel: AppViewModel
    @State private var showingConfirmation = false

    private var denials: [String] {
        OTAPolicy.denialReasons(for: viewModel.device.telemetry)
    }

    var body: some View {
        List {
            Section("Release") {
                Text(viewModel.firmwareStatus)
                Button("Check GitHub release") {
                    viewModel.checkFirmware()
                }
            }
            Section("Admission") {
                if denials.isEmpty {
                    Text("Device mock reports parked and eligible")
                } else {
                    ForEach(denials, id: \.self) { reason in
                        Text(reason).foregroundStyle(.red)
                    }
                }
            }
            Section {
                Button("Install with confirmation") {
                    showingConfirmation = true
                }
                .disabled(!denials.isEmpty)
            } footer: {
                Text("No automatic update. Installation is available only on the phone.")
            }
        }
        .navigationTitle("Firmware")
        .alert("Confirm firmware installation", isPresented: $showingConfirmation) {
            Button("Cancel", role: .cancel) {}
            Button("Install", role: .destructive) {
                viewModel.installFirmware()
            }
        } message: {
            Text("The mock scaffold performs no real device action.")
        }
    }
}
