import SwiftUI

struct DashboardView: View {
    let telemetry: TelemetrySnapshot
    let connectionState: ConnectionState
    let isConnecting: Bool
    let profile: VehiclePerformanceProfile
    let themeMode: RideThemeMode
    let themeThresholds: RideThemeThresholds

    @Environment(\.accessibilityReduceMotion) private var systemReduceMotion
    @State private var resolvedTheme = RideResolvedTheme.night
    @State private var tachometerZone = TachometerZone.unavailable
    @State private var leanExtrema = LeanExtrema()

    private var dashboard: RideDashboardState {
        RideDashboardState.build(
            telemetry: telemetry,
            connectionState: connectionState,
            isConnecting: isConnecting,
            profile: profile
        )
    }

    private var palette: RidePalette {
        RidePalette.resolve(resolvedTheme)
    }

    var body: some View {
        GeometryReader { geometry in
            Group {
                if geometry.size.width > geometry.size.height * 1.12 {
                    landscapeContent
                } else {
                    portraitContent
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(palette.background)
        }
        .toolbarBackground(palette.background, for: .navigationBar)
        .toolbarColorScheme(.dark, for: .navigationBar)
        .navigationTitle("SVC Ride")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear(perform: updateDerivedState)
        .onChange(of: telemetry) { _, _ in updateDerivedState() }
        .onChange(of: themeMode) { _, _ in updateDerivedState() }
        .onChange(of: profile.id) { _, _ in
            tachometerZone = .unavailable
            updateDerivedState()
        }
    }

    private var landscapeContent: some View {
        VStack(spacing: RideDesignTokens.compactSpacing) {
            RideStatusBar(dashboard: dashboard, palette: palette)
            HStack(spacing: RideDesignTokens.spacing) {
                LeanPanel(
                    lean: dashboard.leanAngle,
                    extrema: leanExtrema,
                    speed: dashboard.speed,
                    palette: palette,
                    reset: resetLeanExtrema
                )
                .frame(maxWidth: 220)

                RideCenterPanel(
                    dashboard: dashboard,
                    zone: tachometerZone,
                    palette: palette,
                    reduceMotion: systemReduceMotion
                )
                .frame(maxWidth: .infinity)

                RideMetricPanel(dashboard: dashboard, palette: palette)
                    .frame(maxWidth: 220)
            }
            RideAlertBanner(alert: dashboard.activeAlert, palette: palette)
        }
        .padding(RideDesignTokens.contentPadding)
    }

    private var portraitContent: some View {
        ScrollView {
            VStack(spacing: RideDesignTokens.spacing) {
                RideStatusBar(dashboard: dashboard, palette: palette)
                RideCenterPanel(
                    dashboard: dashboard,
                    zone: tachometerZone,
                    palette: palette,
                    reduceMotion: systemReduceMotion
                )
                .frame(minHeight: 360)
                RideAlertBanner(alert: dashboard.activeAlert, palette: palette)
                LeanPanel(
                    lean: dashboard.leanAngle,
                    extrema: leanExtrema,
                    speed: dashboard.speed,
                    palette: palette,
                    reset: resetLeanExtrema
                )
                .frame(minHeight: 185)
                RideMetricPanel(dashboard: dashboard, palette: palette)
            }
            .padding(RideDesignTokens.contentPadding)
        }
        .background(palette.background)
    }

    private func updateDerivedState() {
        let nextTheme = RideThemeResolver.resolve(
            mode: themeMode,
            ambientLight: dashboard.ambientLight,
            previous: resolvedTheme,
            thresholds: themeThresholds
        )
        let nextZone = TachometerZoneResolver.zoneWithHysteresis(
            rpm: dashboard.engineRpm.displayValue,
            profile: profile,
            previous: tachometerZone
        )
        if systemReduceMotion {
            resolvedTheme = nextTheme
            tachometerZone = nextZone
        } else {
            withAnimation(
                .easeOut(
                    duration: RideMotionPolicy.duration(
                        reduceMotion: systemReduceMotion,
                        standardDuration: RideDesignTokens.themeAnimation
                    )
                )
            ) {
                resolvedTheme = nextTheme
                tachometerZone = nextZone
            }
        }
        leanExtrema.observe(dashboard.leanAngle.displayValue)
    }

    private func resetLeanExtrema() {
        _ = leanExtrema.resetIfStationary(speed: dashboard.speed)
    }
}

private struct RideStatusBar: View {
    let dashboard: RideDashboardState
    let palette: RidePalette

    var body: some View {
        HStack(spacing: RideDesignTokens.compactSpacing) {
            Text(dashboard.profile.displayName.uppercased())
                .font(.caption.weight(.semibold))
                .tracking(1.4)
                .foregroundStyle(palette.secondaryText)
                .lineLimit(1)
            Spacer()
            StatusPill(
                label: dashboard.bleLabel,
                state: dashboard.bleState,
                palette: palette
            )
            StatusPill(
                label: dashboard.canState.displayValue?.uppercased() ?? "CAN —",
                state: dashboard.canState.state,
                palette: palette
            )
        }
        .frame(minHeight: RideDesignTokens.statusHeight)
    }
}

private struct StatusPill: View {
    let label: String
    let state: RideDataState
    let palette: RidePalette

    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(state.color(palette: palette))
                .frame(width: 7, height: 7)
            Text(label)
                .font(.caption2.weight(.bold))
                .tracking(0.7)
        }
        .foregroundStyle(palette.primaryText)
        .padding(.horizontal, 10)
        .padding(.vertical, 7)
        .background(palette.surface, in: Capsule())
        .overlay(Capsule().stroke(palette.divider, lineWidth: 1))
    }
}

private struct RideCenterPanel: View {
    let dashboard: RideDashboardState
    let zone: TachometerZone
    let palette: RidePalette
    let reduceMotion: Bool

    var body: some View {
        VStack(spacing: 0) {
            ZStack {
                TachometerDial(
                    rpm: dashboard.engineRpm.displayValue,
                    profile: dashboard.profile,
                    zone: zone,
                    palette: palette,
                    reduceMotion: reduceMotion
                )
                HStack(alignment: .firstTextBaseline, spacing: 20) {
                    VStack(spacing: 0) {
                        Text(speedText)
                            .font(.system(size: 82, weight: .semibold, design: .rounded))
                            .monospacedDigit()
                            .minimumScaleFactor(0.55)
                            .lineLimit(1)
                        Text("km/h")
                            .font(.caption.weight(.semibold))
                            .tracking(1.3)
                            .foregroundStyle(palette.secondaryText)
                    }
                    VStack(spacing: 0) {
                        Text(dashboard.gear.displayValue)
                            .font(.system(size: 58, weight: .bold, design: .rounded))
                            .monospacedDigit()
                        Text("GEAR")
                            .font(.caption2.weight(.semibold))
                            .tracking(1.4)
                            .foregroundStyle(palette.secondaryText)
                    }
                }
                .foregroundStyle(palette.primaryText)
                .offset(y: 14)
            }
            .frame(minHeight: 250)

            HStack(alignment: .firstTextBaseline, spacing: 8) {
                Text("RPM")
                    .font(.caption.weight(.semibold))
                    .tracking(1.2)
                    .foregroundStyle(palette.secondaryText)
                Text(rpmText)
                    .font(.title2.weight(.bold))
                    .monospacedDigit()
                    .foregroundStyle(zone.color(palette: palette))
            }
            if dashboard.engineRpm.state != .valid {
                Text(dashboard.engineRpm.state.label)
                    .font(.caption2.weight(.semibold))
                    .foregroundStyle(dashboard.engineRpm.state.color(palette: palette))
            }
        }
        .padding(.horizontal, RideDesignTokens.compactSpacing)
    }

    private var speedText: String {
        dashboard.speed.displayValue.map {
            $0.formatted(.number.precision(.fractionLength(0)))
        } ?? "—"
    }

    private var rpmText: String {
        dashboard.engineRpm.displayValue.map {
            $0.formatted(.number.precision(.fractionLength(0)))
        } ?? "—"
    }
}

private struct TachometerDial: View {
    let rpm: Double?
    let profile: VehiclePerformanceProfile
    let zone: TachometerZone
    let palette: RidePalette
    let reduceMotion: Bool

    @State private var displayedFraction = 0.0

    private let startDegrees = 150.0
    private let sweepDegrees = 240.0

    var body: some View {
        Canvas { context, size in
            let radius = min(size.width, size.height) * 0.43
            let center = CGPoint(x: size.width / 2, y: size.height / 2 + 18)
            drawArc(
                context: &context,
                center: center,
                radius: radius,
                startFraction: 0,
                endFraction: 1,
                color: palette.divider,
                width: RideDesignTokens.gaugeLineWidth
            )
            if let maximum = profile.tachometerScaleMaxRpm, maximum > 0 {
                drawProfileZones(
                    context: &context,
                    center: center,
                    radius: radius,
                    maximum: Double(maximum)
                )
                drawArc(
                    context: &context,
                    center: center,
                    radius: radius - 1,
                    startFraction: 0,
                    endFraction: displayedFraction,
                    color: zone.color(palette: palette),
                    width: RideDesignTokens.gaugeLineWidth - 5
                )
                drawTicks(
                    context: &context,
                    center: center,
                    radius: radius,
                    maximum: maximum
                )
            } else {
                context.draw(
                    Text("PROFILE SCALE —")
                        .font(.caption2.weight(.semibold))
                        .foregroundColor(palette.secondaryText),
                    at: CGPoint(x: center.x, y: center.y - radius)
                )
            }
        }
        .onAppear(perform: updateFraction)
        .onChange(of: rpm) { _, _ in updateFraction() }
        .onChange(of: profile.id) { _, _ in updateFraction() }
    }

    private func drawProfileZones(
        context: inout GraphicsContext,
        center: CGPoint,
        radius: CGFloat,
        maximum: Double
    ) {
        if let warning = profile.warningStartRpm {
            let warningStart = min(max(Double(warning) / maximum, 0), 1)
            let redStart = profile.redZoneStartRpm
                .map { min(max(Double($0) / maximum, warningStart), 1) }
                ?? 1
            drawArc(
                context: &context,
                center: center,
                radius: radius,
                startFraction: warningStart,
                endFraction: redStart,
                color: palette.warning.opacity(0.55),
                width: RideDesignTokens.gaugeLineWidth
            )
        }
        if let red = profile.redZoneStartRpm {
            drawArc(
                context: &context,
                center: center,
                radius: radius,
                startFraction: min(max(Double(red) / maximum, 0), 1),
                endFraction: 1,
                color: palette.critical.opacity(0.65),
                width: RideDesignTokens.gaugeLineWidth
            )
        }
    }

    private func drawTicks(
        context: inout GraphicsContext,
        center: CGPoint,
        radius: CGFloat,
        maximum: Int
    ) {
        let finalTick = max(maximum / 1_000, 1)
        for tick in 0...finalTick {
            let fraction = Double(tick) / Double(finalTick)
            let radians = (startDegrees + sweepDegrees * fraction) * .pi / 180
            let labelRadius = radius - 28
            let point = CGPoint(
                x: center.x + CGFloat(cos(radians)) * labelRadius,
                y: center.y + CGFloat(sin(radians)) * labelRadius
            )
            context.draw(
                Text("\(tick)")
                    .font(.caption2.weight(.bold))
                    .foregroundColor(palette.secondaryText),
                at: point
            )
        }
    }

    private func drawArc(
        context: inout GraphicsContext,
        center: CGPoint,
        radius: CGFloat,
        startFraction: Double,
        endFraction: Double,
        color: Color,
        width: CGFloat
    ) {
        guard endFraction > startFraction else { return }
        var path = Path()
        path.addArc(
            center: center,
            radius: radius,
            startAngle: .degrees(startDegrees + sweepDegrees * startFraction),
            endAngle: .degrees(startDegrees + sweepDegrees * endFraction),
            clockwise: false
        )
        context.stroke(path, with: .color(color), lineWidth: width)
    }

    private func updateFraction() {
        let target: Double
        if let rpm, let maximum = profile.tachometerScaleMaxRpm, maximum > 0 {
            target = min(max(rpm / Double(maximum), 0), 1)
        } else {
            target = 0
        }
        if reduceMotion {
            displayedFraction = target
        } else {
            withAnimation(
                .easeOut(
                    duration: RideMotionPolicy.duration(reduceMotion: reduceMotion)
                )
            ) {
                displayedFraction = target
            }
        }
    }
}

private struct LeanPanel: View {
    let lean: RideValue<Double>
    let extrema: LeanExtrema
    let speed: RideValue<Double>
    let palette: RidePalette
    let reset: () -> Void

    private var leanDegrees: Double? {
        lean.displayValue.map { min(max($0, -60), 60) }
    }

    var body: some View {
        VStack(spacing: RideDesignTokens.compactSpacing) {
            HStack {
                Text("SVC LEAN")
                    .font(.caption.weight(.semibold))
                    .tracking(1.2)
                Spacer()
                Text(lean.state.label)
                    .font(.caption2.weight(.bold))
                    .foregroundStyle(lean.state.color(palette: palette))
            }
            .foregroundStyle(palette.secondaryText)

            ZStack {
                Circle()
                    .stroke(palette.divider, lineWidth: 1)
                ForEach([-60, -45, -30, -20, -10, 0, 10, 20, 30, 45, 60], id: \.self) {
                    angle in
                    Capsule()
                        .fill(angle == 0 ? palette.primaryText : palette.divider)
                        .frame(width: angle == 0 ? 2 : 1, height: angle == 0 ? 13 : 8)
                        .offset(y: -68)
                        .rotationEffect(.degrees(Double(angle)))
                }
                Rectangle()
                    .fill(palette.accentBright)
                    .frame(width: 112, height: 3)
                    .rotationEffect(.degrees(leanDegrees ?? 0))
                Image(systemName: "motorcycle")
                    .font(.system(size: 34, weight: .medium))
                    .foregroundStyle(
                        leanDegrees == nil ? palette.secondaryText : palette.primaryText
                    )
                    .rotationEffect(.degrees(leanDegrees ?? 0))
                Text(leanText)
                    .font(.title3.weight(.bold))
                    .monospacedDigit()
                    .foregroundStyle(palette.primaryText)
                    .offset(y: 50)
            }
            .frame(width: 150, height: 150)

            HStack {
                Text("L \(extrema.maximumLeftDegrees, specifier: "%.0f")°")
                Spacer()
                Text("R \(extrema.maximumRightDegrees, specifier: "%.0f")°")
            }
            .font(.caption.monospacedDigit())
            .foregroundStyle(palette.secondaryText)

            Button("Reset maxima", action: reset)
                .buttonStyle(.borderless)
                .font(.caption.weight(.semibold))
                .disabled(speed.displayValue != 0)
        }
        .padding(RideDesignTokens.spacing)
        .background(palette.surface, in: RoundedRectangle(cornerRadius: RideDesignTokens.cornerRadius))
        .overlay(
            RoundedRectangle(cornerRadius: RideDesignTokens.cornerRadius)
                .stroke(palette.divider, lineWidth: 1)
        )
    }

    private var leanText: String {
        guard let leanDegrees else { return "LEAN —" }
        let direction = leanDegrees < 0 ? "L" : leanDegrees > 0 ? "R" : ""
        return "\(direction) \(abs(leanDegrees).formatted(.number.precision(.fractionLength(0))))°"
            .trimmingCharacters(in: .whitespaces)
    }
}

private struct RideMetricPanel: View {
    let dashboard: RideDashboardState
    let palette: RidePalette

    var body: some View {
        VStack(spacing: RideDesignTokens.compactSpacing) {
            RideMetricCard(
                title: "ENGINE",
                value: dashboard.engineTemperature.number(fractionDigits: 0),
                unit: "°C",
                state: dashboard.engineTemperature.state,
                palette: palette
            )
            RideMetricCard(
                title: "FUEL",
                value: dashboard.fuelLevel.number(fractionDigits: 0),
                unit: "%",
                state: dashboard.fuelLevel.state,
                palette: palette
            )
            RideMetricCard(
                title: "BATTERY",
                value: dashboard.batteryVoltage.number(fractionDigits: 1),
                unit: "V",
                state: dashboard.batteryVoltage.state,
                palette: palette
            )
            RideMetricCard(
                title: "SVC CURRENT",
                value: dashboard.totalCurrent.number(fractionDigits: 1),
                unit: "A",
                state: dashboard.totalCurrent.state,
                palette: palette
            )
        }
    }
}

private struct RideMetricCard: View {
    let title: String
    let value: String
    let unit: String
    let state: RideDataState
    let palette: RidePalette

    var body: some View {
        HStack(alignment: .firstTextBaseline) {
            VStack(alignment: .leading, spacing: 3) {
                Text(title)
                    .font(.caption2.weight(.semibold))
                    .tracking(1)
                    .foregroundStyle(palette.secondaryText)
                Text(state.label)
                    .font(.caption2)
                    .foregroundStyle(state.color(palette: palette))
            }
            Spacer()
            Text(value)
                .font(.title3.weight(.bold))
                .monospacedDigit()
                .foregroundStyle(palette.primaryText)
            Text(value == "—" ? "" : unit)
                .font(.caption.weight(.semibold))
                .foregroundStyle(palette.secondaryText)
        }
        .padding(.horizontal, 12)
        .frame(maxWidth: .infinity, minHeight: 58)
        .background(palette.surface, in: RoundedRectangle(cornerRadius: RideDesignTokens.compactCornerRadius))
        .overlay(
            RoundedRectangle(cornerRadius: RideDesignTokens.compactCornerRadius)
                .stroke(palette.divider, lineWidth: 1)
        )
    }
}

private struct RideAlertBanner: View {
    let alert: RideAlert?
    let palette: RidePalette

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: alert == nil ? "shield.lefthalf.filled" : "exclamationmark.triangle.fill")
            Text(alert?.title ?? "NO ACTIVE WARNING DATA")
                .font(.subheadline.weight(.bold))
                .tracking(0.6)
            Spacer()
        }
        .foregroundStyle(alert == nil ? palette.secondaryText : .white)
        .padding(.horizontal, 14)
        .frame(maxWidth: .infinity, minHeight: 44)
        .background(backgroundColor, in: RoundedRectangle(cornerRadius: RideDesignTokens.compactCornerRadius))
        .overlay(
            RoundedRectangle(cornerRadius: RideDesignTokens.compactCornerRadius)
                .stroke(alert == nil ? palette.divider : backgroundColor, lineWidth: 1)
        )
    }

    private var backgroundColor: Color {
        switch alert?.severity {
        case .critical:
            palette.critical
        case .warning:
            palette.warning.opacity(0.88)
        case .info:
            palette.accent
        case nil:
            palette.surface
        }
    }
}

private extension RideValue where Value == Double {
    func number(fractionDigits: Int) -> String {
        displayValue?.formatted(
            .number.precision(.fractionLength(fractionDigits))
        ) ?? "—"
    }
}

private extension RideDataState {
    var label: String {
        switch self {
        case .valid: "VALID"
        case .stale: "STALE"
        case .degraded: "DEGRADED"
        case .invalid: "INVALID"
        case .unavailable: "UNAVAILABLE"
        }
    }

    func color(palette: RidePalette) -> Color {
        switch self {
        case .valid:
            palette.valid
        case .degraded, .stale:
            palette.degraded
        case .invalid:
            palette.critical
        case .unavailable:
            palette.secondaryText
        }
    }
}

private extension TachometerZone {
    func color(palette: RidePalette) -> Color {
        switch self {
        case .normal:
            palette.accentBright
        case .warning:
            palette.warning
        case .red:
            palette.critical
        case .unavailable:
            palette.secondaryText
        }
    }
}

#Preview("SVC Ride Landscape", traits: .landscapeLeft) {
    NavigationStack {
        DashboardPreview()
    }
}

#Preview("SVC Ride Portrait") {
    NavigationStack {
        DashboardPreview()
    }
}

private struct DashboardPreview: View {
    var body: some View {
        DashboardView(
            telemetry: PreviewFixtures.telemetry,
            connectionState: .connected,
            isConnecting: false,
            profile: VehiclePerformanceCatalog.load().resolve(
                profileId: "bmw-r1200gs-k25-2007"
            ),
            themeMode: .night,
            themeThresholds: .default
        )
    }
}

private enum PreviewFixtures {
    static var telemetry: TelemetrySnapshot {
        let bundle = Bundle.main
        guard
            let url = bundle.url(forResource: "device-v1", withExtension: "json"),
            let data = try? Data(contentsOf: url),
            let snapshot = try? JSONDecoder().decode(TelemetrySnapshot.self, from: data)
        else {
            fatalError("Missing SVC preview telemetry")
        }
        return snapshot
    }
}
