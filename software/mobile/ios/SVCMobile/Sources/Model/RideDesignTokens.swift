import SwiftUI

enum RideThemeMode: String, CaseIterable, Identifiable {
    case day
    case night
    case automatic

    var id: String { rawValue }

    var title: String {
        switch self {
        case .day: "SVC Day"
        case .night: "SVC Night"
        case .automatic: "Automatic"
        }
    }
}

enum RideResolvedTheme: Equatable {
    case day
    case night
}

struct RideThemeThresholds: Equatable {
    let nightEnterLux: Double
    let dayEnterLux: Double

    static let `default` = RideThemeThresholds(
        nightEnterLux: 250,
        dayEnterLux: 650
    )
}

enum RideThemeResolver {
    static func resolve(
        mode: RideThemeMode,
        ambientLight: RideValue<Double>,
        previous: RideResolvedTheme
    ) -> RideResolvedTheme {
        resolve(
            mode: mode,
            ambientLight: ambientLight,
            previous: previous,
            thresholds: .default
        )
    }

    static func resolve(
        mode: RideThemeMode,
        ambientLight: RideValue<Double>,
        previous: RideResolvedTheme,
        thresholds: RideThemeThresholds
    ) -> RideResolvedTheme {
        switch mode {
        case .day:
            return .day
        case .night:
            return .night
        case .automatic:
            guard let lux = ambientLight.displayValue else {
                return previous
            }
            switch previous {
            case .day:
                return lux <= thresholds.nightEnterLux ? .night : .day
            case .night:
                return lux >= thresholds.dayEnterLux ? .day : .night
            }
        }
    }
}

struct RidePalette {
    let background: Color
    let surface: Color
    let raisedSurface: Color
    let primaryText: Color
    let secondaryText: Color
    let divider: Color
    let accent: Color
    let accentBright: Color
    let warning: Color
    let critical: Color
    let valid: Color
    let degraded: Color

    static func resolve(_ theme: RideResolvedTheme) -> RidePalette {
        switch theme {
        case .day:
            RidePalette(
                background: Color(red: 11 / 255, green: 17 / 255, blue: 24 / 255),
                surface: Color(red: 20 / 255, green: 29 / 255, blue: 39 / 255),
                raisedSurface: Color(red: 28 / 255, green: 39 / 255, blue: 51 / 255),
                primaryText: .white,
                secondaryText: Color(red: 190 / 255, green: 201 / 255, blue: 212 / 255),
                divider: Color(red: 64 / 255, green: 78 / 255, blue: 92 / 255),
                accent: Color(red: 28 / 255, green: 105 / 255, blue: 212 / 255),
                accentBright: Color(red: 74 / 255, green: 163 / 255, blue: 1),
                warning: Color(red: 1, green: 176 / 255, blue: 0),
                critical: Color(red: 227 / 255, green: 38 / 255, blue: 54 / 255),
                valid: Color(red: 91 / 255, green: 214 / 255, blue: 144 / 255),
                degraded: Color(red: 1, green: 176 / 255, blue: 0)
            )
        case .night:
            RidePalette(
                background: Color(red: 3 / 255, green: 5 / 255, blue: 8 / 255),
                surface: Color(red: 10 / 255, green: 14 / 255, blue: 19 / 255),
                raisedSurface: Color(red: 17 / 255, green: 23 / 255, blue: 30 / 255),
                primaryText: Color(red: 244 / 255, green: 247 / 255, blue: 250 / 255),
                secondaryText: Color(red: 151 / 255, green: 165 / 255, blue: 179 / 255),
                divider: Color(red: 40 / 255, green: 50 / 255, blue: 61 / 255),
                accent: Color(red: 20 / 255, green: 84 / 255, blue: 177 / 255),
                accentBright: Color(red: 57 / 255, green: 139 / 255, blue: 232 / 255),
                warning: Color(red: 1, green: 176 / 255, blue: 0),
                critical: Color(red: 227 / 255, green: 38 / 255, blue: 54 / 255),
                valid: Color(red: 74 / 255, green: 194 / 255, blue: 126 / 255),
                degraded: Color(red: 1, green: 176 / 255, blue: 0)
            )
        }
    }
}

enum RideDesignTokens {
    static let cornerRadius: CGFloat = 18
    static let compactCornerRadius: CGFloat = 12
    static let spacing: CGFloat = 14
    static let compactSpacing: CGFloat = 8
    static let contentPadding: CGFloat = 18
    static let statusHeight: CGFloat = 34
    static let gaugeLineWidth: CGFloat = 16
    static let metricMinimumWidth: CGFloat = 128
    static let standardAnimation = 0.18
    static let themeAnimation = 0.3
}

enum RideMotionPolicy {
    static func duration(
        reduceMotion: Bool,
        standardDuration: Double = RideDesignTokens.standardAnimation
    ) -> Double {
        reduceMotion ? 0 : standardDuration
    }
}
