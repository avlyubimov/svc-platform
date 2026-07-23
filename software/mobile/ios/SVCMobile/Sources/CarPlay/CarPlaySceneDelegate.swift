#if SVC_CARPLAY_EXPERIMENT
import CarPlay
import UIKit

final class CarPlaySceneDelegate: UIResponder, CPTemplateApplicationSceneDelegate {
    func templateApplicationScene(
        _ templateApplicationScene: CPTemplateApplicationScene,
        didConnect interfaceController: CPInterfaceController
    ) {
        let items = [
            CPListItem(text: "Battery", detailText: "12.7 V"),
            CPListItem(text: "Total current", detailText: "8.4 A"),
            CPListItem(text: "Speed", detailText: "0 km/h"),
            CPListItem(text: "Engine RPM", detailText: "0 rpm"),
            CPListItem(text: "Engine temperature", detailText: "Unavailable"),
            CPListItem(text: "Fuel consumption", detailText: "Unavailable"),
            CPListItem(text: "Ambient temperature", detailText: "Unavailable"),
            CPListItem(text: "Ambient light", detailText: "820 lux"),
            CPListItem(text: "Lean angle", detailText: "0.8°"),
            CPListItem(text: "Warnings", detailText: "SD card missing"),
            CPListItem(text: "Channels", detailText: "3 on, 7 off")
        ]
        items.forEach { $0.isEnabled = false }
        let template = CPListTemplate(
            title: "SVC Status",
            sections: [CPListSection(items: items)]
        )
        interfaceController.setRootTemplate(template, animated: false)
    }
}
#endif
