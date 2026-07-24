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
        RidePalette.resolve(resolvedTheme)
    }

    var body: some View {
        GeometryReader { geometry in
            let compact = geometry.size.height < 390 || geometry.size.width < 760
            let horizontalPadding: CGFloat = compact ? 16 : 24

            ZStack {
                palette.background

                TFTTachometer(data: data, palette: palette)
                    .frame(
                        width: geometry.size.width - horizontalPadding * 2,
                        height: compact ? 108 : 138
                    )
                    .position(
                        x: geometry.size.width / 2,
                        y: compact ? 54 : 69
                    )
                    .animation(
                        .easeOut(duration: reduceMotion ? 0 : 0.22),
                        value: data.engineRpm
                    )
                    .accessibilityIdentifier("tftTachometer")

                TFTActiveIndicators(
                    indicators: data.activeIndicators,
                    palette: palette,
                    compact: compact
                )
                .frame(
                    maxWidth: .infinity,
                    maxHeight: .infinity,
                    alignment: .leading
                )
                .padding(.leading, horizontalPadding)
                .padding(.bottom, 8)

                TFTConnectionIcons(data: data, palette: palette)
                    .frame(
                        maxWidth: .infinity,
                        maxHeight: .infinity,
                        alignment: .topTrailing
                    )
                    .padding(.trailing, horizontalPadding)
                    .padding(.top, 10)

                TFTSpeedCluster(data: data, palette: palette, compact: compact)
                    .position(
                        x: geometry.size.width * 0.5,
                        y: geometry.size.height * 0.55
                    )
                    .accessibilityIdentifier("tftSpeed")

                TFTGear(
                    gear: data.gear,
                    palette: palette,
                    compact: compact
                )
                .position(
                    x: geometry.size.width * 0.85,
                    y: geometry.size.height * 0.55
                )
                .accessibilityIdentifier("tftGear")

                if let criticalMessage = data.criticalMessage {
                    Text(criticalMessage.uppercased())
                        .font(.system(size: compact ? 10 : 12, weight: .bold))
                        .tracking(1.2)
                        .foregroundStyle(palette.primaryText)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 5)
                        .background(palette.critical.opacity(0.86))
                        .frame(maxHeight: .infinity, alignment: .bottom)
                        .padding(.bottom, compact ? 72 : 86)
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
                        .padding(.bottom, compact ? 80 : 96)
                        .transition(.opacity)
                        .accessibilityIdentifier("tftToast")
                }

                TFTBottomTelemetry(
                    data: data,
                    palette: palette,
                    compact: compact
                )
                .frame(height: compact ? 68 : 82)
                .frame(maxHeight: .infinity, alignment: .bottom)
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

private struct TFTTachometer: View {
    let data: TFTDashboardData
    let palette: RidePalette

    private var maximumRpm: Double {
        data.tachometerMaximumRpm ?? 0
    }

    private var activeFraction: Double {
        guard maximumRpm > 0 else { return 0 }
        return min(max((data.engineRpm ?? 0) / maximumRpm, 0), 1)
    }

    private var warningRatio: Double {
        guard maximumRpm > 0, let warning = data.warningStartRpm else { return 1 }
        return min(max(warning / maximumRpm, 0), 1)
    }

    private var redRatio: Double {
        guard maximumRpm > 0, let red = data.redStartRpm else { return 1 }
        return min(max(red / maximumRpm, warningRatio), 1)
    }

    var body: some View {
        GeometryReader { geometry in
            let segmentCount = 45
            let left = geometry.size.width * 0.035
            let right = geometry.size.width * 0.965
            let availableWidth = right - left
            let gap = min(4, availableWidth * 0.004)
            let segmentWidth =
                (availableWidth - gap * CGFloat(segmentCount - 1))
                / CGFloat(segmentCount)
            let barTop = geometry.size.height * 0.22
            let barHeight = min(23, geometry.size.height * 0.24)

            Canvas { context, size in
                for segment in 0..<segmentCount {
                    let startRatio = Double(segment) / Double(segmentCount)
                    let endRatio = Double(segment + 1) / Double(segmentCount)
                    let inactiveColor: Color = if endRatio > redRatio {
                        palette.accent.opacity(0.42)
                    } else if endRatio > warningRatio {
                        palette.warning.opacity(0.34)
                    } else {
                        palette.divider
                    }
                    let activeColor: Color = if endRatio > redRatio {
                        palette.accent
                    } else if endRatio > warningRatio {
                        palette.warning
                    } else {
                        palette.primaryText
                    }
                    let color = startRatio < activeFraction
                        ? activeColor
                        : inactiveColor
                    context.fill(
                        Path(
                            CGRect(
                                x: left + CGFloat(segment) * (segmentWidth + gap),
                                y: barTop,
                                width: segmentWidth,
                                height: barHeight
                            )
                        ),
                        with: .color(color)
                    )
                }

                let maximumLabel = maximumRpm > 0
                    ? max(Int((maximumRpm / 1_000).rounded()), 1)
                    : 9
                for index in 1...maximumLabel {
                    context.draw(
                        Text("\(index)")
                            .font(.system(size: 11, weight: .semibold, design: .monospaced))
                            .foregroundStyle(palette.secondaryText),
                        at: CGPoint(
                            x: left + availableWidth
                                * CGFloat(index) / CGFloat(maximumLabel),
                            y: barTop + barHeight + 14
                        ),
                        anchor: .center
                    )
                }
                context.draw(
                    Text("×1000  RPM")
                        .font(.system(size: 8, weight: .medium, design: .monospaced))
                        .tracking(0.8)
                        .foregroundStyle(palette.secondaryText.opacity(0.78)),
                    at: CGPoint(x: size.width / 2, y: 7),
                    anchor: .center
                )
            }
        }
    }
}

private struct TFTSpeedCluster: View {
    let data: TFTDashboardData
    let palette: RidePalette
    let compact: Bool

    var body: some View {
        VStack(spacing: 0) {
            HStack(alignment: .lastTextBaseline, spacing: 2) {
                Text(data.speedKmh.wholeOrDash)
                    .font(
                        .system(
                            size: compact ? 84 : 104,
                            weight: .light,
                            design: .monospaced
                        )
                    )
                    .foregroundStyle(palette.primaryText)
                    .lineLimit(1)
                Text("km/h")
                    .font(.system(size: compact ? 15 : 18, design: .monospaced))
                    .foregroundStyle(palette.secondaryText)
                    .padding(.bottom, compact ? 12 : 15)
            }
            Text("\(data.engineRpm.wholeOrDash) rpm")
                .font(.system(size: compact ? 11 : 13, design: .monospaced))
                .tracking(1.2)
                .foregroundStyle(palette.secondaryText)
                .accessibilityIdentifier("tftDigitalRpm")
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
                    size: compact ? 68 : 88,
                    weight: .medium,
                    design: .monospaced
                )
            )
            .foregroundStyle(gear == "N" ? palette.valid : palette.primaryText)
            .lineLimit(1)
    }
}

private struct TFTBottomTelemetry: View {
    let data: TFTDashboardData
    let palette: RidePalette
    let compact: Bool

    var body: some View {
        HStack(spacing: 0) {
            TFTMetric(
                "FUEL",
                data.fuelPercent.valueOrDash("%", decimals: 0),
                selected: true
            )
            TFTMetric("RANGE", data.rangeKm.valueOrDash("km", decimals: 0))
            TFTMetric("BAT", data.batteryVoltage.valueOrDash("V", decimals: 1))
            TFTMetric(
                "ENGINE",
                data.engineTemperatureCelsius.valueOrDash("°C", decimals: 0)
            )
            TFTMetric("TIME", data.currentTime, divider: false)
        }
        .padding(.horizontal, compact ? 16 : 24)
        .background(palette.surface)
    }

    @ViewBuilder
    private func TFTMetric(
        _ label: String,
        _ value: String,
        degraded: Bool = false,
        selected: Bool = false,
        divider: Bool = true
    ) -> some View {
        HStack(spacing: 0) {
            ZStack(alignment: .top) {
                if selected {
                    Rectangle()
                        .fill(palette.accent)
                        .frame(height: 3)
                }
                VStack(spacing: 3) {
                    Text(label)
                        .font(.system(size: compact ? 8 : 10))
                        .tracking(0.9)
                        .foregroundStyle(palette.secondaryText.opacity(0.86))
                        .lineLimit(1)
                    HStack(spacing: 2) {
                        Text(value)
                            .font(
                                .system(
                                    size: compact ? 13 : 17,
                                    weight: .semibold,
                                    design: .monospaced
                                )
                            )
                            .foregroundStyle(palette.primaryText)
                            .lineLimit(1)
                        if degraded {
                            Text("▲")
                                .font(.system(size: compact ? 7 : 8))
                                .foregroundStyle(palette.degraded)
                        }
                    }
                }
                .frame(maxHeight: .infinity)
            }
            .frame(maxWidth: .infinity)
            if divider {
                Rectangle()
                    .fill(palette.divider.opacity(0.7))
                    .frame(width: 1)
                    .padding(.vertical, 10)
            }
        }
        .frame(maxWidth: .infinity)
    }
}

private struct TFTActiveIndicators: View {
    let indicators: [TFTIndicator]
    let palette: RidePalette
    let compact: Bool

    var body: some View {
        HStack(spacing: compact ? 8 : 12) {
            ForEach(indicators) { indicator in
                TFTIndicatorGlyph(
                    indicator: indicator,
                    palette: palette,
                    compact: compact
                )
            }
        }
        .accessibilityIdentifier("tftActiveIndicators")
    }
}

private struct TFTConnectionIcons: View {
    let data: TFTDashboardData
    let palette: RidePalette

    var body: some View {
        HStack(spacing: 10) {
            if !data.bleConnected {
                connection("BLE", connected: false)
            }
            if !data.canConnected {
                connection("CAN", connected: false)
            }
        }
        .accessibilityIdentifier("tftConnectionIcons")
    }

    private func connection(_ label: String, connected: Bool) -> some View {
        HStack(spacing: 4) {
            Circle()
                .fill(connected ? palette.valid : palette.critical)
                .frame(width: 6, height: 6)
            Text(label)
                .font(.system(size: 8, weight: .bold))
                .tracking(0.8)
                .foregroundStyle(palette.secondaryText)
        }
    }
}

private struct TFTIndicatorGlyph: View {
    let indicator: TFTIndicator
    let palette: RidePalette
    let compact: Bool

    var body: some View {
        switch indicator {
        case .highBeam, .fogLights:
            Canvas { context, size in
                let color = indicator.color(palette)
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
                    style: StrokeStyle(lineWidth: 1.8, lineCap: .round)
                )
                var edge = Path()
                edge.move(to: CGPoint(x: size.width * 0.30, y: size.height * 0.18))
                edge.addLine(to: CGPoint(x: size.width * 0.30, y: size.height * 0.82))
                context.stroke(edge, with: .color(color), lineWidth: 1.8)

                for index in 0..<3 {
                    let y = size.height * (0.29 + CGFloat(index) * 0.21)
                    var beam = Path()
                    beam.move(to: CGPoint(x: size.width * 0.48, y: y))
                    if indicator == .fogLights {
                        beam.addCurve(
                            to: CGPoint(x: size.width * 0.96, y: y),
                            control1: CGPoint(x: size.width * 0.62, y: y - size.height * 0.08),
                            control2: CGPoint(x: size.width * 0.82, y: y + size.height * 0.08)
                        )
                    } else {
                        beam.addLine(to: CGPoint(x: size.width * 0.96, y: y))
                    }
                    context.stroke(
                        beam,
                        with: .color(color),
                        style: StrokeStyle(lineWidth: 1.8, lineCap: .round)
                    )
                }
                if indicator == .fogLights {
                    var slash = Path()
                    slash.move(to: CGPoint(x: size.width * 0.70, y: size.height * 0.12))
                    slash.addLine(to: CGPoint(x: size.width * 0.60, y: size.height * 0.88))
                    context.stroke(slash, with: .color(color), lineWidth: 1.8)
                }
            }
            .frame(width: compact ? 28 : 34, height: compact ? 18 : 22)
        case .abs:
            Text("ABS")
                .font(.system(size: compact ? 7 : 8, weight: .bold))
                .foregroundStyle(indicator.color(palette))
                .frame(width: compact ? 26 : 31, height: compact ? 26 : 31)
                .overlay {
                    Circle()
                        .stroke(indicator.color(palette), lineWidth: 1.6)
                }
        default:
            Text(indicator.label)
                .font(
                    .system(
                        size: indicator.label.count > 3
                            ? (compact ? 9 : 11)
                            : (compact ? 15 : 18),
                        weight: .bold
                    )
                )
                .tracking(0.8)
                .foregroundStyle(indicator.color(palette))
        }
    }
}

private extension TFTIndicator {
    func color(_ palette: RidePalette) -> Color {
        switch self {
        case .turnLeft, .turnRight, .neutral:
            palette.valid
        case .highBeam:
            palette.highBeam
        case .fogLights:
            palette.fogLight
        case .abs, .engineWarning, .tirePressure, .lowVoltage:
            palette.warning
        case .svcError:
            palette.critical
        }
    }
}

private extension Optional where Wrapped == Double {
    var wholeOrDash: String {
        guard let self else { return "—" }
        return String(Int(self.rounded()))
    }

    func numberOrDash(decimals: Int) -> String {
        guard let self else { return "—" }
        return String(format: "%.\(decimals)f", self)
    }

    func valueOrDash(_ unit: String, decimals: Int) -> String {
        guard let self else { return "—" }
        return "\(String(format: "%.\(decimals)f", self)) \(unit)"
    }

    func signedValueOrDash(_ unit: String, decimals: Int) -> String {
        guard let self else { return "—" }
        return "\(String(format: "%+.\(decimals)f", self)) \(unit)"
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
