import Foundation
import SwiftUI

enum PrimaryScreen: String, CaseIterable, Identifiable {
    case dashboard
    case channels
    case canTelemetry
    case navigation
    case diagnostics

    var id: String { rawValue }

    var title: String {
        switch self {
        case .dashboard: "Dashboard"
        case .channels: "Channels"
        case .canTelemetry: "CAN telemetry"
        case .navigation: "Navigation status"
        case .diagnostics: "Diagnostics"
        }
    }
}

struct BrandPack: Equatable {
    let id: String
    let theme: String
    let manufacturer: String
    let model: String
    let generation: String
    let year: Int
    let logoResource: URL?
    let wordmarkResource: URL?
    let manufacturerWordmark: String
    let vehicleModel: String
    let vehicleGeneration: String
    let brandTagline: String
    let accentColor: Color

    static func resolved(
        profileId: String,
        bundle: Bundle = .main
    ) -> BrandPack {
        guard profileId == "bmw-r1200gs-k25-personal" else {
            return .generic
        }
        let logo = localAsset("bmw-roundel", bundle: bundle)
        let wordmark = localAsset("bmw-motorrad-wordmark", bundle: bundle)
        guard let logo, wordmark != nil else { return .generic }
        return BrandPack(
            id: "bmw-r1200gs-k25-personal",
            theme: "svc-boxer-blue",
            manufacturer: "BMW",
            model: "R1200GS",
            generation: "K25",
            year: 2007,
            logoResource: logo,
            wordmarkResource: wordmark,
            manufacturerWordmark: "BMW MOTORRAD",
            vehicleModel: "R 1200 GS",
            vehicleGeneration: "K25 · 2007",
            brandTagline: "MAKE LIFE A RIDE",
            accentColor: SVCTheme.bmwBlue
        )
    }

    static let generic = BrandPack(
        id: "generic-automotive",
        theme: "svc-boxer-blue",
        manufacturer: "SVC",
        model: "Smart Vehicle Controller",
        generation: "Generic Automotive",
        year: 2026,
        logoResource: nil,
        wordmarkResource: nil,
        manufacturerWordmark: "SMART VEHICLE CONTROLLER",
        vehicleModel: "SVC",
        vehicleGeneration: "GENERIC AUTOMOTIVE",
        brandTagline: "ENGINEERED FOR THE RIDE",
        accentColor: SVCTheme.bmwBlue
    )

    private static func localAsset(
        _ name: String,
        bundle: Bundle
    ) -> URL? {
        bundle.url(forResource: name, withExtension: "svg", subdirectory: "local")
            ?? bundle.url(forResource: name, withExtension: "svg")
    }
}

enum SVCTheme {
    static let background = Color(red: 5 / 255, green: 5 / 255, blue: 5 / 255)
    static let surface = Color(red: 17 / 255, green: 18 / 255, blue: 20 / 255)
    static let primaryText = Color(red: 244 / 255, green: 244 / 255, blue: 244 / 255)
    static let secondaryText = Color(red: 167 / 255, green: 169 / 255, blue: 172 / 255)
    static let bmwBlue = Color(red: 28 / 255, green: 105 / 255, blue: 212 / 255)
    static let lightBlue = Color(red: 74 / 255, green: 163 / 255, blue: 1)
    static let divider = Color(red: 48 / 255, green: 50 / 255, blue: 54 / 255)
    static let warning = Color(red: 1, green: 176 / 255, blue: 0)
    static let critical = Color(red: 227 / 255, green: 38 / 255, blue: 54 / 255)
}

enum StartupTiming {
    static func durationSeconds(
        animationEnabled: Bool,
        reduceMotion: Bool,
        critical: Bool
    ) -> TimeInterval {
        guard animationEnabled else { return 0 }
        return reduceMotion || critical ? 0.5 : 2.1
    }
}

final class AppearanceStore: ObservableObject {
    @Published var profileId: String {
        didSet { defaults.set(profileId, forKey: Keys.profile) }
    }
    @Published var animationEnabled: Bool {
        didSet { defaults.set(animationEnabled, forKey: Keys.animationEnabled) }
    }
    @Published var forceReduceMotion: Bool {
        didSet { defaults.set(forceReduceMotion, forKey: Keys.reduceMotion) }
    }

    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        profileId = defaults.string(forKey: Keys.profile)
            ?? "bmw-r1200gs-k25-personal"
        animationEnabled = defaults.object(forKey: Keys.animationEnabled) as? Bool
            ?? true
        forceReduceMotion = defaults.bool(forKey: Keys.reduceMotion)
    }

    var brandPack: BrandPack { BrandPack.resolved(profileId: profileId) }

    func restoredScreen() -> PrimaryScreen {
        guard
            let rawValue = defaults.string(forKey: Keys.lastScreen),
            let screen = PrimaryScreen(rawValue: rawValue)
        else {
            return .dashboard
        }
        return screen
    }

    func select(_ screen: PrimaryScreen) {
        defaults.set(screen.rawValue, forKey: Keys.lastScreen)
    }

    private enum Keys {
        static let profile = "vehicleProfile"
        static let animationEnabled = "startupAnimationEnabled"
        static let reduceMotion = "startupReduceMotionOverride"
        static let lastScreen = "lastSelectedScreen"
    }
}
