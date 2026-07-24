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
    let disabledText: Color
    let divider: Color
    let accent: Color
    let accentBright: Color
    let warning: Color
    let critical: Color
    let valid: Color
    let degraded: Color
    let highBeam: Color
    let fogLight: Color

    static func resolve(_ theme: RideResolvedTheme) -> RidePalette {
        switch theme {
        case .day:
            RidePalette(
                background: Color(red: 5 / 255, green: 6 / 255, blue: 7 / 255),
                surface: Color(red: 17 / 255, green: 20 / 255, blue: 24 / 255),
                raisedSurface: Color(red: 23 / 255, green: 29 / 255, blue: 36 / 255),
                primaryText: Color(red: 244 / 255, green: 246 / 255, blue: 248 / 255),
                secondaryText: Color(red: 174 / 255, green: 181 / 255, blue: 189 / 255),
                disabledText: Color(red: 98 / 255, green: 107 / 255, blue: 118 / 255),
                divider: Color(red: 52 / 255, green: 58 / 255, blue: 66 / 255),
                accent: Color(red: 226 / 255, green: 27 / 255, blue: 45 / 255),
                accentBright: Color(red: 226 / 255, green: 27 / 255, blue: 45 / 255),
                warning: Color(red: 1, green: 176 / 255, blue: 0),
                critical: Color(red: 1, green: 59 / 255, blue: 48 / 255),
                valid: Color(red: 53 / 255, green: 208 / 255, blue: 127 / 255),
                degraded: Color(red: 1, green: 176 / 255, blue: 0),
                highBeam: Color(red: 61 / 255, green: 165 / 255, blue: 1),
                fogLight: Color(red: 102 / 255, green: 214 / 255, blue: 232 / 255)
            )
        case .night:
            RidePalette(
                background: Color(red: 5 / 255, green: 6 / 255, blue: 7 / 255),
                surface: Color(red: 17 / 255, green: 20 / 255, blue: 24 / 255),
                raisedSurface: Color(red: 23 / 255, green: 29 / 255, blue: 36 / 255),
                primaryText: Color(red: 244 / 255, green: 246 / 255, blue: 248 / 255),
                secondaryText: Color(red: 174 / 255, green: 181 / 255, blue: 189 / 255),
                disabledText: Color(red: 98 / 255, green: 107 / 255, blue: 118 / 255),
                divider: Color(red: 52 / 255, green: 58 / 255, blue: 66 / 255),
                accent: Color(red: 226 / 255, green: 27 / 255, blue: 45 / 255),
                accentBright: Color(red: 226 / 255, green: 27 / 255, blue: 45 / 255),
                warning: Color(red: 1, green: 176 / 255, blue: 0),
                critical: Color(red: 1, green: 59 / 255, blue: 48 / 255),
                valid: Color(red: 53 / 255, green: 208 / 255, blue: 127 / 255),
                degraded: Color(red: 1, green: 176 / 255, blue: 0),
                highBeam: Color(red: 61 / 255, green: 165 / 255, blue: 1),
                fogLight: Color(red: 102 / 255, green: 214 / 255, blue: 232 / 255)
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
