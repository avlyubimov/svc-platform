import XCTest

final class RideModeUITests: XCTestCase {
    private var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["SVC_SKIP_STARTUP", "SVC_RESET_RIDE_PAGE"]
        app.launch()
        XCTAssertTrue(
            app.otherElements["rideModeRoot"].waitForExistence(timeout: 5)
        )
    }

    func testRideModeHasNoSystemOrApplicationNavigationChrome() {
        XCTAssertEqual(app.statusBars.count, 0)
        XCTAssertEqual(app.navigationBars.count, 0)
        XCTAssertEqual(app.tabBars.count, 0)
        XCTAssertFalse(app.buttons["Menu"].exists)
        XCTAssertFalse(app.buttons["Back"].exists)
        XCTAssertEqual(currentPage, "PURE RIDE")
    }

    func testHorizontalSwipesMoveBothDirectionsAndDoNotCycle() {
        rideRoot.swipeLeft()
        XCTAssertTrue(waitForPage("SPORT / CORE"))
        rideRoot.swipeRight()
        XCTAssertTrue(waitForPage("PURE RIDE"))
        rideRoot.swipeRight()
        XCTAssertTrue(waitForPage("PURE RIDE"))
    }

    func testVerticalMovementDoesNotChangePage() {
        let start = rideRoot.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.82))
        let end = rideRoot.coordinate(withNormalizedOffset: CGVector(dx: 0.51, dy: 0.18))
        start.press(forDuration: 0.05, thenDragTo: end)
        XCTAssertTrue(waitForPage("PURE RIDE"))
    }

    func testCurrentPageSurvivesBackgroundForeground() {
        rideRoot.swipeLeft()
        XCTAssertTrue(waitForPage("SPORT / CORE"))
        XCUIDevice.shared.press(.home)
        app.activate()
        XCTAssertTrue(waitForPage("SPORT / CORE"))
        XCTAssertEqual(app.statusBars.count, 0)
    }

    func testNewLaunchRestoresLastRidePage() {
        rideRoot.swipeLeft()
        XCTAssertTrue(waitForPage("SPORT / CORE"))
        app.terminate()
        app.launchArguments = ["SVC_SKIP_STARTUP"]
        app.launch()
        XCTAssertTrue(waitForPage("SPORT / CORE"))
    }

    func testExitRestoresNormalSystemBehavior() {
        rideRoot.tap()
        let exit = app.buttons["exitRideMode"]
        XCTAssertTrue(exit.waitForExistence(timeout: 2))
        exit.tap()
        XCTAssertTrue(app.buttons["enterRideMode"].waitForExistence(timeout: 2))
        XCTAssertGreaterThan(app.statusBars.count, 0)
        XCTAssertGreaterThan(app.navigationBars.count, 0)
    }

    private var rideRoot: XCUIElement {
        app.otherElements["rideModeRoot"]
    }

    private var currentPage: String {
        rideRoot.value as? String ?? ""
    }

    private func waitForPage(_ page: String) -> Bool {
        let predicate = NSPredicate(format: "value == %@", page)
        let expectation = XCTNSPredicateExpectation(
            predicate: predicate,
            object: rideRoot
        )
        return XCTWaiter.wait(for: [expectation], timeout: 5) == .completed
    }
}
