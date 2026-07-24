pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "SVCMobile"
include(
    ":app-mobile",
    ":app-automotive",
    ":core-model",
    ":core-protocol",
    ":core-ble",
    ":core-update",
    ":core-mock",
)
