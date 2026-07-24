import Foundation

enum RideDataState: String, Equatable {
    case valid
    case stale
    case degraded
    case invalid
    case unavailable
}

struct RideValue<Value: Equatable>: Equatable {
    let value: Value?
    let unit: String
    let state: RideDataState

    var displayValue: Value? {
        switch state {
        case .valid, .degraded:
            value
        case .stale, .invalid, .unavailable:
            nil
        }
    }
}

extension Measurement where Value: Equatable {
    var rideValue: RideValue<Value> {
        let state: RideDataState
        if stale {
            state = .stale
        } else if !valid || value == nil {
            state = quality == .invalid ? .invalid : .unavailable
        } else {
            switch quality {
            case .good:
                state = .valid
            case .degraded:
                state = .degraded
            case .invalid:
                state = .invalid
            case .unavailable:
                state = .unavailable
            }
        }
        return RideValue(value: value, unit: unit, state: state)
    }
}

enum RideGear: String, CaseIterable, Equatable {
    case neutral = "N"
    case first = "1"
    case second = "2"
    case third = "3"
    case fourth = "4"
    case fifth = "5"
    case sixth = "6"
    case between = "BETWEEN"
    case unavailable

    var displayValue: String {
        switch self {
        case .unavailable:
            "—"
        default:
            rawValue
        }
    }
}

enum TachometerZone: String, Equatable {
    case normal
    case warning
    case red
    case unavailable
}

enum TachometerZoneResolver {
    static func zone(
        rpm: Double?,
        profile: VehiclePerformanceProfile
    ) -> TachometerZone {
        guard
            let rpm,
            profile.tachometerScaleMaxRpm != nil
        else {
            return .unavailable
        }
        if let red = profile.redZoneStartRpm, rpm >= Double(red) {
            return .red
        }
        if let warning = profile.warningStartRpm, rpm >= Double(warning) {
            return .warning
        }
        return .normal
    }

    static func zoneWithHysteresis(
        rpm: Double?,
        profile: VehiclePerformanceProfile,
        previous: TachometerZone,
        hysteresisRpm: Double = 80
    ) -> TachometerZone {
        guard let rpm else { return .unavailable }
        let raw = zone(rpm: rpm, profile: profile)
        switch previous {
        case .red:
            if
                let red = profile.redZoneStartRpm,
                rpm >= Double(red) - hysteresisRpm
            {
                return .red
            }
        case .warning:
            if
                let red = profile.redZoneStartRpm,
                rpm >= Double(red)
            {
                return .red
            }
            if
                let warning = profile.warningStartRpm,
                rpm >= Double(warning) - hysteresisRpm
            {
                return .warning
            }
        case .normal, .unavailable:
            break
        }
        return raw
    }
}

struct LeanExtrema: Equatable {
    private(set) var maximumLeftDegrees: Double = 0
    private(set) var maximumRightDegrees: Double = 0

    mutating func observe(_ leanDegrees: Double?) {
        guard let leanDegrees else { return }
        if leanDegrees < 0 {
            maximumLeftDegrees = max(maximumLeftDegrees, abs(leanDegrees))
        } else {
            maximumRightDegrees = max(maximumRightDegrees, leanDegrees)
        }
    }

    mutating func resetIfStationary(speed: RideValue<Double>) -> Bool {
        guard speed.displayValue == 0 else { return false }
        maximumLeftDegrees = 0
        maximumRightDegrees = 0
        return true
    }
}

struct MotorcycleMountingTransform: Codable, Equatable {
    let rollDegrees: Double
    let pitchDegrees: Double
    let yawDegrees: Double
    let zeroOffsetDegrees: Double
}

enum MotorcycleCalibrationPolicy {
    static func canCalibrate(
        speed: RideValue<Double>,
        demoMode: Bool
    ) -> Bool {
        demoMode && speed.displayValue == 0
    }
}

enum RideAlertSeverity: Int, Comparable {
    case info = 0
    case warning = 1
    case critical = 2

    static func < (lhs: RideAlertSeverity, rhs: RideAlertSeverity) -> Bool {
        lhs.rawValue < rhs.rawValue
    }
}

struct RideAlert: Equatable, Identifiable {
    let id: String
    let title: String
    let severity: RideAlertSeverity
}

struct RideDashboardState: Equatable {
    let speed: RideValue<Double>
    let engineRpm: RideValue<Double>
    let gear: RideGear
    let leanAngle: RideValue<Double>
    let engineTemperature: RideValue<Double>
    let fuelLevel: RideValue<Double>
    let ambientTemperature: RideValue<Double>
    let ambientLight: RideValue<Double>
    let batteryVoltage: RideValue<Double>
    let totalCurrent: RideValue<Double>
    let canState: RideValue<String>
    let bleLabel: String
    let bleState: RideDataState
    let tachometerZone: TachometerZone
    let alerts: [RideAlert]
    let profile: VehiclePerformanceProfile

    var activeAlert: RideAlert? {
        alerts.max {
            if $0.severity == $1.severity {
                return $0.id > $1.id
            }
            return $0.severity < $1.severity
        }
    }

    static func build(
        telemetry: TelemetrySnapshot,
        connectionState: ConnectionState,
        isConnecting: Bool,
        profile: VehiclePerformanceProfile,
        leanCalibrated: Bool = false
    ) -> RideDashboardState {
        let speed = telemetry.vehicle.speed.rideValue
        let rpm = telemetry.vehicle.engineRpm.rideValue
        let rawLean = telemetry.leanAngle.rideValue
        let lean = RideValue(
            value: rawLean.value,
            unit: rawLean.unit,
            state: rawLean.state == .valid && !leanCalibrated
                ? .degraded
                : rawLean.state
        )
        let ble: (String, RideDataState) = if isConnecting {
            ("CONNECTING", .degraded)
        } else {
            switch connectionState {
            case .connected:
                ("BLE", .valid)
            case .scanning:
                ("SCANNING", .degraded)
            case .disconnected:
                ("BLE LOST", .unavailable)
            }
        }
        let zone = TachometerZoneResolver.zone(
            rpm: rpm.displayValue,
            profile: profile
        )
        let alerts = buildAlerts(
            telemetry: telemetry,
            rpm: rpm,
            zone: zone,
            connectionState: connectionState,
            isConnecting: isConnecting,
            profile: profile
        )
        return RideDashboardState(
            speed: speed,
            engineRpm: rpm,
            gear: .unavailable,
            leanAngle: lean,
            engineTemperature: telemetry.vehicle.engineTemperature.rideValue,
            fuelLevel: telemetry.vehicle.fuelLevel.rideValue,
            ambientTemperature: telemetry.vehicle.ambientTemperature.rideValue,
            ambientLight: telemetry.ambientLight.rideValue,
            batteryVoltage: telemetry.batteryVoltage.rideValue,
            totalCurrent: telemetry.totalCurrent.rideValue,
            canState: telemetry.can1.state.rideValue,
            bleLabel: ble.0,
            bleState: ble.1,
            tachometerZone: zone,
            alerts: alerts,
            profile: profile
        )
    }

    private static func buildAlerts(
        telemetry: TelemetrySnapshot,
        rpm: RideValue<Double>,
        zone: TachometerZone,
        connectionState: ConnectionState,
        isConnecting: Bool,
        profile: VehiclePerformanceProfile
    ) -> [RideAlert] {
        var alerts = telemetry.warnings
            .filter(\.active)
            .map {
                RideAlert(
                    id: $0.code,
                    title: $0.message,
                    severity: severity($0.severity)
                )
            }
        var codes = Set(alerts.map(\.id))

        if zone == .red, rpm.displayValue != nil {
            append(
                RideAlert(id: "high_rpm", title: "HIGH RPM", severity: .critical),
                to: &alerts,
                codes: &codes
            )
        }
        if
            let fuel = telemetry.vehicle.fuelLevel.rideValue.displayValue,
            let capacity = profile.fuelCapacityLiters,
            let reserve = profile.fuelReserveLiters,
            capacity > 0,
            fuel <= reserve / capacity * 100
        {
            append(
                RideAlert(
                    id: "fuel_reserve",
                    title: "FUEL RESERVE",
                    severity: .warning
                ),
                to: &alerts,
                codes: &codes
            )
        }
        if
            let ambient = telemetry.vehicle.ambientTemperature.rideValue.displayValue,
            let threshold = profile.iceWarningTemperatureCelsius,
            ambient < threshold
        {
            append(
                RideAlert(id: "ice_warning", title: "ICE WARNING", severity: .warning),
                to: &alerts,
                codes: &codes
            )
        }
        if connectionState == .disconnected, !isConnecting {
            append(
                RideAlert(id: "ble_lost", title: "SVC CONNECTION LOST", severity: .warning),
                to: &alerts,
                codes: &codes
            )
        }
        if telemetry.can1.state.rideValue.displayValue == nil {
            append(
                RideAlert(id: "can_unavailable", title: "CAN UNAVAILABLE", severity: .warning),
                to: &alerts,
                codes: &codes
            )
        }
        if telemetry.storage.sdCardState.rideValue.displayValue == "missing" {
            append(
                RideAlert(id: "sd_card_missing", title: "SD CARD MISSING", severity: .warning),
                to: &alerts,
                codes: &codes
            )
        }
        return alerts
    }

    private static func append(
        _ alert: RideAlert,
        to alerts: inout [RideAlert],
        codes: inout Set<String>
    ) {
        guard codes.insert(alert.id).inserted else { return }
        alerts.append(alert)
    }

    private static func severity(_ value: String) -> RideAlertSeverity {
        switch value.lowercased() {
        case "critical":
            .critical
        case "warning":
            .warning
        default:
            .info
        }
    }
}
