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

struct BrandAssets: Codable, Equatable {
    let logo: String
    let wordmark: String?
}

struct BrandPackDefinition: Codable, Equatable, Identifiable {
    let schemaVersion: Int
    let id: String
    let displayName: String
    let theme: String
    let manufacturer: String
    let model: String
    let generation: String
    let year: Int
    let manufacturerWordmark: String
    let vehicleModel: String
    let vehicleGeneration: String
    let brandTagline: String
    let accentColor: String
    let assets: BrandAssets
}

private struct BrandCatalogEntry: Codable {
    let id: String
    let configuration: String
}

private struct BrandCatalogDocument: Codable {
    let schemaVersion: Int
    let defaultProfileId: String
    let fallbackProfileId: String
    let profiles: [BrandCatalogEntry]
}

struct BrandPack: Equatable {
    let definition: BrandPackDefinition
    let logoResource: URL?
    let wordmarkResource: URL?
    let requestedProfileId: String

    var id: String { definition.id }
    var theme: String { definition.theme }
    var manufacturer: String { definition.manufacturer }
    var model: String { definition.model }
    var generation: String { definition.generation }
    var year: Int { definition.year }
    var manufacturerWordmark: String { definition.manufacturerWordmark }
    var vehicleModel: String { definition.vehicleModel }
    var vehicleGeneration: String { definition.vehicleGeneration }
    var brandTagline: String { definition.brandTagline }
    var accentColor: Color { Color(svcHex: definition.accentColor) }
    var usesFallback: Bool { requestedProfileId != id }
}

struct BrandCatalog {
    let defaultProfileId: String
    let fallbackProfileId: String
    let profiles: [BrandPackDefinition]

    private let definitions: [String: BrandPackDefinition]
    private let resourceURL: (String) -> URL?

    init(
        defaultProfileId: String,
        fallbackProfileId: String,
        profiles: [BrandPackDefinition],
        resourceURL: @escaping (String) -> URL?
    ) {
        self.defaultProfileId = defaultProfileId
        self.fallbackProfileId = fallbackProfileId
        self.profiles = profiles
        definitions = Dictionary(uniqueKeysWithValues: profiles.map { ($0.id, $0) })
        self.resourceURL = resourceURL
    }

    static func load(bundle: Bundle = .main) -> BrandCatalog {
        do {
            let indexData = try resourceData(
                named: "brand-pack-index-v1.json",
                bundle: bundle
            )
            let decoder = JSONDecoder()
            let document = try decoder.decode(
                BrandCatalogDocument.self,
                from: indexData
            )
            guard document.schemaVersion == 1 else {
                throw BrandCatalogError.unsupportedSchema
            }
            let profiles = try document.profiles.map { entry in
                let data = try resourceData(
                    named: entry.configuration,
                    bundle: bundle
                )
                let definition = try decoder.decode(
                    BrandPackDefinition.self,
                    from: data
                )
                guard definition.schemaVersion == 1, definition.id == entry.id else {
                    throw BrandCatalogError.identityMismatch
                }
                return definition
            }
            guard
                Set(profiles.map(\.id)).count == profiles.count,
                profiles.contains(where: { $0.id == document.defaultProfileId }),
                profiles.contains(where: { $0.id == document.fallbackProfileId })
            else {
                throw BrandCatalogError.missingRequiredProfile
            }
            return BrandCatalog(
                defaultProfileId: document.defaultProfileId,
                fallbackProfileId: document.fallbackProfileId,
                profiles: profiles,
                resourceURL: { assetURL(path: $0, bundle: bundle) }
            )
        } catch {
            return .emergency
        }
    }

    func resolve(profileId: String) -> BrandPack {
        let fallback = definitions[fallbackProfileId] ?? Self.emergencyDefinition
        let requested = definitions[profileId] ?? fallback
        let selected = resourceURL(requested.assets.logo) == nil
            ? fallback
            : requested
        return BrandPack(
            definition: selected,
            logoResource: resourceURL(selected.assets.logo),
            wordmarkResource: selected.assets.wordmark.flatMap(resourceURL),
            requestedProfileId: profileId
        )
    }

    private static func resourceData(
        named fileName: String,
        bundle: Bundle
    ) throws -> Data {
        let path = fileName as NSString
        let name = path.deletingPathExtension
        let fileExtension = path.pathExtension
        guard let url = bundle.url(
            forResource: name,
            withExtension: fileExtension.isEmpty ? nil : fileExtension
        ) else {
            throw BrandCatalogError.missingResource
        }
        return try Data(contentsOf: url)
    }

    private static func assetURL(path: String, bundle: Bundle) -> URL? {
        guard let resourceURL = bundle.resourceURL else { return nil }
        let candidate = resourceURL.appendingPathComponent(path)
        return FileManager.default.fileExists(atPath: candidate.path)
            ? candidate
            : nil
    }

    private static let emergencyDefinition = BrandPackDefinition(
        schemaVersion: 1,
        id: "emergency-svc",
        displayName: "SVC",
        theme: "svc-dark",
        manufacturer: "SVC",
        model: "Mobile",
        generation: "Fallback",
        year: 0,
        manufacturerWordmark: "SVC",
        vehicleModel: "SVC",
        vehicleGeneration: "",
        brandTagline: "",
        accentColor: "#1C69D4",
        assets: BrandAssets(logo: "", wordmark: nil)
    )

    private static let emergency = BrandCatalog(
        defaultProfileId: emergencyDefinition.id,
        fallbackProfileId: emergencyDefinition.id,
        profiles: [emergencyDefinition],
        resourceURL: { _ in nil }
    )
}

private enum BrandCatalogError: Error {
    case unsupportedSchema
    case identityMismatch
    case missingRequiredProfile
    case missingResource
}

struct StartupTimeline: Codable, Equatable {
    struct Phases: Codable, Equatable {
        let screenOnEndMs: Int
        let logoEndMs: Int
        let identityEndMs: Int
        let taglineEndMs: Int
        let dashboardEndMs: Int
    }

    let schemaVersion: Int
    let durationMs: Int
    let criticalDurationMs: Int
    let phases: Phases

    static func load(bundle: Bundle = .main) -> StartupTimeline {
        guard
            let url = bundle.url(
                forResource: "startup-animation-v1",
                withExtension: "json"
            ),
            let data = try? Data(contentsOf: url),
            let timeline = try? JSONDecoder().decode(StartupTimeline.self, from: data),
            timeline.schemaVersion == 1,
            timeline.phases.dashboardEndMs == timeline.durationMs
        else {
            return .emergency
        }
        return timeline
    }

    func durationSeconds(
        animationEnabled: Bool,
        reduceMotion: Bool,
        critical: Bool
    ) -> TimeInterval {
        guard animationEnabled else { return 0 }
        let milliseconds = reduceMotion || critical
            ? criticalDurationMs
            : durationMs
        return TimeInterval(milliseconds) / 1_000
    }

    func progress(milliseconds: Int) -> Double {
        Double(milliseconds) / Double(durationMs)
    }

    private static let emergency = StartupTimeline(
        schemaVersion: 1,
        durationMs: 300,
        criticalDurationMs: 300,
        phases: Phases(
            screenOnEndMs: 50,
            logoEndMs: 100,
            identityEndMs: 160,
            taglineEndMs: 220,
            dashboardEndMs: 300
        )
    )
}

enum SVCTheme {
    static let background = Color(red: 5 / 255, green: 5 / 255, blue: 5 / 255)
    static let surface = Color(red: 17 / 255, green: 18 / 255, blue: 20 / 255)
    static let primaryText = Color(red: 244 / 255, green: 244 / 255, blue: 244 / 255)
    static let secondaryText = Color(red: 167 / 255, green: 169 / 255, blue: 172 / 255)
    static let accentBlue = Color(red: 28 / 255, green: 105 / 255, blue: 212 / 255)
    static let lightBlue = Color(red: 74 / 255, green: 163 / 255, blue: 1)
    static let divider = Color(red: 48 / 255, green: 50 / 255, blue: 54 / 255)
    static let warning = Color(red: 1, green: 176 / 255, blue: 0)
    static let critical = Color(red: 227 / 255, green: 38 / 255, blue: 54 / 255)
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

    let startupTimeline: StartupTimeline

    private let defaults: UserDefaults
    private let catalog: BrandCatalog

    init(
        defaults: UserDefaults = .standard,
        bundle: Bundle = .main
    ) {
        self.defaults = defaults
        catalog = BrandCatalog.load(bundle: bundle)
        startupTimeline = StartupTimeline.load(bundle: bundle)
        let storedProfile = defaults.string(forKey: Keys.profile)
        if
            let storedProfile,
            catalog.profiles.contains(where: { $0.id == storedProfile })
        {
            profileId = storedProfile
        } else {
            profileId = storedProfile == nil
                ? catalog.defaultProfileId
                : catalog.fallbackProfileId
        }
        animationEnabled = defaults.object(forKey: Keys.animationEnabled) as? Bool
            ?? true
        forceReduceMotion = defaults.bool(forKey: Keys.reduceMotion)
    }

    var availableProfiles: [BrandPackDefinition] { catalog.profiles }
    var brandPack: BrandPack { catalog.resolve(profileId: profileId) }

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

private extension Color {
    init(svcHex: String) {
        let value = UInt64(svcHex.dropFirst(), radix: 16) ?? 0x1C69D4
        self.init(
            red: Double((value >> 16) & 0xff) / 255,
            green: Double((value >> 8) & 0xff) / 255,
            blue: Double(value & 0xff) / 255
        )
    }
}
