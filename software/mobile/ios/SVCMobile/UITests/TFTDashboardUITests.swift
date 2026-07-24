import XCTest

final class TFTDashboardUITests: XCTestCase {
    private var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = [
            "SVC_SKIP_STARTUP",
            "SVC_TFT_DEMO",
            "SVC_TFT_PAGE=0"
        ]
        app.launch()
        XCTAssertTrue(
            app.otherElements["rideModeRoot"]
                .waitForExistence(timeout: 5)
        )
    }

    func testDashboardFillsLandscapeWithoutSystemChrome() {
        let dashboard = app.otherElements["rideModeRoot"]

        XCTAssertEqual(dashboard.value as? String, "PURE RIDE")
        XCTAssertGreaterThan(dashboard.frame.width, dashboard.frame.height)
        XCTAssertEqual(app.statusBars.count, 0)
        XCTAssertEqual(app.navigationBars.count, 0)
        XCTAssertEqual(app.tabBars.count, 0)

        let attachment = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        attachment.name = "SVC-TFT-main-dashboard"
        attachment.lifetime = .keepAlways
        add(attachment)
    }
}
