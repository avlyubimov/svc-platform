import Foundation

enum OTAPolicy {
    static func denialReasons(for telemetry: TelemetrySnapshot) -> [String] {
        var reasons: [String] = []
        if !telemetry.vehicle.speed.isUsable || telemetry.vehicle.speed.value != 0 {
            reasons.append("vehicle_moving")
        }
        if !telemetry.vehicle.engineRpm.isUsable || telemetry.vehicle.engineRpm.value != 0 {
            reasons.append("engine_running")
        }
        if telemetry.channels.contains(where: { $0.state.value != "off" }) {
            reasons.append("outputs_active")
        }
        if telemetry.warnings.contains(where: { $0.active && $0.severity == "critical" }) {
            reasons.append("critical_fault")
        }
        if !telemetry.batteryVoltage.isUsable ||
            telemetry.batteryVoltage.value.map({ (11.8...14.8).contains($0) }) != true {
            reasons.append("battery_out_of_range")
        }
        if telemetry.powerZoneTemperatures.contains(
            where: { !$0.valid || $0.stale || ($0.value ?? .infinity) > 85 }
        ) {
            reasons.append("temperature_out_of_range")
        }
        return reasons
    }
}
