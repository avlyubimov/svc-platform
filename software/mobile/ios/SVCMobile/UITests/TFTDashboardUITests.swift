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
            app.descendants(matching: .any)["tftDashboard"]
                .waitForExistence(timeout: 5)
        )
    }

    func testCoreClusterIsVisibleWithoutOverlapOrSystemChrome() {
        let dashboard = app.descendants(matching: .any)["tftDashboard"]
        let tachometer = app.descendants(matching: .any)["tftTachometer"]
        let speed = app.descendants(matching: .any)["tftSpeed"]
        let gear = app.descendants(matching: .any)["tftGear"]
        let bottomStrip = app.descendants(matching: .any)["tftBottomStrip"]

        XCTAssertTrue(tachometer.exists)
        XCTAssertTrue(speed.exists)
        XCTAssertTrue(gear.exists)
        XCTAssertTrue(bottomStrip.exists)
        XCTAssertTrue(dashboard.frame.contains(tachometer.frame))
        XCTAssertFalse(speed.frame.intersects(gear.frame))
        XCTAssertLessThan(speed.frame.maxY, bottomStrip.frame.minY)
        XCTAssertLessThan(gear.frame.maxY, bottomStrip.frame.minY)
        XCTAssertEqual(app.statusBars.count, 0)
        XCTAssertEqual(app.navigationBars.count, 0)
        XCTAssertEqual(app.tabBars.count, 0)

        let attachment = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        attachment.name = "SVC-TFT-main-dashboard"
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    func testSportCoreScreenshotHasNoSystemChrome() {
        app.terminate()
        app.launchArguments = [
            "SVC_SKIP_STARTUP",
            "SVC_TFT_DEMO",
            "SVC_TFT_PAGE=1"
        ]
        app.launch()

        let root = app.otherElements["rideModeRoot"]
        XCTAssertTrue(root.waitForExistence(timeout: 5))
        XCTAssertEqual(root.value as? String, "SPORT / CORE")
        XCTAssertEqual(app.statusBars.count, 0)
        XCTAssertEqual(app.navigationBars.count, 0)
        XCTAssertEqual(app.tabBars.count, 0)

        let attachment = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        attachment.name = "SVC-TFT-sport-core"
        attachment.lifetime = .keepAlways
        add(attachment)
    }
}
