import SwiftUI

struct EventLogView: View {
    let events: [String]

    var body: some View {
        List(events, id: \.self) { event in
            Text(event)
        }
        .navigationTitle("Event Log")
    }
}
