#if SVC_CARPLAY_EXPERIMENT
import CarPlay
import UIKit

final class CarPlaySceneDelegate: UIResponder, CPTemplateApplicationSceneDelegate {
    func templateApplicationScene(
        _ templateApplicationScene: CPTemplateApplicationScene,
        didConnect interfaceController: CPInterfaceController
    ) {
        let items = [
            CPListItem(text: "Speed", detailText: "—"),
            CPListItem(text: "Gear", detailText: "—"),
            CPListItem(text: "Battery", detailText: "—"),
            CPListItem(text: "SVC current", detailText: "—"),
            CPListItem(text: "Main warning", detailText: "Connection required"),
            CPListItem(text: "Connection", detailText: "Unavailable")
        ]
        items.forEach { $0.isEnabled = false }
        let template = CPListTemplate(
            title: "SVC Ride",
            sections: [CPListSection(items: items)]
        )
        interfaceController.setRootTemplate(template, animated: false)
    }
}
#endif
