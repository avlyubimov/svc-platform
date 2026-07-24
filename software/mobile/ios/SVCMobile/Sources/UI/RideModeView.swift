import Foundation
import SwiftUI
import UIKit

enum RideModePage: Int, CaseIterable, Identifiable {
    case mainDashboard
    case leanImu
    case vehicleRdc
    case svcPower
    case canDiagnostics

    var id: Int { rawValue }

    var title: String {
        switch self {
        case .mainDashboard: "PURE RIDE"
        case .leanImu: "SPORT / CORE"
        case .vehicleRdc: "VEHICLE"
        case .svcPower: "SVC POWER"
        case .canDiagnostics: "DIAGNOSTICS"
        }
    }

    var accessibilityID: String {
        switch self {
        case .mainDashboard: "MAIN_DASHBOARD"
        case .leanImu: "LEAN_IMU"
        case .vehicleRdc: "VEHICLE_RDC"
        case .svcPower: "SVC_POWER"
        case .canDiagnostics: "CAN_DIAGNOSTICS"
        }
    }
}

enum RideSwipePolicy {
    static let transitionDuration = 0.25
    static let edgeWidth: CGFloat = 24
    static let pageThreshold: CGFloat = 72
    static let horizontalDominance = 1.2
    static let boundaryResistance = 0.18

    static func targetPage(
        currentPage: Int,
        pageCount: Int,
        translation: CGSize,
        predictedTranslation: CGSize
    ) -> Int {
        let horizontal = abs(translation.width)
        let vertical = abs(translation.height)
        guard horizontal > vertical * horizontalDominance else {
            return currentPage
        }
        let projectedWidth = abs(predictedTranslation.width)
        guard max(horizontal, projectedWidth) >= pageThreshold else {
            return currentPage
        }
        if translation.width < 0 {
            return min(currentPage + 1, pageCount - 1)
        }
        return max(currentPage - 1, 0)
    }

    static func startsOutsideSystemEdges(
        x: CGFloat,
        width: CGFloat
    ) -> Bool {
        x >= edgeWidth && x <= width - edgeWidth
    }
}

struct RideModeView: View {
    let telemetry: TelemetrySnapshot
    let connectionState: ConnectionState
    let isConnecting: Bool
    let profile: VehiclePerformanceProfile
    @ObservedObject var ridePreferences: RidePreferences
    let reduceMotion: Bool
    let demoMode: Bool
    let exitRideMode: () -> Void
    let openSettings: () -> Void

    @State private var currentPage = RideModePage.mainDashboard.rawValue
    @State private var dragOffset: CGFloat = 0
    @State private var resolvedTheme = RideResolvedTheme.night
    @State private var controlsVisible = ProcessInfo.processInfo.arguments.contains(
        "SVC_UI_TEST_KEEP_CONTROLS"
    )
    @State private var indicatorVisible = true
    @State private var brightness = Double(UIScreen.main.brightness)
    @State private var controlsTask: Task<Void, Never>?
    @State private var indicatorTask: Task<Void, Never>?

    private var dashboard: RideDashboardState {
        RideDashboardState.build(
            telemetry: telemetry,
            connectionState: connectionState,
            isConnecting: isConnecting,
            profile: profile
        )
    }

    private var data: TFTDashboardData {
        TFTDashboardData.resolve(
            dashboard: dashboard,
            telemetry: telemetry,
            demoMode: demoMode
        )
    }

    private var palette: RidePalette {
        RidePalette.resolve(resolvedTheme)
    }

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                palette.background
                    .ignoresSafeArea()

                pager(
                    size: CGSize(
                        width: geometry.size.width
                            - geometry.safeAreaInsets.leading
                            - geometry.safeAreaInsets.trailing,
                        height: geometry.size.height
                    )
                )
                .padding(.leading, geometry.safeAreaInsets.leading)
                .padding(.trailing, geometry.safeAreaInsets.trailing)

                if ridePreferences.pageIndicatorEnabled {
                    RidePageIndicator(
                        selectedPage: currentPage,
                        palette: palette
                    )
                    .opacity(indicatorVisible ? 1 : 0)
                    .animation(.easeOut(duration: 0.32), value: indicatorVisible)
                    .frame(maxHeight: .infinity, alignment: .bottom)
                    .padding(.bottom, 6)
                    .accessibilityIdentifier("ridePageIndicator")
                }

                if controlsVisible {
                    RideControlsOverlay(
                        brightness: $brightness,
                        themeMode: $ridePreferences.themeMode,
                        stationaryControlsEnabled: dashboard.speed.displayValue == 0,
                        palette: palette,
                        exitRideMode: exitRideMode,
                        openSettings: openSettings,
                        interaction: controlsInteraction
                    )
                    .transition(.opacity)
                    .frame(maxHeight: .infinity, alignment: .top)
                    .padding(.top, 10)
                    .accessibilityIdentifier("rideControlsOverlay")
                }
            }
            .contentShape(Rectangle())
            .simultaneousGesture(
                TapGesture().onEnded { _ in showControls() }
            )
        }
        .ignoresSafeArea(.container, edges: [.top, .bottom])
        .statusBarHidden(true)
        .persistentSystemOverlays(.hidden)
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("rideModeRoot")
        .accessibilityValue(RideModePage(rawValue: currentPage)?.title ?? "")
        .onAppear {
            if demoMode {
                currentPage = presentationPage
            } else if ProcessInfo.processInfo.arguments.contains(
                "SVC_RESET_RIDE_PAGE"
            ) {
                currentPage = 0
                ridePreferences.lastRidePage = 0
            } else {
                currentPage = ridePreferences.lastRidePage
            }
            updateTheme()
            showIndicator()
        }
        .onChange(of: telemetry) { _, _ in updateTheme() }
        .onChange(of: ridePreferences.themeMode) { _, _ in updateTheme() }
        .onDisappear {
            controlsTask?.cancel()
            indicatorTask?.cancel()
        }
    }

    private func pager(size: CGSize) -> some View {
        HStack(spacing: 0) {
            ForEach(RideModePage.allCases) { page in
                pageView(page)
                    .frame(width: size.width, height: size.height)
                    .accessibilityIdentifier("ridePage_\(page.accessibilityID)")
            }
        }
        .frame(width: size.width, height: size.height, alignment: .leading)
        .offset(x: -CGFloat(currentPage) * size.width + dragOffset)
        .contentShape(Rectangle())
        .clipped()
        .gesture(
            DragGesture(minimumDistance: 12, coordinateSpace: .local)
                .onChanged { value in
                    updateDrag(value, pageWidth: size.width)
                }
                .onEnded(finishDrag)
        )
    }

    @ViewBuilder
    private func pageView(_ page: RideModePage) -> some View {
        switch page {
        case .mainDashboard:
            DashboardView(
                telemetry: telemetry,
                connectionState: connectionState,
                isConnecting: isConnecting,
                profile: profile,
                themeMode: ridePreferences.themeMode,
                themeThresholds: ridePreferences.themeThresholds,
                demoMode: demoMode
            )
        case .leanImu:
            LeanIMUPage(
                data: data,
                telemetry: telemetry,
                palette: palette
            )
        case .vehicleRdc:
            VehicleRDCPage(
                data: data,
                telemetry: telemetry,
                palette: palette
            )
        case .svcPower:
            SVCPowerPage(
                data: data,
                telemetry: telemetry,
                palette: palette
            )
        case .canDiagnostics:
            CANDiagnosticsPage(
                data: data,
                telemetry: telemetry,
                palette: palette
            )
        }
    }

    private func updateDrag(
        _ value: DragGesture.Value,
        pageWidth: CGFloat
    ) {
        guard RideSwipePolicy.startsOutsideSystemEdges(
            x: value.startLocation.x,
            width: pageWidth
        ) else {
            dragOffset = 0
            return
        }
        let horizontal = abs(value.translation.width)
        let vertical = abs(value.translation.height)
        guard horizontal > vertical * RideSwipePolicy.horizontalDominance else {
            dragOffset = 0
            return
        }
        let atFirst = currentPage == 0 && value.translation.width > 0
        let atLast = currentPage == RideModePage.allCases.count - 1
            && value.translation.width < 0
        dragOffset = value.translation.width
            * (atFirst || atLast ? RideSwipePolicy.boundaryResistance : 1)
        showIndicator()
    }

    private func finishDrag(_ value: DragGesture.Value) {
        let target = RideSwipePolicy.targetPage(
            currentPage: currentPage,
            pageCount: RideModePage.allCases.count,
            translation: value.translation,
            predictedTranslation: value.predictedEndTranslation
        )
        withAnimation(
            .easeOut(
                duration: reduceMotion ? 0 : RideSwipePolicy.transitionDuration
            )
        ) {
            currentPage = target
            if !demoMode {
                ridePreferences.lastRidePage = target
            }
            dragOffset = 0
        }
        showIndicator()
    }

    private func updateTheme() {
        resolvedTheme = RideThemeResolver.resolve(
            mode: ridePreferences.themeMode,
            ambientLight: dashboard.ambientLight,
            previous: resolvedTheme,
            thresholds: ridePreferences.themeThresholds
        )
    }

    private func showControls() {
        controlsTask?.cancel()
        withAnimation(.easeOut(duration: 0.12)) {
            controlsVisible = true
        }
        let autoHideDelay: Duration = ProcessInfo.processInfo.arguments.contains(
            "SVC_UI_TEST_KEEP_CONTROLS"
        ) ? .seconds(30) : .seconds(3)
        controlsTask = Task {
            try? await Task.sleep(for: autoHideDelay)
            guard !Task.isCancelled else { return }
            withAnimation(.easeOut(duration: 0.18)) {
                controlsVisible = false
            }
        }
    }

    private func controlsInteraction() {
        UIScreen.main.brightness = CGFloat(brightness)
        showControls()
    }

    private func showIndicator() {
        guard ridePreferences.pageIndicatorEnabled else {
            indicatorVisible = false
            return
        }
        indicatorTask?.cancel()
        indicatorVisible = true
        indicatorTask = Task {
            try? await Task.sleep(for: .seconds(3))
            guard !Task.isCancelled else { return }
            indicatorVisible = false
        }
    }

    private var presentationPage: Int {
        let prefix = "SVC_TFT_PAGE="
        let requested = ProcessInfo.processInfo.arguments
            .first(where: { $0.hasPrefix(prefix) })
            .flatMap { Int($0.dropFirst(prefix.count)) }
            ?? 0
        return min(max(requested, 0), RideModePage.allCases.count - 1)
    }
}

private struct RidePageIndicator: View {
    let selectedPage: Int
    let palette: RidePalette

    var body: some View {
        HStack(spacing: 7) {
            ForEach(RideModePage.allCases) { page in
                Circle()
                    .fill(
                        page.rawValue == selectedPage
                            ? palette.primaryText
                            : palette.secondaryText.opacity(0.42)
                    )
                    .frame(
                        width: page.rawValue == selectedPage ? 6 : 4,
                        height: page.rawValue == selectedPage ? 6 : 4
                    )
            }
        }
        .opacity(0.76)
    }
}

private struct LeanIMUPage: View {
    let data: TFTDashboardData
    let telemetry: TelemetrySnapshot
    let palette: RidePalette

    @State private var extrema = LeanExtrema()

    var body: some View {
        GeometryReader { geometry in
            let compact = geometry.size.height < 390
            ZStack {
                palette.background
                TFTPageHeader("SPORT / CORE", data: data, palette: palette)
                    .frame(maxHeight: .infinity, alignment: .top)
                Rectangle()
                    .fill(palette.accent)
                    .frame(width: compact ? 72 : 96, height: 3)
                    .frame(
                        maxWidth: .infinity,
                        maxHeight: .infinity,
                        alignment: .topLeading
                    )
                    .padding(.top, 28)

                HStack(spacing: compact ? 28 : 46) {
                    TFTSportMetric(
                        "SPEED",
                        "\(data.speedKmh.map { String(Int($0.rounded())) } ?? "—") km/h",
                        palette: palette,
                        compact: compact
                    )
                    TFTSportMetric(
                        "RPM",
                        data.engineRpm.map { String(Int($0.rounded())) } ?? "—",
                        palette: palette,
                        compact: compact
                    )
                    TFTSportMetric(
                        "GEAR",
                        data.gear.isEmpty ? "—" : data.gear,
                        palette: palette,
                        compact: compact,
                        valueColor: data.gear == "N"
                            ? palette.valid
                            : palette.primaryText
                    )
                }
                .frame(maxHeight: .infinity, alignment: .top)
                .padding(.top, compact ? 30 : 34)

                LeanHorizon(leanDegrees: data.leanDegrees, palette: palette)
                    .frame(
                        width: geometry.size.width * 0.68,
                        height: geometry.size.height * 0.58
                    )
                    .padding(.top, compact ? 36 : 46)

                VStack(spacing: 3) {
                    Text(data.leanDegrees.signedTFT("°", decimals: 1))
                        .font(
                            .system(
                                size: compact ? 72 : 96,
                                weight: .light,
                                design: .monospaced
                            )
                        )
                        .foregroundStyle(palette.primaryText)
                    HStack(spacing: 3) {
                        Text((data.leanDegrees ?? 0) < 0 ? "LEFT LEAN" : "RIGHT LEAN")
                            .font(.system(size: 10))
                            .tracking(2)
                            .foregroundStyle(palette.secondaryText)
                        if data.leanDegraded {
                            Text("▲")
                                .font(.system(size: 9))
                                .foregroundStyle(palette.degraded)
                        }
                    }
                }
                .padding(.top, compact ? 48 : 58)

                HStack(alignment: .bottom) {
                    TFTSideMetric(
                        "MAX LEFT",
                        "\(extrema.maximumLeftDegrees.tftNumber(1))°",
                        palette: palette
                    )
                    Spacer()
                    TFTSideMetric(
                        "MAX RIGHT",
                        "\(extrema.maximumRightDegrees.tftNumber(1))°",
                        palette: palette
                    )
                    Spacer()
                    TFTSideMetric(
                        "ACCELERATION",
                        data.accelerationG.tftValue("g", decimals: 2),
                        palette: palette
                    )
                    Spacer()
                    TFTSideMetric(
                        "BRAKING",
                        data.brakingG.tftValue("g", decimals: 2),
                        palette: palette,
                        alignment: .trailing
                    )
                }
                .frame(
                    maxWidth: .infinity,
                    maxHeight: .infinity,
                    alignment: .bottom
                )
                .padding(.horizontal, 18)
                .padding(.bottom, 16)
            }
        }
        .padding(.horizontal, 22)
        .padding(.vertical, 12)
        .background(palette.background)
        .onAppear { extrema.observe(data.leanDegrees) }
        .onChange(of: data.leanDegrees) { _, value in extrema.observe(value) }
    }
}

private struct LeanHorizon: View {
    let leanDegrees: Double?
    let palette: RidePalette

    var body: some View {
        Canvas { context, size in
            let lean = min(max(leanDegrees ?? 0, -60), 60)
            let radians = lean * .pi / 180
            let center = CGPoint(x: size.width / 2, y: size.height * 0.58)
            let radius = min(size.width, size.height) * 0.43
            var arc = Path()
            arc.addArc(
                center: center,
                radius: radius,
                startAngle: .degrees(205),
                endAngle: .degrees(335),
                clockwise: false
            )
            context.stroke(
                arc,
                with: .color(palette.divider),
                style: StrokeStyle(lineWidth: 2, lineCap: .round)
            )
            for mark in stride(from: -60, through: 60, by: 10) {
                let angle = Double(270 + mark) * .pi / 180
                let outer = CGPoint(
                    x: center.x + cos(angle) * radius,
                    y: center.y + sin(angle) * radius
                )
                let inner = CGPoint(
                    x: center.x + cos(angle) * (radius - 12),
                    y: center.y + sin(angle) * (radius - 12)
                )
                var tick = Path()
                tick.move(to: inner)
                tick.addLine(to: outer)
                context.stroke(
                    tick,
                    with: .color(palette.secondaryText.opacity(0.72)),
                    lineWidth: 1.5
                )
            }
            let length = radius * 0.78
            var horizon = Path()
            horizon.move(
                to: CGPoint(
                    x: center.x - cos(radians) * length,
                    y: center.y - sin(radians) * length
                )
            )
            horizon.addLine(
                to: CGPoint(
                    x: center.x + cos(radians) * length,
                    y: center.y + sin(radians) * length
                )
            )
            context.stroke(
                horizon,
                with: .color(palette.accent),
                style: StrokeStyle(lineWidth: 5, lineCap: .round)
            )
            context.fill(
                Path(
                    ellipseIn: CGRect(
                        x: center.x - 4,
                        y: center.y - 4,
                        width: 8,
                        height: 8
                    )
                ),
                with: .color(palette.primaryText)
            )
        }
    }
}

private struct VehicleRDCPage: View {
    let data: TFTDashboardData
    let telemetry: TelemetrySnapshot
    let palette: RidePalette

    var body: some View {
        GeometryReader { geometry in
            let compact = geometry.size.height < 390
            VStack(spacing: 0) {
                TFTPageHeader("VEHICLE", data: data, palette: palette)
                HStack(spacing: 0) {
                    TFTLargeZone(
                        label: "FUEL",
                        value: data.fuelPercent.tftValue("%", decimals: 0),
                        detail: "RANGE \(data.rangeKm.tftValue("km", decimals: 0))  ·  AVG \(telemetry.vehicle.averageFuelConsumption.tftMeasurement(" L/100", decimals: 1))",
                        palette: palette,
                        compact: compact
                    )
                    Divider().overlay(palette.divider).padding(.vertical, 22)
                    TFTLargeZone(
                        label: "ENGINE / OIL",
                        value: data.engineTemperatureCelsius.tftValue(
                            "°C",
                            decimals: 0
                        ),
                        detail: "BAT \(data.batteryVoltage.tftValue("V", decimals: 1))  ·  AIR \(data.ambientTemperatureCelsius.signedTFT("°C", decimals: 0))",
                        palette: palette,
                        compact: compact
                    )
                    Divider().overlay(palette.divider).padding(.vertical, 22)
                    VStack(spacing: 12) {
                        Text("RDC")
                            .font(.system(size: 10))
                            .tracking(2)
                            .foregroundStyle(palette.secondaryText)
                        HStack(spacing: 32) {
                            TirePressure(
                                "FRONT",
                                pressure: data.frontPressureBar,
                                palette: palette,
                                compact: compact
                            )
                            TirePressure(
                                "REAR",
                                pressure: data.rearPressureBar,
                                palette: palette,
                                compact: compact
                            )
                        }
                        Text("DWA  —")
                        .font(
                            .system(
                                size: compact ? 11 : 13,
                                design: .monospaced
                            )
                        )
                        .foregroundStyle(palette.secondaryText)
                    }
                    .frame(maxWidth: .infinity)
                }
                .frame(maxHeight: .infinity)
            }
        }
        .padding(.horizontal, 22)
        .padding(.vertical, 12)
        .background(palette.background)
    }
}

private struct SVCPowerPage: View {
    let data: TFTDashboardData
    let telemetry: TelemetrySnapshot
    let palette: RidePalette

    private let columns = Array(
        repeating: GridItem(.flexible(), spacing: 12),
        count: 5
    )

    var body: some View {
        GeometryReader { geometry in
            let compact = geometry.size.height < 390
            VStack(spacing: 8) {
                TFTPageHeader("SVC POWER", data: data, palette: palette)
                HStack {
                    TFTInlineMetric(
                        "INPUT",
                        telemetry.batteryVoltage.tftMeasurement("V", decimals: 1),
                        palette: palette
                    )
                    TFTCompactOutputStates(palette: palette)
                    TFTInlineMetric(
                        "FAULTS",
                        String(
                            telemetry.channels.filter {
                                guard
                                    $0.fault.isUsable,
                                    let fault = $0.fault.value
                                else {
                                    return false
                                }
                                return fault.caseInsensitiveCompare("none")
                                    != .orderedSame
                            }.count
                        ),
                        palette: palette
                    )
                    TFTInlineMetric(
                        "TOTAL",
                        telemetry.totalCurrent.tftMeasurement("A", decimals: 1),
                        palette: palette
                    )
                    TFTInlineMetric(
                        "POWER TEMP",
                        telemetry.powerZoneTemperatures
                            .compactMap {
                                $0.valid && !$0.stale ? $0.value : nil
                            }
                            .max()
                            .tftValue("°C", decimals: 0),
                        palette: palette
                    )
                }
                .frame(height: compact ? 60 : 76)
                Divider().overlay(palette.divider)
                LazyVGrid(columns: columns, spacing: 5) {
                    ForEach(telemetry.channels) { channel in
                        TFTChannel(channel: channel, palette: palette)
                            .frame(minHeight: compact ? 78 : 96)
                    }
                }
                .frame(maxHeight: .infinity)
            }
        }
        .padding(.horizontal, 22)
        .padding(.vertical, 12)
        .background(palette.background)
    }
}

private struct CANDiagnosticsPage: View {
    let data: TFTDashboardData
    let telemetry: TelemetrySnapshot
    let palette: RidePalette

    var body: some View {
        VStack(spacing: 0) {
            TFTPageHeader("DIAGNOSTICS", data: data, palette: palette)
            HStack(spacing: 0) {
                VStack(alignment: .leading, spacing: 14) {
                    Text("CAN1  \(telemetry.can1.state.tftState)")
                        .font(
                            .system(
                                size: 22,
                                weight: .bold,
                                design: .monospaced
                            )
                        )
                        .foregroundStyle(palette.highBeam)
                    TFTDiagnosticRow(
                        "BLE",
                        data.bleConnected ? "CONNECTED" : "LOST",
                        palette: palette
                    )
                    TFTDiagnosticRow(
                        "CAN SAFETY",
                        "LISTEN-ONLY",
                        palette: palette
                    )
                    TFTDiagnosticRow(
                        "RX FRAMES",
                        telemetry.can1.rxFrames.tftMeasurement("", decimals: 0),
                        palette: palette
                    )
                    TFTDiagnosticRow(
                        "DROPPED",
                        telemetry.can1.droppedFrames.tftMeasurement("", decimals: 0),
                        palette: palette
                    )
                    TFTDiagnosticRow(
                        "LAST FRAME",
                        telemetry.can1.lastFrameTimestamp.tftState,
                        palette: palette
                    )
                    TFTDiagnosticRow(
                        "LOGGER",
                        telemetry.storage.canLoggerState.tftState,
                        palette: palette
                    )
                    TFTDiagnosticRow(
                        "SD",
                        telemetry.storage.sdCardState.tftState,
                        palette: palette
                    )
                    TFTDiagnosticRow(
                        "DATA QUALITY",
                        telemetry.tftQualitySummary,
                        palette: palette
                    )
                    Spacer()
                }
                .padding(.top, 22)
                .padding(.trailing, 22)
                .frame(maxWidth: .infinity)

                Divider().overlay(palette.divider).padding(.vertical, 22)

                VStack(alignment: .leading, spacing: 0) {
                    Text("WARNING JOURNAL")
                        .font(.system(size: 10))
                        .tracking(1.8)
                        .foregroundStyle(palette.secondaryText)
                        .padding(.bottom, 12)
                    if telemetry.warnings.isEmpty {
                        Text("NO RECORDED WARNINGS")
                            .font(.system(size: 13))
                            .foregroundStyle(palette.secondaryText)
                    } else {
                        ForEach(telemetry.warnings.prefix(6)) { warning in
                            HStack {
                                Text(warning.active ? "●" : "○")
                                    .font(.system(size: 10))
                                    .foregroundStyle(
                                        warning.active
                                            ? (
                                                warning.severity
                                                    .caseInsensitiveCompare("critical")
                                                    == .orderedSame
                                                    ? palette.critical
                                                    : palette.warning
                                            )
                                            : palette.secondaryText
                                    )
                                Text(warning.code.uppercased())
                                    .font(.system(size: 12, design: .monospaced))
                                    .foregroundStyle(palette.primaryText)
                                Spacer()
                                Text(warning.severity.uppercased())
                                    .font(.system(size: 9))
                                    .foregroundStyle(palette.secondaryText)
                            }
                            .padding(.vertical, 6)
                            Divider().overlay(palette.divider.opacity(0.58))
                        }
                    }
                    Spacer()
                }
                .padding(.leading, 22)
                .padding(.top, 22)
                .frame(maxWidth: .infinity)
            }
        }
        .padding(.horizontal, 22)
        .padding(.vertical, 12)
        .background(palette.background)
    }
}

private struct TFTPageHeader: View {
    let title: String
    let data: TFTDashboardData
    let palette: RidePalette

    init(_ title: String, data: TFTDashboardData, palette: RidePalette) {
        self.title = title
        self.data = data
        self.palette = palette
    }

    var body: some View {
        HStack {
            Text(title)
                .font(.system(size: 10, weight: .bold))
                .tracking(2)
                .foregroundStyle(palette.secondaryText)
            Spacer()
            if !data.bleConnected {
                connection("BLE", connected: false)
            }
            if !data.canConnected {
                connection("CAN", connected: false)
            }
        }
        .frame(height: 28)
    }

    private func connection(_ label: String, connected: Bool) -> some View {
        HStack(spacing: 4) {
            Circle()
                .fill(connected ? palette.valid : palette.critical)
                .frame(width: 5, height: 5)
            Text(label)
                .font(.system(size: 8))
                .foregroundStyle(palette.secondaryText)
        }
        .padding(.leading, 10)
    }
}

private struct TFTSideMetric: View {
    let label: String
    let value: String
    let palette: RidePalette
    let alignment: HorizontalAlignment

    init(
        _ label: String,
        _ value: String,
        palette: RidePalette,
        alignment: HorizontalAlignment = .leading
    ) {
        self.label = label
        self.value = value
        self.palette = palette
        self.alignment = alignment
    }

    var body: some View {
        VStack(alignment: alignment, spacing: 2) {
            Text(label)
                .font(.system(size: 9))
                .tracking(1)
                .foregroundStyle(palette.secondaryText)
            Text(value)
                .font(.system(size: 18, weight: .semibold, design: .monospaced))
                .foregroundStyle(palette.primaryText)
        }
    }
}

private struct TFTSportMetric: View {
    let label: String
    let value: String
    let palette: RidePalette
    let compact: Bool
    let valueColor: Color

    init(
        _ label: String,
        _ value: String,
        palette: RidePalette,
        compact: Bool,
        valueColor: Color? = nil
    ) {
        self.label = label
        self.value = value
        self.palette = palette
        self.compact = compact
        self.valueColor = valueColor ?? palette.primaryText
    }

    var body: some View {
        VStack(spacing: 2) {
            Text(label)
                .font(.system(size: compact ? 8 : 9))
                .tracking(1.4)
                .foregroundStyle(palette.secondaryText)
            Text(value)
                .font(
                    .system(
                        size: compact ? 17 : 21,
                        weight: .bold,
                        design: .monospaced
                    )
                )
                .foregroundStyle(valueColor)
        }
    }
}

private struct TFTLargeZone: View {
    let label: String
    let value: String
    let detail: String
    let palette: RidePalette
    let compact: Bool

    var body: some View {
        VStack(spacing: 6) {
            Text(label)
                .font(.system(size: 10))
                .tracking(2)
                .foregroundStyle(palette.secondaryText)
            Text(value)
                .font(
                    .system(
                        size: compact ? 42 : 58,
                        weight: .light,
                        design: .monospaced
                    )
                )
                .foregroundStyle(palette.primaryText)
            Text(detail)
                .font(
                    .system(
                        size: compact ? 11 : 14,
                        design: .monospaced
                    )
                )
                .foregroundStyle(palette.secondaryText)
        }
        .frame(maxWidth: .infinity)
    }
}

private struct TirePressure: View {
    let label: String
    let pressure: Double?
    let palette: RidePalette
    let compact: Bool

    init(
        _ label: String,
        pressure: Double?,
        palette: RidePalette,
        compact: Bool
    ) {
        self.label = label
        self.pressure = pressure
        self.palette = palette
        self.compact = compact
    }

    var body: some View {
        VStack(spacing: 3) {
            RoundedRectangle(cornerRadius: 8)
                .stroke(palette.divider, lineWidth: 2)
                .frame(width: compact ? 34 : 42, height: 54)
                .overlay {
                    VStack {
                        Rectangle()
                            .fill(palette.secondaryText)
                            .frame(width: compact ? 18 : 22, height: 1)
                        Spacer()
                        Rectangle()
                            .fill(palette.secondaryText)
                            .frame(width: compact ? 18 : 22, height: 1)
                    }
                    .padding(.vertical, 11)
                }
            Text(label)
                .font(.system(size: 8))
                .foregroundStyle(palette.secondaryText)
            Text(pressure.tftValue("bar", decimals: 1))
                .font(
                    .system(
                        size: compact ? 16 : 20,
                        weight: .bold,
                        design: .monospaced
                    )
                )
                .foregroundStyle(palette.primaryText)
        }
    }
}

private struct TFTInlineMetric: View {
    let label: String
    let value: String
    let palette: RidePalette

    init(_ label: String, _ value: String, palette: RidePalette) {
        self.label = label
        self.value = value
        self.palette = palette
    }

    var body: some View {
        VStack(spacing: 2) {
            Text(label)
                .font(.system(size: 9))
                .tracking(1.4)
                .foregroundStyle(palette.secondaryText)
            Text(value)
                .font(.system(size: 25, weight: .semibold, design: .monospaced))
                .foregroundStyle(palette.primaryText)
        }
        .frame(maxWidth: .infinity)
    }
}

private struct TFTCompactOutputStates: View {
    let palette: RidePalette

    var body: some View {
        VStack(spacing: 2) {
            Text("CONFIGURED OUTPUTS")
                .font(.system(size: 9))
                .tracking(1.2)
                .foregroundStyle(palette.secondaryText)
            Text("FOG --   CHARGE --   AUX --")
                .font(.system(size: 11, weight: .semibold, design: .monospaced))
                .foregroundStyle(palette.disabledText)
        }
        .frame(maxWidth: .infinity)
    }
}

private struct TFTChannel: View {
    let channel: ChannelTelemetry
    let palette: RidePalette

    private var current: Double? {
        channel.current.isUsable ? channel.current.value : nil
    }

    private var fraction: Double {
        min(max((current ?? 0) / 10, 0), 1)
    }

    private var faulted: Bool {
        guard
            channel.fault.isUsable,
            let fault = channel.fault.value
        else {
            return false
        }
        return fault.caseInsensitiveCompare("none") != .orderedSame
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            HStack {
                Text(channel.id)
                    .font(.system(size: 9, weight: .bold))
                    .foregroundStyle(palette.secondaryText)
                Spacer()
                Text(channel.state.tftState)
                    .font(.system(size: 8))
                    .foregroundStyle(faulted ? palette.critical : palette.valid)
            }
            Text(channel.current.tftMeasurement("A", decimals: 1))
                .font(.system(size: 18, weight: .semibold, design: .monospaced))
                .foregroundStyle(palette.primaryText)
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    Rectangle().fill(palette.divider.opacity(0.64))
                    Rectangle()
                        .fill(faulted ? palette.critical : palette.accentBright)
                        .frame(width: geometry.size.width * fraction)
                }
            }
            .frame(height: 3)
        }
        .padding(.horizontal, 3)
        .padding(.vertical, 4)
    }
}

private struct TFTDiagnosticRow: View {
    let label: String
    let value: String
    let palette: RidePalette

    init(_ label: String, _ value: String, palette: RidePalette) {
        self.label = label
        self.value = value
        self.palette = palette
    }

    var body: some View {
        HStack {
            Text(label)
                .font(.system(size: 10))
                .foregroundStyle(palette.secondaryText)
            Spacer()
            Text(value)
                .font(.system(size: 12, design: .monospaced))
                .foregroundStyle(palette.primaryText)
                .lineLimit(1)
        }
    }
}

private struct RideControlsOverlay: View {
    @Binding var brightness: Double
    @Binding var themeMode: RideThemeMode
    let stationaryControlsEnabled: Bool
    let palette: RidePalette
    let exitRideMode: () -> Void
    let openSettings: () -> Void
    let interaction: () -> Void

    var body: some View {
        HStack(spacing: 8) {
            Button("EXIT", action: exitRideMode)
                .disabled(!stationaryControlsEnabled)
                .accessibilityIdentifier("exitRideMode")
            Text("BRIGHTNESS")
                .font(.caption2)
                .foregroundStyle(palette.secondaryText)
            Slider(value: $brightness, in: 0.05...1)
                .frame(width: 180)
                .onChange(of: brightness) { _, _ in interaction() }
                .accessibilityIdentifier("rideBrightness")
            ForEach(RideThemeMode.allCases) { mode in
                Button(mode.overlayTitle) {
                    themeMode = mode
                    switch mode {
                    case .day:
                        brightness = max(brightness, 0.85)
                    case .night:
                        brightness = min(brightness, 0.35)
                    case .automatic:
                        break
                    }
                    interaction()
                }
                .foregroundStyle(
                    themeMode == mode ? palette.accentBright : palette.primaryText
                )
                .accessibilityIdentifier("rideTheme_\(mode.rawValue)")
            }
            Button("SETTINGS", action: openSettings)
                .disabled(!stationaryControlsEnabled)
                .accessibilityIdentifier("rideSettings")
        }
        .font(.caption.weight(.semibold))
        .buttonStyle(.borderless)
        .padding(.horizontal, 12)
        .padding(.vertical, 7)
        .background(
            palette.raisedSurface.opacity(0.96),
            in: RoundedRectangle(cornerRadius: 4)
        )
    }
}

private extension RideThemeMode {
    var overlayTitle: String {
        switch self {
        case .automatic: "AUTO"
        case .day: "DAY"
        case .night: "NIGHT"
        }
    }
}

private extension Measurement where Value == Double {
    func tftMeasurement(_ suffix: String, decimals: Int) -> String {
        guard isUsable, let value else { return "—" }
        return "\(String(format: "%.\(decimals)f", value))\(suffix)"
    }

    func shortNumber(_ decimals: Int) -> String {
        guard isUsable, let value else { return "—" }
        return String(format: "%.\(decimals)f", value)
    }
}

private extension TelemetrySnapshot {
    var tftQualitySummary: String {
        let measurements: [Measurement<Double>] = [
            batteryVoltage,
            totalCurrent,
            ambientLight,
            leanAngle,
            accelerometer.x,
            accelerometer.y,
            accelerometer.z,
            vehicle.speed,
            vehicle.engineRpm,
            vehicle.engineTemperature,
            vehicle.instantFuelConsumption,
            vehicle.averageFuelConsumption,
            vehicle.fuelLevel,
            vehicle.ambientTemperature
        ]
        return "\(measurements.filter(\.isUsable).count)/\(measurements.count) VALID"
    }
}

private extension Measurement where Value == String {
    var tftState: String {
        guard isUsable, let value else { return "—" }
        return value.uppercased()
    }
}

private extension Optional where Wrapped == Double {
    func tftValue(_ suffix: String, decimals: Int) -> String {
        guard let self else { return "—" }
        return "\(String(format: "%.\(decimals)f", self)) \(suffix)"
    }

    func signedTFT(_ suffix: String, decimals: Int) -> String {
        guard let self else { return "—" }
        return "\(String(format: "%+.\(decimals)f", self))\(suffix)"
    }
}

private extension Double {
    func tftNumber(_ decimals: Int) -> String {
        String(format: "%.\(decimals)f", self)
    }
}
