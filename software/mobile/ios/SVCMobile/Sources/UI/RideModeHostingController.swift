import SwiftUI
import UIKit

struct RideModePresenter<Content: View>: UIViewControllerRepresentable {
    @Binding var isPresented: Bool
    @ViewBuilder let content: () -> Content

    func makeUIViewController(context: Context) -> RideModePresentationController {
        RideModePresentationController()
    }

    func updateUIViewController(
        _ controller: RideModePresentationController,
        context: Context
    ) {
        controller.update(
            isPresented: isPresented,
            content: AnyView(content())
        )
    }

    static func dismantleUIViewController(
        _ controller: RideModePresentationController,
        coordinator: Void
    ) {
        controller.dismissRideMode()
    }
}

@MainActor
final class RideModePresentationController: UIViewController {
    private var requestedPresentation = false
    private var pendingContent = AnyView(EmptyView())
    private var rideController: RideModeHostingController?

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .clear
        view.isUserInteractionEnabled = false
    }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        reconcilePresentation()
    }

    func update(isPresented: Bool, content: AnyView) {
        requestedPresentation = isPresented
        pendingContent = content
        if let rideController {
            rideController.rootView = content
        }
        reconcilePresentation()
    }

    func dismissRideMode() {
        requestedPresentation = false
        reconcilePresentation()
    }

    private func reconcilePresentation() {
        guard viewIfLoaded?.window != nil else { return }
        if requestedPresentation {
            guard rideController == nil else { return }
            let controller = RideModeHostingController(rootView: pendingContent)
            controller.modalPresentationStyle = .fullScreen
            controller.isModalInPresentation = true
            rideController = controller
            present(controller, animated: false)
        } else if let rideController {
            rideController.dismiss(animated: false)
            self.rideController = nil
        }
    }
}

@MainActor
final class RideModeHostingController: UIHostingController<AnyView> {
    private var originalIdleTimerDisabled = false
    private var originalBrightness: CGFloat = 0
    private var didApplyRideMode = false

    override var prefersStatusBarHidden: Bool { true }
    override var prefersHomeIndicatorAutoHidden: Bool { true }
    override var supportedInterfaceOrientations: UIInterfaceOrientationMask {
        [.landscapeLeft, .landscapeRight]
    }
    override var preferredInterfaceOrientationForPresentation: UIInterfaceOrientation {
        .landscapeRight
    }
    override var shouldAutorotate: Bool { true }

    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        applyRideModeIfNeeded()
        setNeedsStatusBarAppearanceUpdate()
        setNeedsUpdateOfHomeIndicatorAutoHidden()
        setNeedsUpdateOfSupportedInterfaceOrientations()
        request(interfaceOrientations: .landscape)
    }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        setNeedsStatusBarAppearanceUpdate()
        setNeedsUpdateOfHomeIndicatorAutoHidden()
        request(interfaceOrientations: .landscape)
    }

    override func viewWillDisappear(_ animated: Bool) {
        restoreSystemBehavior()
        super.viewWillDisappear(animated)
    }

    deinit {
        MainActor.assumeIsolated {
            restoreSystemBehavior()
        }
    }

    private func applyRideModeIfNeeded() {
        guard !didApplyRideMode else { return }
        didApplyRideMode = true
        originalIdleTimerDisabled = UIApplication.shared.isIdleTimerDisabled
        originalBrightness = UIScreen.main.brightness
        UIApplication.shared.isIdleTimerDisabled = true
    }

    private func restoreSystemBehavior() {
        guard didApplyRideMode else { return }
        didApplyRideMode = false
        UIApplication.shared.isIdleTimerDisabled = originalIdleTimerDisabled
        UIScreen.main.brightness = originalBrightness
        request(interfaceOrientations: .allButUpsideDown)
    }

    private func request(interfaceOrientations: UIInterfaceOrientationMask) {
        guard let windowScene = view.window?.windowScene else { return }
        windowScene.requestGeometryUpdate(
            UIWindowScene.GeometryPreferences.iOS(
                interfaceOrientations: interfaceOrientations
            )
        )
    }
}
