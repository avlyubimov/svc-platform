import SwiftUI

struct ChannelsView: View {
    let channels: [ChannelTelemetry]

    var body: some View {
        List(channels) { channel in
            VStack(alignment: .leading) {
                Text(channel.id).font(.headline)
                Text("State: \(channel.state.displayValue)")
                Text("Current: \(channel.current.displayValue)")
                Text("Fault: \(channel.fault.displayValue)")
            }
        }
        .navigationTitle("Channels")
    }
}
