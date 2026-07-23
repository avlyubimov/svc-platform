import SwiftUI
import WebKit

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

    private var screenOnEnd: Double {
        timeline.progress(milliseconds: timeline.phases.screenOnEndMs)
    }
    private var logoEnd: Double {
        timeline.progress(milliseconds: timeline.phases.logoEndMs)
    }
    private var identityEnd: Double {
        timeline.progress(milliseconds: timeline.phases.identityEndMs)
    }
    private var taglineEnd: Double {
        timeline.progress(milliseconds: timeline.phases.taglineEndMs)
    }
    private var logoPhase: Double { phase(progress, screenOnEnd, logoEnd) }
    private var identityPhase: Double { phase(progress, logoEnd, identityEnd) }
    private var taglinePhase: Double { phase(progress, identityEnd, taglineEnd) }
    private var transitionPhase: Double { phase(progress, taglineEnd, 1) }

    var body: some View {
        ZStack {
            SVCTheme.background
                .opacity(1 - transitionPhase)
            RadialGradient(
                colors: [SVCTheme.lightBlue.opacity(0.12), .clear],
                center: .center,
                startRadius: 0,
                endRadius: 220
            )
            .opacity(phase(progress, 0, screenOnEnd) * (1 - transitionPhase))

            VStack(spacing: 15) {
                BrandLogoView(brandPack: brandPack)
                    .frame(width: 112, height: 112)
                    .scaleEffect(0.92 + 0.08 * logoPhase - 0.06 * transitionPhase)
                    .opacity(logoPhase * (1 - transitionPhase))
                    .overlay {
                        Circle()
                            .stroke(
                                LinearGradient(
                                    colors: [.clear, .white.opacity(0.8), .clear],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                ),
                                lineWidth: 1
                            )
                            .rotationEffect(.degrees(-30))
                            .opacity(
                                phase(logoPhase, 0.38, 0.48)
                                    * (1 - phase(logoPhase, 0.48, 0.72))
                            )
                    }

                VStack(spacing: 7) {
                    if let wordmark = brandPack.wordmarkResource {
                        LocalSVGView(url: wordmark)
                            .frame(width: 210, height: 28)
                    } else {
                        Text(brandPack.manufacturerWordmark)
                            .font(.system(size: 18, weight: .semibold, design: .default))
                            .tracking(4.5)
                    }
                    Text(brandPack.vehicleModel)
                        .font(.system(size: 15, weight: .medium))
                        .tracking(2.2)
                    Text(brandPack.vehicleGeneration)
                        .font(.system(size: 12, weight: .regular))
                        .tracking(1.8)
                        .foregroundStyle(SVCTheme.secondaryText)
                }
                .foregroundStyle(SVCTheme.primaryText)
                .opacity(identityPhase * (1 - transitionPhase))

                Text(brandPack.brandTagline)
                    .font(.system(size: 12, weight: .medium))
                    .tracking(2.8)
                    .foregroundStyle(SVCTheme.primaryText)
                    .opacity(taglinePhase * (1 - transitionPhase))
            }
            .scaleEffect(1 - 0.04 * transitionPhase)

            Rectangle()
                .fill(
                    LinearGradient(
                        colors: [.clear, brandPack.accentColor, .white, .clear],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .frame(height: 1)
                .scaleEffect(x: transitionPhase, anchor: .center)
                .opacity(transitionPhase * (1 - transitionPhase))
        }
    }

    private func phase(_ value: Double, _ start: Double, _ end: Double) -> Double {
        min(max((value - start) / (end - start), 0), 1)
    }
}

private struct BrandLogoView: View {
    let brandPack: BrandPack

    var body: some View {
        if let url = brandPack.logoResource {
            LocalSVGView(url: url)
                .clipShape(Circle())
        } else {
            ZStack {
                Circle().fill(SVCTheme.surface)
                Circle().stroke(SVCTheme.primaryText.opacity(0.72), lineWidth: 2)
                Text("SVC")
                    .font(.system(size: 26, weight: .bold, design: .rounded))
                    .tracking(1.5)
                    .foregroundStyle(SVCTheme.primaryText)
            }
        }
    }
}

private struct LocalSVGView: UIViewRepresentable {
    let url: URL

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.suppressesIncrementalRendering = false
        let view = WKWebView(frame: .zero, configuration: configuration)
        view.isOpaque = false
        view.backgroundColor = .clear
        view.scrollView.backgroundColor = .clear
        view.scrollView.isScrollEnabled = false
        view.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
        return view
    }

    func updateUIView(_ view: WKWebView, context: Context) {}
}
