import SwiftUI

struct PairingView: View {
    @ObservedObject var viewModel: AppViewModel

    var body: some View {
        List {
            Button("Search for SVC") {
                viewModel.discover()
            }
            ForEach(viewModel.discoveredDevices) { device in
                Button {
                    viewModel.connect(to: device)
                } label: {
                    LabeledContent(device.name, value: "\(device.signalStrength) dBm")
                }
            }
        }
        .navigationTitle("Pairing")
    }
}
