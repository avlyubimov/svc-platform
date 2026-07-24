import Combine
import Foundation

struct VehiclePerformanceProfile: Codable, Equatable, Identifiable {
    let schemaVersion: Int
    let id: String
    let manufacturer: String
    let model: String
    let generation: String?
    let yearFrom: Int?
    let yearTo: Int?
    let engineName: String?
    let engineDisplacementCc: Double?
    let maximumTorqueNm: Double?
    let nominalPowerKw: Double?
    let gearboxGears: Int?
    let fuelCapacityLiters: Double?
    let fuelReserveLiters: Double?
    let iceWarningTemperatureCelsius: Double?
    let idleRpm: Int?
    let idleToleranceRpm: Int?
    let torquePeakRpm: Int?
    let powerPeakRpm: Int?
    let tachometerScaleMinRpm: Int
    let tachometerScaleMaxRpm: Int?
    let warningStartRpm: Int?
    let redZoneStartRpm: Int?
    let revLimiterRpm: Int?
    let source: String
    let reference: String
    let confidence: String

    var displayName: String {
        [manufacturer, model, generation]
            .compactMap { $0 }
            .joined(separator: " ")
    }
}

private struct VehiclePerformanceCatalogEntry: Codable {
    let id: String
    let configuration: String
}

private struct VehiclePerformanceCatalogDocument: Codable {
    let schemaVersion: Int
    let defaultProfileId: String
    let fallbackProfileId: String
    let profiles: [VehiclePerformanceCatalogEntry]
}

struct VehiclePerformanceCatalog {
    let defaultProfileId: String
    let fallbackProfileId: String
    let profiles: [VehiclePerformanceProfile]

    private let definitions: [String: VehiclePerformanceProfile]

    init(
        defaultProfileId: String,
        fallbackProfileId: String,
        profiles: [VehiclePerformanceProfile]
    ) {
        self.defaultProfileId = defaultProfileId
        self.fallbackProfileId = fallbackProfileId
        self.profiles = profiles
        definitions = Dictionary(uniqueKeysWithValues: profiles.map { ($0.id, $0) })
    }

    static func load(bundle: Bundle = .main) -> VehiclePerformanceCatalog {
        do {
            let decoder = JSONDecoder()
            let indexData = try resourceData(
                named: "vehicle-profile-index-v1.json",
                bundle: bundle
            )
            let document = try decoder.decode(
                VehiclePerformanceCatalogDocument.self,
                from: indexData
            )
            guard document.schemaVersion == 1 else {
                return .emergency
            }
            let profiles = try document.profiles.map { entry in
                let data = try resourceData(named: entry.configuration, bundle: bundle)
                let profile = try decoder.decode(
                    VehiclePerformanceProfile.self,
                    from: data
                )
                guard profile.schemaVersion == 1, profile.id == entry.id else {
                    throw VehiclePerformanceCatalogError.identityMismatch
                }
                return profile
            }
            guard
                Set(profiles.map(\.id)).count == profiles.count,
                profiles.contains(where: { $0.id == document.defaultProfileId }),
                profiles.contains(where: { $0.id == document.fallbackProfileId })
            else {
                return .emergency
            }
            return VehiclePerformanceCatalog(
                defaultProfileId: document.defaultProfileId,
                fallbackProfileId: document.fallbackProfileId,
                profiles: profiles
            )
        } catch {
            return .emergency
        }
    }

    func resolve(profileId: String) -> VehiclePerformanceProfile {
        definitions[profileId]
            ?? definitions[fallbackProfileId]
            ?? Self.emergencyProfile
    }

    private static func resourceData(
        named fileName: String,
        bundle: Bundle
    ) throws -> Data {
        guard
            let resourceURL = bundle.resourceURL,
            FileManager.default.fileExists(
                atPath: resourceURL.appendingPathComponent(fileName).path
            )
        else {
            throw VehiclePerformanceCatalogError.missingResource
        }
        return try Data(contentsOf: resourceURL.appendingPathComponent(fileName))
    }

    private static let emergencyProfile = VehiclePerformanceProfile(
        schemaVersion: 1,
        id: "emergency-generic-motorcycle",
        manufacturer: "Generic",
        model: "Motorcycle",
        generation: nil,
        yearFrom: nil,
        yearTo: nil,
        engineName: nil,
        engineDisplacementCc: nil,
        maximumTorqueNm: nil,
        nominalPowerKw: nil,
        gearboxGears: nil,
        fuelCapacityLiters: nil,
        fuelReserveLiters: nil,
        iceWarningTemperatureCelsius: nil,
        idleRpm: nil,
        idleToleranceRpm: nil,
        torquePeakRpm: nil,
        powerPeakRpm: nil,
        tachometerScaleMinRpm: 0,
        tachometerScaleMaxRpm: nil,
        warningStartRpm: nil,
        redZoneStartRpm: nil,
        revLimiterRpm: nil,
        source: "Emergency no-assumption fallback",
        reference: "docs/reference-vehicle/bmw-k25-2007/dashboard-profile.md",
        confidence: "unknown"
    )

    private static let emergency = VehiclePerformanceCatalog(
        defaultProfileId: emergencyProfile.id,
        fallbackProfileId: emergencyProfile.id,
        profiles: [emergencyProfile]
    )
}

private enum VehiclePerformanceCatalogError: Error {
    case identityMismatch
    case missingResource
}

final class RidePreferences: ObservableObject {
    @Published var vehicleProfileId: String {
        didSet { defaults.set(vehicleProfileId, forKey: Keys.vehicleProfile) }
    }
    @Published var themeMode: RideThemeMode {
        didSet { defaults.set(themeMode.rawValue, forKey: Keys.themeMode) }
    }
    @Published var nightEnterLux: Double {
        didSet { defaults.set(nightEnterLux, forKey: Keys.nightEnterLux) }
    }
    @Published var dayEnterLux: Double {
        didSet { defaults.set(dayEnterLux, forKey: Keys.dayEnterLux) }
    }
    @Published var pageIndicatorEnabled: Bool {
        didSet { defaults.set(pageIndicatorEnabled, forKey: Keys.pageIndicatorEnabled) }
    }
    @Published var lastRidePage: Int {
        didSet {
            defaults.set(
                min(max(lastRidePage, 0), RideModePage.allCases.count - 1),
                forKey: Keys.lastRidePage
            )
        }
    }

    private let defaults: UserDefaults
    private let catalog: VehiclePerformanceCatalog

    init(
        defaults: UserDefaults = .standard,
        bundle: Bundle = .main
    ) {
        self.defaults = defaults
        catalog = VehiclePerformanceCatalog.load(bundle: bundle)
        let storedProfile = defaults.string(forKey: Keys.vehicleProfile)
        if
            let storedProfile,
            catalog.profiles.contains(where: { $0.id == storedProfile })
        {
            vehicleProfileId = storedProfile
        } else {
            vehicleProfileId = storedProfile == nil
                ? catalog.defaultProfileId
                : catalog.fallbackProfileId
        }
        themeMode = defaults.string(forKey: Keys.themeMode)
            .flatMap(RideThemeMode.init(rawValue:))
            ?? .automatic
        let storedNight = defaults.object(forKey: Keys.nightEnterLux) as? Double
        let storedDay = defaults.object(forKey: Keys.dayEnterLux) as? Double
        nightEnterLux = storedNight ?? RideThemeThresholds.default.nightEnterLux
        dayEnterLux = storedDay ?? RideThemeThresholds.default.dayEnterLux
        pageIndicatorEnabled = defaults.object(
            forKey: Keys.pageIndicatorEnabled
        ) as? Bool ?? true
        lastRidePage = min(
            max(defaults.integer(forKey: Keys.lastRidePage), 0),
            RideModePage.allCases.count - 1
        )
    }

    var availableProfiles: [VehiclePerformanceProfile] { catalog.profiles }
    var vehicleProfile: VehiclePerformanceProfile {
        catalog.resolve(profileId: vehicleProfileId)
    }

    var themeThresholds: RideThemeThresholds {
        RideThemeThresholds(
            nightEnterLux: min(nightEnterLux, dayEnterLux - 50),
            dayEnterLux: max(dayEnterLux, nightEnterLux + 50)
        )
    }

    private enum Keys {
        static let vehicleProfile = "rideVehiclePerformanceProfile"
        static let themeMode = "rideThemeMode"
        static let nightEnterLux = "rideNightEnterLux"
        static let dayEnterLux = "rideDayEnterLux"
        static let pageIndicatorEnabled = "ridePageIndicatorEnabled"
        static let lastRidePage = "rideLastPage"
    }
}
