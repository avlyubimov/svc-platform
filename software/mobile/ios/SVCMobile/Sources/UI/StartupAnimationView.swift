import SwiftUI

struct StartupAnimationView: View {
    let brandPack: BrandPack
    let timeline: StartupTimeline
    let animationEnabled: Bool
    let reduceMotion: Bool
    let critical: Bool
    let replayToken: UUID
    let onComplete: () -> Void

    @Environment(\.accessibilityReduceMotion) private var systemReduceMotion
    @State private var startedAt = Date()

    private var duration: TimeInterval {
        timeline.durationSeconds(
            animationEnabled: animationEnabled,
            reduceMotion: reduceMotion || systemReduceMotion,
            critical: critical
        )
    }

    var body: some View {
        TimelineView(.animation(minimumInterval: 1 / 60)) { context in
            let elapsed = context.date.timeIntervalSince(startedAt)
            let progress = animationEnabled
                ? min(max(elapsed / duration, 0), 1)
                : 1
            StartupVisual(
                brandPack: brandPack,
                timeline: timeline,
                progress: progress
            )
        }
        .ignoresSafeArea()
        .id(replayToken)
        .onAppear {
            startedAt = Date()
            Task {
                if duration > 0 {
                    try? await Task.sleep(for: .seconds(duration))
                }
                onComplete()
            }
        }
    }
}

private struct StartupVisual: View {
    let brandPack: BrandPack
    let timeline: StartupTimeline
    let progress: Double

    private var logoPhase: Double {
        phase(progress, 0.02, 0.20) * (1 - phase(progress, 0.25, 0.36))
    }
    private var lampCheckPhase: Double {
        phase(progress, 0.16, 0.28) * (1 - phase(progress, 0.38, 0.48))
    }
    private var sweepPhase: Double {
        progress < 0.62
            ? phase(progress, 0.28, 0.62)
            : 1 - phase(progress, 0.62, 0.80)
    }
    private var clusterPhase: Double { phase(progress, 0.72, 0.90) }
    private var transitionPhase: Double {
        phase(
            progress,
            timeline.progress(milliseconds: timeline.phases.taglineEndMs),
            1
        )
    }

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                Color(red: 5 / 255, green: 6 / 255, blue: 7 / 255)
                    .opacity(1 - transitionPhase)
                StartupBrandLines()
                .opacity(phase(progress, 0, 0.14))

                ZStack {
                    Circle()
                        .fill(Color(red: 17 / 255, green: 20 / 255, blue: 24 / 255))
                    Circle()
                        .stroke(
                            Color(red: 226 / 255, green: 27 / 255, blue: 45 / 255),
                            lineWidth: 2
                        )
                    Text("SVC")
                        .font(.system(size: 28, weight: .bold))
                        .tracking(2)
                        .foregroundStyle(SVCTheme.primaryText)
                }
                .frame(width: 116, height: 116)
                .scaleEffect(0.88 + logoPhase * 0.12)
                .opacity(logoPhase)

                HStack(spacing: 20) {
                    indicator(
                        "←",
                        color: Color(red: 74 / 255, green: 194 / 255, blue: 126 / 255)
                    )
                    indicator("HIGH", color: SVCTheme.lightBlue)
                    indicator("ABS", color: SVCTheme.warning)
                    indicator("ENGINE", color: SVCTheme.warning)
                    indicator("SVC", color: SVCTheme.critical)
                    indicator(
                        "→",
                        color: Color(red: 74 / 255, green: 194 / 255, blue: 126 / 255)
                    )
                }
                .opacity(lampCheckPhase)
                .frame(maxHeight: .infinity, alignment: .top)
                .padding(.top, 18)

                StartupTFTSegments(progress: sweepPhase)
                .frame(
                    width: geometry.size.width * 0.92,
                    height: geometry.size.height * 0.28
                )
                .frame(maxHeight: .infinity, alignment: .top)
                .opacity(phase(progress, 0.24, 0.34) * (1 - transitionPhase))

                HStack {
                    VStack(spacing: 0) {
                        Text("0")
                            .font(.system(size: 82, weight: .light))
                            .foregroundStyle(SVCTheme.primaryText)
                        Text("km/h")
                            .font(.system(size: 14))
                            .tracking(1.2)
                            .foregroundStyle(SVCTheme.secondaryText)
                    }
                    Spacer()
                    Text("N")
                        .font(.system(size: 58, weight: .medium))
                        .foregroundStyle(
                            Color(
                                red: 53 / 255,
                                green: 208 / 255,
                                blue: 127 / 255
                            )
                        )
                }
                .frame(width: geometry.size.width * 0.46)
                .opacity(clusterPhase * (1 - transitionPhase))
            }
        }
    }

    private func indicator(_ label: String, color: Color) -> some View {
        Text(label)
            .font(.system(size: 13, weight: .bold))
            .tracking(1)
            .foregroundStyle(color)
    }

    private func phase(_ value: Double, _ start: Double, _ end: Double) -> Double {
        min(max((value - start) / (end - start), 0), 1)
    }
}

private struct StartupBrandLines: View {
    var body: some View {
        GeometryReader { geometry in
            Canvas { context, size in
                let centerY = size.height / 2
                let red = Color(red: 226 / 255, green: 27 / 255, blue: 45 / 255)
                let white = Color(red: 244 / 255, green: 246 / 255, blue: 248 / 255)
                let blue = Color(red: 61 / 255, green: 165 / 255, blue: 1)

                context.stroke(
                    line(
                        from: CGPoint(x: size.width * 0.12, y: centerY - 14),
                        to: CGPoint(x: size.width * 0.43, y: centerY - 14)
                    ),
                    with: .color(red),
                    lineWidth: 2
                )
                context.stroke(
                    line(
                        from: CGPoint(x: size.width * 0.10, y: centerY),
                        to: CGPoint(x: size.width * 0.40, y: centerY)
                    ),
                    with: .color(white),
                    lineWidth: 1
                )
                context.stroke(
                    line(
                        from: CGPoint(x: size.width * 0.15, y: centerY + 14),
                        to: CGPoint(x: size.width * 0.34, y: centerY + 14)
                    ),
                    with: .color(blue),
                    lineWidth: 1
                )
                context.stroke(
                    line(
                        from: CGPoint(x: size.width * 0.57, y: centerY - 14),
                        to: CGPoint(x: size.width * 0.88, y: centerY - 14)
                    ),
                    with: .color(red),
                    lineWidth: 2
                )
                context.stroke(
                    line(
                        from: CGPoint(x: size.width * 0.60, y: centerY),
                        to: CGPoint(x: size.width * 0.90, y: centerY)
                    ),
                    with: .color(white),
                    lineWidth: 1
                )
                context.stroke(
                    line(
                        from: CGPoint(x: size.width * 0.66, y: centerY + 14),
                        to: CGPoint(x: size.width * 0.85, y: centerY + 14)
                    ),
                    with: .color(blue),
                    lineWidth: 1
                )
            }
        }
    }

    private func line(from: CGPoint, to: CGPoint) -> Path {
        var path = Path()
        path.move(to: from)
        path.addLine(to: to)
        return path
    }
}

private struct StartupTFTSegments: View {
    let progress: Double

    var body: some View {
        GeometryReader { geometry in
            let segmentCount = 45
            let left = geometry.size.width * 0.06
            let right = geometry.size.width * 0.94
            let width = right - left
            let gap: CGFloat = 4
            let segmentWidth =
                (width - gap * CGFloat(segmentCount - 1))
                / CGFloat(segmentCount)

            Canvas { context, _ in
                for segment in 0..<segmentCount {
                    let ratio = Double(segment + 1) / Double(segmentCount)
                    let inactive: Color = if ratio > 8 / 9 {
                        Color(red: 226 / 255, green: 27 / 255, blue: 45 / 255)
                            .opacity(0.42)
                    } else if ratio > 7 / 9 {
                        SVCTheme.warning.opacity(0.34)
                    } else {
                        Color(red: 52 / 255, green: 58 / 255, blue: 66 / 255)
                    }
                    let active: Color = if ratio > 8 / 9 {
                        Color(red: 226 / 255, green: 27 / 255, blue: 45 / 255)
                    } else if ratio > 7 / 9 {
                        SVCTheme.warning
                    } else {
                        Color(red: 244 / 255, green: 246 / 255, blue: 248 / 255)
                    }
                    context.fill(
                        Path(
                            CGRect(
                                x: left + CGFloat(segment) * (segmentWidth + gap),
                                y: geometry.size.height * 0.08,
                                width: segmentWidth,
                                height: 20
                            )
                        ),
                        with: .color(
                            Double(segment) / Double(segmentCount) < progress
                                ? active
                                : inactive
                        )
                    )
                }
            }
        }
    }
}
