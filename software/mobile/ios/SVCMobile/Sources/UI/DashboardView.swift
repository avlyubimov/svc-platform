import Foundation
import SwiftUI

struct DashboardView: View {
    let telemetry: TelemetrySnapshot
    let connectionState: ConnectionState
    let isConnecting: Bool
    let profile: VehiclePerformanceProfile
    let themeMode: RideThemeMode
    let themeThresholds: RideThemeThresholds
    var demoMode = false

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var resolvedTheme = RideResolvedTheme.night
    @State private var toastVisible = false

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
        let inherited = RidePalette.resolve(resolvedTheme)
        return RidePalette(
            background: Color(red: 3 / 255, green: 5 / 255, blue: 7 / 255),
            surface: inherited.surface,
            raisedSurface: inherited.raisedSurface,
            primaryText: Color(red: 244 / 255, green: 246 / 255, blue: 248 / 255),
            secondaryText: Color(red: 170 / 255, green: 178 / 255, blue: 188 / 255),
            disabledText: inherited.disabledText,
            divider: Color(red: 41 / 255, green: 49 / 255, blue: 58 / 255),
            accent: Color(red: 226 / 255, green: 27 / 255, blue: 45 / 255),
            accentBright: Color(red: 226 / 255, green: 27 / 255, blue: 45 / 255),
            warning: Color(red: 242 / 255, green: 169 / 255, blue: 0),
            critical: inherited.critical,
            valid: Color(red: 66 / 255, green: 215 / 255, blue: 125 / 255),
            degraded: Color(red: 242 / 255, green: 169 / 255, blue: 0),
            highBeam: Color(red: 68 / 255, green: 166 / 255, blue: 1),
            fogLight: Color(red: 244 / 255, green: 246 / 255, blue: 248 / 255)
        )
    }

    private var rpmFraction: Double {
        guard
            let maximum = data.tachometerMaximumRpm,
            maximum > 0
        else {
            return 0
        }
        return min(max((data.engineRpm ?? 0) / maximum, 0), 1)
    }

    var body: some View {
        GeometryReader { geometry in
            let compact = geometry.size.height < 390 || geometry.size.width < 760
            let edgePadding = geometry.size.width * 0.04

            ZStack {
                palette.background

                TFTRibbonTachometer(
                    data: data,
                    palette: palette,
                    fillFraction: rpmFraction
                )
                .frame(width: geometry.size.width, height: geometry.size.height)
                .animation(
                    .easeInOut(duration: reduceMotion ? 0 : 0.28),
                    value: rpmFraction
                )
                .accessibilityIdentifier("tftTachometer")

                TFTTopLine(data: data, palette: palette, compact: compact)
                    .frame(
                        width: geometry.size.width * 0.72,
                        height: geometry.size.height * 0.15,
                        alignment: .top
                    )
                    .position(
                        x: geometry.size.width * 0.5,
                        y: geometry.size.height * 0.075
                    )

                TFTSpeedCluster(data: data, palette: palette, compact: compact)
                    .frame(
                        width: geometry.size.width * 0.31,
                        height: geometry.size.height * 0.28,
                        alignment: .leading
                    )
                    .position(
                        x: geometry.size.width * 0.325,
                        y: geometry.size.height * 0.31
                    )
                    .accessibilityIdentifier("tftSpeed")

                TFTGear(
                    gear: data.gear,
                    palette: palette,
                    compact: compact
                )
                .frame(
                    width: geometry.size.width * 0.15,
                    height: geometry.size.height * 0.25
                )
                .position(
                    x: geometry.size.width * 0.815,
                    y: geometry.size.height * 0.665
                )
                .accessibilityIdentifier("tftGear")

                Text("\(data.engineRpm.wholeOrDash) rpm")
                    .font(.system(size: compact ? 11 : 13, design: .monospaced))
                    .tracking(1.2)
                    .foregroundStyle(palette.secondaryText)
                    .position(
                        x: geometry.size.width * 0.50,
                        y: geometry.size.height * 0.70
                    )
                    .accessibilityIdentifier("tftDigitalRpm")

                TFTSideIndicators(
                    side: .left,
                    data: data,
                    palette: palette,
                    compact: compact
                )
                .frame(
                    width: compact ? 30 : 36,
                    height: geometry.size.height * 0.49
                )
                .position(
                    x: edgePadding + (compact ? 15 : 18),
                    y: geometry.size.height * 0.445
                )

                TFTSideIndicators(
                    side: .right,
                    data: data,
                    palette: palette,
                    compact: compact
                )
                .frame(
                    width: compact ? 30 : 36,
                    height: geometry.size.height * 0.49
                )
                .position(
                    x: geometry.size.width - edgePadding - (compact ? 15 : 18),
                    y: geometry.size.height * 0.445
                )

                TFTConnectionStatus(
                    data: data,
                    palette: palette,
                    compact: compact
                )
                .frame(width: geometry.size.width * 0.24)
                .position(
                    x: geometry.size.width * 0.55,
                    y: geometry.size.height * 0.78
                )
                .accessibilityIdentifier("tftConnectionIcons")

                if let criticalMessage = data.criticalMessage {
                    Text(criticalMessage.uppercased())
                        .font(.system(size: compact ? 10 : 12, weight: .bold))
                        .tracking(1.2)
                        .foregroundStyle(palette.primaryText)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 5)
                        .background(palette.critical.opacity(0.9))
                        .frame(maxHeight: .infinity, alignment: .bottom)
                        .padding(.bottom, geometry.size.height * 0.14)
                        .accessibilityIdentifier("tftCriticalStrip")
                }

                if toastVisible, let toastMessage = data.toastMessage {
                    Text("●  \(toastMessage)")
                        .font(.system(size: compact ? 10 : 12))
                        .foregroundStyle(palette.secondaryText)
                        .lineLimit(1)
                        .padding(.horizontal, 14)
                        .padding(.vertical, 7)
                        .background(
                            Color.black.opacity(0.86),
                            in: Capsule()
                        )
                        .frame(maxHeight: .infinity, alignment: .bottom)
                        .padding(.bottom, geometry.size.height * 0.15)
                        .transition(.opacity)
                        .accessibilityIdentifier("tftToast")
                }

                TFTBottomTelemetry(
                    data: data,
                    palette: palette,
                    compact: compact
                )
                .frame(
                    width: geometry.size.width * 0.78,
                    height: geometry.size.height * 0.135
                )
                .position(
                    x: geometry.size.width * 0.5,
                    y: geometry.size.height * 0.9325
                )
                .accessibilityIdentifier("tftBottomStrip")
            }
        }
        .background(palette.background)
        .accessibilityIdentifier("tftDashboard")
        .onAppear {
            updateTheme()
            scheduleToast()
        }
        .onChange(of: telemetry) { _, _ in
            updateTheme()
            scheduleToast()
        }
        .onChange(of: themeMode) { _, _ in updateTheme() }
    }

    private func updateTheme() {
        resolvedTheme = RideThemeResolver.resolve(
            mode: themeMode,
            ambientLight: dashboard.ambientLight,
            previous: resolvedTheme,
            thresholds: themeThresholds
        )
    }

    private func scheduleToast() {
        guard data.toastMessage != nil else {
            toastVisible = false
            return
        }
        toastVisible = true
        Task {
            try? await Task.sleep(for: .seconds(4))
            withAnimation(.easeOut(duration: 0.22)) {
                toastVisible = false
            }
        }
    }
}

private struct TFTRibbonTachometer: View, Animatable {
    let data: TFTDashboardData
    let palette: RidePalette
    var fillFraction: Double

    var animatableData: Double {
        get { fillFraction }
        set { fillFraction = newValue }
    }

    private var maximumRpm: Double {
        data.tachometerMaximumRpm ?? 9_000
    }

    private var warningFraction: CGFloat {
        guard maximumRpm > 0 else { return 7 / 9 }
        return CGFloat(
            min(max((data.warningStartRpm ?? 7_000) / maximumRpm, 0), 1)
        )
    }

    private var redFraction: CGFloat {
        guard maximumRpm > 0 else { return 8 / 9 }
        return CGFloat(
            min(
                max(
                    (data.redStartRpm ?? 8_000) / maximumRpm,
                    Double(warningFraction)
                ),
                1
            )
        )
    }

    var body: some View {
        Canvas { context, size in
            let geometry = TFTRibbonGeometry.resolve(size)
            let ribbon = geometry.closedPath
            let activeEnd = geometry.x(at: min(CGFloat(fillFraction), warningFraction))

            context.fill(
                ribbon,
                with: .color(TFTRibbonColors.inactive)
            )

            var activeContext = context
            activeContext.clip(
                to: Path(
                    CGRect(
                        x: geometry.upperStart.x,
                        y: 0,
                        width: max(activeEnd - geometry.upperStart.x, 0),
                        height: size.height
                    )
                )
            )
            activeContext.fill(
                ribbon,
                with: .linearGradient(
                    Gradient(
                        colors: [
                            TFTRibbonColors.activeStart,
                            TFTRibbonColors.activeEnd
                        ]
                    ),
                    startPoint: geometry.upperStart,
                    endPoint: geometry.upperEnd
                )
            )

            let warningStart = geometry.x(at: warningFraction)
            let redStart = geometry.x(at: redFraction)
            var warningContext = context
            warningContext.clip(
                to: Path(
                    CGRect(
                        x: warningStart,
                        y: 0,
                        width: max(redStart - warningStart, 0),
                        height: size.height
                    )
                )
            )
            warningContext.fill(
                ribbon,
                with: .color(TFTRibbonColors.warning)
            )

            var redContext = context
            redContext.clip(
                to: Path(
                    CGRect(
                        x: redStart,
                        y: 0,
                        width: max(size.width - redStart, 0),
                        height: size.height
                    )
                )
            )
            redContext.fill(ribbon, with: .color(TFTRibbonColors.red))

            context.stroke(
                geometry.upperPath,
                with: .color(palette.primaryText.opacity(0.76)),
                style: StrokeStyle(lineWidth: 1.1, lineCap: .round)
            )
            context.stroke(
                geometry.lowerPath,
                with: .color(TFTRibbonColors.activeEnd.opacity(0.72)),
                style: StrokeStyle(lineWidth: 1.1, lineCap: .round)
            )

            for index in 0...9 {
                let point = geometry.upperPoint(CGFloat(index) / 9)
                context.draw(
                    Text("\(index)")
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundStyle(palette.primaryText),
                    at: CGPoint(x: point.x, y: point.y - 18),
                    anchor: .center
                )
            }

            context.draw(
                Text("×1000 RPM")
                    .font(.system(size: 8, weight: .medium, design: .monospaced))
                    .tracking(0.7)
                    .foregroundStyle(palette.secondaryText),
                at: geometry.bandCenter(0.47),
                anchor: .center
            )
        }
    }
}

private struct TFTTopLine: View {
    let data: TFTDashboardData
    let palette: RidePalette
    let compact: Bool

    var body: some View {
        HStack(spacing: 0) {
            topValue(
                label: "TRIP",
                value: data.tripDistanceKm.valueOrDash("km", decimals: 1)
            )
            topValue(label: "MODE", value: "ROAD", selected: true)
            topValue(
                label: "RANGE",
                value: data.rangeKm.valueOrDash("km", decimals: 0)
            )
        }
    }

    private func topValue(
        label: String,
        value: String,
        selected: Bool = false
    ) -> some View {
        VStack(spacing: 3) {
            Text(label)
                .font(.system(size: compact ? 7 : 9))
                .tracking(1)
                .foregroundStyle(palette.secondaryText)
                .lineLimit(1)
            Text(value)
                .font(
                    .system(
                        size: compact ? 13 : 16,
                        weight: .bold,
                        design: .monospaced
                    )
                )
                .foregroundStyle(
                    selected ? TFTRibbonColors.activeEnd : palette.primaryText
                )
                .lineLimit(1)
            if selected {
                Rectangle()
                    .fill(palette.accent)
                    .frame(width: compact ? 34 : 42, height: 2)
            }
        }
        .frame(maxWidth: .infinity, alignment: .top)
    }
}

private struct TFTSpeedCluster: View {
    let data: TFTDashboardData
    let palette: RidePalette
    let compact: Bool

    var body: some View {
        HStack(alignment: .lastTextBaseline, spacing: 3) {
            Text(data.speedKmh.wholeOrDash)
                .font(
                    .system(
                        size: compact ? 78 : 102,
                        weight: .light,
                        design: .monospaced
                    )
                )
                .foregroundStyle(palette.primaryText)
                .lineLimit(1)
            Text("km/h")
                .font(.system(size: compact ? 14 : 18, design: .monospaced))
                .foregroundStyle(palette.secondaryText)
                .padding(.bottom, compact ? 10 : 14)
        }
    }
}

private struct TFTGear: View {
    let gear: String
    let palette: RidePalette
    let compact: Bool

    var body: some View {
        Text(gear.isEmpty ? "—" : gear)
            .font(
                .system(
                    size: compact ? 74 : 94,
                    weight: .medium,
                    design: .monospaced
                )
            )
            .foregroundStyle(gear == "N" ? palette.valid : palette.primaryText)
            .lineLimit(1)
    }
}

private struct TFTSideIndicators: View {
    let side: TFTIndicatorSide
    let data: TFTDashboardData
    let palette: RidePalette
    let compact: Bool

    private var indicators: [TFTSideIndicator] {
        switch side {
        case .left:
            return [
                TFTSideIndicator(icon: .turnLeft, active: false, color: palette.valid),
                TFTSideIndicator(
                    icon: .highBeam,
                    active: data.activeIndicators.contains(.highBeam),
                    color: palette.highBeam
                ),
                TFTSideIndicator(icon: .lowBeam, active: true, color: palette.primaryText),
                TFTSideIndicator(
                    icon: .fogLight,
                    active: data.activeIndicators.contains(.fogLights),
                    color: palette.primaryText
                )
            ]
        case .right:
            return [
                TFTSideIndicator(icon: .turnRight, active: false, color: palette.valid),
                TFTSideIndicator(
                    icon: .abs,
                    active: data.activeIndicators.contains(.abs),
                    color: palette.warning
                ),
                TFTSideIndicator(
                    icon: .engine,
                    active: data.activeIndicators.contains(.engineWarning),
                    color: palette.warning
                ),
                TFTSideIndicator(
                    icon: .warning,
                    active: data.activeIndicators.contains(.svcError),
                    color: palette.critical
                ),
                TFTSideIndicator(
                    icon: .recording,
                    active: data.canRecording,
                    color: palette.valid
                )
            ]
        }
    }

    var body: some View {
        VStack {
            ForEach(indicators) { indicator in
                TFTSideIndicatorGlyph(
                    indicator: indicator,
                    inactive: palette.disabledText.opacity(0.46),
                    compact: compact
                )
                .frame(maxHeight: .infinity)
            }
        }
        .accessibilityIdentifier("tftSideIndicators_\(side.rawValue)")
    }
}

private struct TFTSideIndicatorGlyph: View {
    let indicator: TFTSideIndicator
    let inactive: Color
    let compact: Bool

    private var color: Color {
        indicator.active ? indicator.color : inactive
    }

    @ViewBuilder
    var body: some View {
        switch indicator.icon {
        case .turnLeft:
            Image(systemName: "arrow.left")
                .font(.system(size: compact ? 17 : 20, weight: .bold))
                .foregroundStyle(color)
        case .turnRight:
            Image(systemName: "arrow.right")
                .font(.system(size: compact ? 17 : 20, weight: .bold))
                .foregroundStyle(color)
        case .highBeam, .lowBeam, .fogLight:
            TFTLampGlyph(icon: indicator.icon, color: color, compact: compact)
        case .abs:
            Text("ABS")
                .font(.system(size: compact ? 6 : 7, weight: .bold))
                .foregroundStyle(color)
                .frame(width: compact ? 24 : 29, height: compact ? 24 : 29)
                .overlay {
                    Circle().stroke(color, lineWidth: 1.5)
                }
        case .engine:
            Image(systemName: "engine.combustion.fill")
                .font(.system(size: compact ? 17 : 20))
                .foregroundStyle(color)
        case .warning:
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: compact ? 18 : 21))
                .foregroundStyle(color)
        case .recording:
            Image(systemName: "record.circle")
                .font(.system(size: compact ? 18 : 21))
                .foregroundStyle(color)
        }
    }
}

private struct TFTLampGlyph: View {
    let icon: TFTSideIcon
    let color: Color
    let compact: Bool

    var body: some View {
        Canvas { context, size in
            var lamp = Path()
            lamp.addArc(
                center: CGPoint(x: size.width * 0.16, y: size.height * 0.5),
                radius: size.height * 0.32,
                startAngle: .degrees(90),
                endAngle: .degrees(270),
                clockwise: false
            )
            context.stroke(
                lamp,
                with: .color(color),
                style: StrokeStyle(lineWidth: 1.6, lineCap: .round)
            )
            var edge = Path()
            edge.move(to: CGPoint(x: size.width * 0.31, y: size.height * 0.18))
            edge.addLine(to: CGPoint(x: size.width * 0.31, y: size.height * 0.82))
            context.stroke(edge, with: .color(color), lineWidth: 1.6)

            for index in 0..<3 {
                let y = size.height * (0.28 + CGFloat(index) * 0.22)
                var beam = Path()
                beam.move(to: CGPoint(x: size.width * 0.48, y: y))
                switch icon {
                case .fogLight:
                    beam.addCurve(
                        to: CGPoint(x: size.width, y: y),
                        control1: CGPoint(
                            x: size.width * 0.64,
                            y: y - size.height * 0.10
                        ),
                        control2: CGPoint(
                            x: size.width * 0.88,
                            y: y + size.height * 0.10
                        )
                    )
                case .lowBeam:
                    beam.addLine(
                        to: CGPoint(
                            x: size.width,
                            y: y + size.height * 0.12
                        )
                    )
                default:
                    beam.addLine(to: CGPoint(x: size.width, y: y))
                }
                context.stroke(
                    beam,
                    with: .color(color),
                    style: StrokeStyle(lineWidth: 1.6, lineCap: .round)
                )
            }
        }
        .frame(
            width: compact ? 24 : 29,
            height: compact ? 16 : 19
        )
    }
}

private struct TFTConnectionStatus: View {
    let data: TFTDashboardData
    let palette: RidePalette
    let compact: Bool

    var body: some View {
        HStack {
            status("BLE", active: data.bleConnected)
            Spacer()
            status("CAN", active: data.canConnected)
            Spacer()
            status("REC", active: data.canRecording)
        }
    }

    private func status(_ label: String, active: Bool) -> some View {
        HStack(spacing: 4) {
            Circle()
                .fill(active ? palette.valid : palette.critical)
                .frame(width: compact ? 5 : 6, height: compact ? 5 : 6)
            Text(label)
                .font(.system(size: compact ? 7 : 8, weight: .bold))
                .tracking(0.7)
                .foregroundStyle(palette.secondaryText)
        }
    }
}

private struct TFTBottomTelemetry: View {
    let data: TFTDashboardData
    let palette: RidePalette
    let compact: Bool

    var body: some View {
        HStack(spacing: 0) {
            metric("FUEL", data.fuelPercent.valueOrDash("%", decimals: 0))
            metric("BAT", data.batteryVoltage.valueOrDash("V", decimals: 1))
            metric("SVC", data.svcCurrentA.valueOrDash("A", decimals: 1))
            metric(
                "ENGINE",
                data.engineTemperatureCelsius.valueOrDash("°C", decimals: 0)
            )
            metric("TIME", data.currentTime)
        }
    }

    private func metric(_ label: String, _ value: String) -> some View {
        VStack(spacing: 3) {
            Text(label)
                .font(.system(size: compact ? 7 : 9))
                .tracking(0.9)
                .foregroundStyle(palette.secondaryText)
                .lineLimit(1)
            Text(value)
                .font(
                    .system(
                        size: compact ? 12 : 15,
                        weight: .semibold,
                        design: .monospaced
                    )
                )
                .foregroundStyle(palette.primaryText)
                .lineLimit(1)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

private enum TFTIndicatorSide: String {
    case left
    case right
}

private enum TFTSideIcon {
    case turnLeft
    case turnRight
    case highBeam
    case lowBeam
    case fogLight
    case abs
    case engine
    case warning
    case recording
}

private struct TFTSideIndicator: Identifiable {
    let icon: TFTSideIcon
    let active: Bool
    let color: Color

    var id: String { String(describing: icon) }
}

private struct TFTRibbonGeometry {
    let upperStart: CGPoint
    let upperControl1: CGPoint
    let upperControl2: CGPoint
    let upperMid: CGPoint
    let upperControl3: CGPoint
    let upperControl4: CGPoint
    let upperEnd: CGPoint
    let lowerStart: CGPoint
    let lowerControl1: CGPoint
    let lowerControl2: CGPoint
    let lowerMid: CGPoint
    let lowerControl3: CGPoint
    let lowerControl4: CGPoint
    let lowerEnd: CGPoint

    var closedPath: Path {
        var path = Path()
        path.move(to: upperStart)
        path.addCurve(
            to: upperMid,
            control1: upperControl1,
            control2: upperControl2
        )
        path.addCurve(
            to: upperEnd,
            control1: upperControl3,
            control2: upperControl4
        )
        path.addLine(to: lowerEnd)
        path.addCurve(
            to: lowerMid,
            control1: lowerControl4,
            control2: lowerControl3
        )
        path.addCurve(
            to: lowerStart,
            control1: lowerControl2,
            control2: lowerControl1
        )
        path.closeSubpath()
        return path
    }

    var upperPath: Path {
        var path = Path()
        path.move(to: upperStart)
        path.addCurve(
            to: upperMid,
            control1: upperControl1,
            control2: upperControl2
        )
        path.addCurve(
            to: upperEnd,
            control1: upperControl3,
            control2: upperControl4
        )
        return path
    }

    var lowerPath: Path {
        var path = Path()
        path.move(to: lowerStart)
        path.addCurve(
            to: lowerMid,
            control1: lowerControl1,
            control2: lowerControl2
        )
        path.addCurve(
            to: lowerEnd,
            control1: lowerControl3,
            control2: lowerControl4
        )
        return path
    }

    func upperPoint(_ fraction: CGFloat) -> CGPoint {
        piecewiseCubic(
            fraction,
            upperStart,
            upperControl1,
            upperControl2,
            upperMid,
            upperControl3,
            upperControl4,
            upperEnd
        )
    }

    func lowerPoint(_ fraction: CGFloat) -> CGPoint {
        piecewiseCubic(
            fraction,
            lowerStart,
            lowerControl1,
            lowerControl2,
            lowerMid,
            lowerControl3,
            lowerControl4,
            lowerEnd
        )
    }

    func x(at fraction: CGFloat) -> CGFloat {
        upperPoint(fraction).x
    }

    func bandCenter(_ fraction: CGFloat) -> CGPoint {
        let upper = upperPoint(fraction)
        let lower = lowerPoint(fraction)
        return CGPoint(
            x: (upper.x + lower.x) / 2,
            y: (upper.y + lower.y) / 2
        )
    }

    static func resolve(_ size: CGSize) -> TFTRibbonGeometry {
        TFTRibbonGeometry(
            upperStart: CGPoint(x: size.width * 0.14, y: size.height * 0.62),
            upperControl1: CGPoint(x: size.width * 0.27, y: size.height * 0.64),
            upperControl2: CGPoint(x: size.width * 0.35, y: size.height * 0.54),
            upperMid: CGPoint(x: size.width * 0.47, y: size.height * 0.43),
            upperControl3: CGPoint(x: size.width * 0.59, y: size.height * 0.33),
            upperControl4: CGPoint(x: size.width * 0.72, y: size.height * 0.25),
            upperEnd: CGPoint(x: size.width * 0.85, y: size.height * 0.27),
            lowerStart: CGPoint(x: size.width * 0.14, y: size.height * 0.69),
            lowerControl1: CGPoint(x: size.width * 0.27, y: size.height * 0.72),
            lowerControl2: CGPoint(x: size.width * 0.38, y: size.height * 0.65),
            lowerMid: CGPoint(x: size.width * 0.51, y: size.height * 0.56),
            lowerControl3: CGPoint(x: size.width * 0.64, y: size.height * 0.48),
            lowerControl4: CGPoint(x: size.width * 0.76, y: size.height * 0.43),
            lowerEnd: CGPoint(x: size.width * 0.85, y: size.height * 0.45)
        )
    }
}

private enum TFTRibbonColors {
    static let inactive = Color(red: 20 / 255, green: 37 / 255, blue: 58 / 255)
    static let activeStart = Color(red: 0, green: 102 / 255, blue: 177 / 255)
    static let activeEnd = Color(red: 45 / 255, green: 156 / 255, blue: 1)
    static let warning = Color(red: 242 / 255, green: 169 / 255, blue: 0)
    static let red = Color(red: 226 / 255, green: 27 / 255, blue: 45 / 255)
}

private func piecewiseCubic(
    _ fraction: CGFloat,
    _ start: CGPoint,
    _ control1: CGPoint,
    _ control2: CGPoint,
    _ middle: CGPoint,
    _ control3: CGPoint,
    _ control4: CGPoint,
    _ end: CGPoint
) -> CGPoint {
    let clamped = min(max(fraction, 0), 1)
    if clamped <= 0.5 {
        return cubicPoint(
            clamped * 2,
            start,
            control1,
            control2,
            middle
        )
    }
    return cubicPoint(
        (clamped - 0.5) * 2,
        middle,
        control3,
        control4,
        end
    )
}

private func cubicPoint(
    _ fraction: CGFloat,
    _ start: CGPoint,
    _ control1: CGPoint,
    _ control2: CGPoint,
    _ end: CGPoint
) -> CGPoint {
    let inverse = 1 - fraction
    let startWeight = inverse * inverse * inverse
    let firstWeight = 3 * inverse * inverse * fraction
    let secondWeight = 3 * inverse * fraction * fraction
    let endWeight = fraction * fraction * fraction
    return CGPoint(
        x: start.x * startWeight
            + control1.x * firstWeight
            + control2.x * secondWeight
            + end.x * endWeight,
        y: start.y * startWeight
            + control1.y * firstWeight
            + control2.y * secondWeight
            + end.y * endWeight
    )
}

private extension Optional where Wrapped == Double {
    var wholeOrDash: String {
        guard let self else { return "—" }
        return String(Int(self.rounded()))
    }

    func valueOrDash(_ unit: String, decimals: Int) -> String {
        guard let self else { return "—" }
        return "\(String(format: "%.\(decimals)f", self)) \(unit)"
    }
}

#Preview("SVC TFT Landscape", traits: .landscapeLeft) {
    DashboardView(
        telemetry: DashboardPreviewFixtures.telemetry,
        connectionState: .connected,
        isConnecting: false,
        profile: VehiclePerformanceCatalog.load().resolve(
            profileId: "bmw-r1200gs-k25-2007"
        ),
        themeMode: .night,
        themeThresholds: .default,
        demoMode: true
    )
}

private enum DashboardPreviewFixtures {
    static var telemetry: TelemetrySnapshot {
        guard
            let url = Bundle.main.url(
                forResource: "device-v1",
                withExtension: "json"
            ),
            let data = try? Data(contentsOf: url),
            let snapshot = try? JSONDecoder().decode(
                TelemetrySnapshot.self,
                from: data
            )
        else {
            fatalError("Missing SVC preview telemetry")
        }
        return snapshot
    }
}
