import Foundation

enum TFTIndicator: String, CaseIterable, Identifiable {
    case turnLeft
    case turnRight
    case highBeam
    case fogLights
    case neutral
    case abs
    case engineWarning
    case tirePressure
    case lowVoltage
    case svcError

    var id: String { rawValue }

    var label: String {
        switch self {
        case .turnLeft: "←"
        case .turnRight: "→"
        case .highBeam: "HIGH"
        case .fogLights: "FOG"
        case .neutral: "N"
        case .abs: "ABS"
        case .engineWarning: "ENGINE"
        case .tirePressure: "RDC"
        case .lowVoltage: "V"
        case .svcError: "SVC"
        }
    }
}

struct TFTDashboardData: Equatable {
    private static let tftMaximumRpm = 9_000.0
    private static let tftWarningStartRpm = 7_000.0
    private static let tftRedStartRpm = 8_000.0

    let speedKmh: Double?
    let engineRpm: Double?
    let tachometerMaximumRpm: Double?
    let warningStartRpm: Double?
    let redStartRpm: Double?
    let gear: String
    let leanDegrees: Double?
    let leanDegraded: Bool
    let accelerationG: Double?
    let brakingG: Double?
    let fuelPercent: Double?
    let rangeKm: Double?
    let batteryVoltage: Double?
    let engineTemperatureCelsius: Double?
    let ambientTemperatureCelsius: Double?
    let frontPressureBar: Double?
    let rearPressureBar: Double?
    let currentTime: String
    let canRecording: Bool
    let bleConnected: Bool
    let canConnected: Bool
    let activeIndicators: [TFTIndicator]
    let criticalMessage: String?
    let toastMessage: String?

    static func resolve(
        dashboard: RideDashboardState,
        telemetry: TelemetrySnapshot,
        demoMode: Bool
    ) -> TFTDashboardData {
        if demoMode { return .demo }

        let activeWarnings = telemetry.warnings.filter(\.active)
        var indicators: [TFTIndicator] = []
        if dashboard.gear.displayValue == "N" {
            indicators.append(.neutral)
        }
        if (dashboard.batteryVoltage.displayValue ?? .greatestFiniteMagnitude) < 11.8 {
            indicators.append(.lowVoltage)
        }
        if activeWarnings.contains(where: { $0.code.localizedCaseInsensitiveContains("abs") }) {
            indicators.append(.abs)
        }
        if
            activeWarnings.contains(where: {
                $0.code.localizedCaseInsensitiveContains("tire")
                    || $0.code.localizedCaseInsensitiveContains("pressure")
            })
        {
            indicators.append(.tirePressure)
        }
        if
            activeWarnings.contains(where: {
                $0.code.localizedCaseInsensitiveContains("engine")
            })
        {
            indicators.append(.engineWarning)
        }
        if
            activeWarnings.contains(where: {
                $0.severity.caseInsensitiveCompare("critical") == .orderedSame
            })
                || telemetry.channels.contains(where: {
                    guard
                        $0.fault.isUsable,
                        let fault = $0.fault.value
                    else {
                        return false
                    }
                    return fault.caseInsensitiveCompare("none") != .orderedSame
                })
        {
            indicators.append(.svcError)
        }
        let loggerRecording = telemetry.storage.canLoggerState.isUsable
            && telemetry.storage.canLoggerState.value?
                .caseInsensitiveCompare("recording") == .orderedSame
        let longitudinalAcceleration = telemetry.accelerometer.x.isUsable
            ? telemetry.accelerometer.x.value
            : nil

        return TFTDashboardData(
            speedKmh: dashboard.speed.displayValue,
            engineRpm: dashboard.engineRpm.displayValue,
            tachometerMaximumRpm: tftMaximumRpm,
            warningStartRpm: tftWarningStartRpm,
            redStartRpm: tftRedStartRpm,
            gear: dashboard.gear.displayValue,
            leanDegrees: dashboard.leanAngle.displayValue,
            leanDegraded: dashboard.leanAngle.state == .degraded,
            accelerationG: longitudinalAcceleration.map { max($0, 0) },
            brakingG: longitudinalAcceleration.map { max(-$0, 0) },
            fuelPercent: dashboard.fuelLevel.displayValue,
            rangeKm: nil,
            batteryVoltage: dashboard.batteryVoltage.displayValue,
            engineTemperatureCelsius: dashboard.engineTemperature.displayValue,
            ambientTemperatureCelsius: dashboard.ambientTemperature.displayValue,
            frontPressureBar: nil,
            rearPressureBar: nil,
            currentTime: Date.now.formatted(date: .omitted, time: .shortened),
            canRecording: loggerRecording,
            bleConnected: dashboard.bleState == .valid,
            canConnected: dashboard.canState.displayValue != nil,
            activeIndicators: indicators,
            criticalMessage: activeWarnings.first(where: {
                $0.severity.caseInsensitiveCompare("critical") == .orderedSame
            })?.message,
            toastMessage: activeWarnings.first(where: {
                $0.code == "sd_card_missing"
            })?.message
        )
    }

    static let demo = TFTDashboardData(
        speedKmh: 87,
        engineRpm: 4_200,
        tachometerMaximumRpm: 9_000,
        warningStartRpm: 7_000,
        redStartRpm: 8_000,
        gear: "4",
        leanDegrees: 18,
        leanDegraded: false,
        accelerationG: 0.32,
        brakingG: 0.08,
        fuelPercent: 62,
        rangeKm: 214,
        batteryVoltage: 14.2,
        engineTemperatureCelsius: 92,
        ambientTemperatureCelsius: 16,
        frontPressureBar: 2.3,
        rearPressureBar: 2.6,
        currentTime: "10:42",
        canRecording: true,
        bleConnected: true,
        canConnected: true,
        activeIndicators: [.highBeam, .fogLights, .abs],
        criticalMessage: nil,
        toastMessage: nil
    )
}
