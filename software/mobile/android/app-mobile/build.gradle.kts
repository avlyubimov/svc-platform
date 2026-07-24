plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("org.jetbrains.kotlin.plugin.serialization")
}

val generatedVehicleProfileAssets =
    layout.buildDirectory.dir("generated/vehicle-profile-assets")
val syncVehicleProfileAssets by tasks.registering(Sync::class) {
    from("../../vehicle-profiles") {
        include("*.json")
    }
    into(generatedVehicleProfileAssets.map { it.dir("vehicle-profiles") })
}

android {
    namespace = "com.avlyubimov.svc.mobile"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.avlyubimov.svc.mobile"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildFeatures {
        compose = true
    }

    sourceSets {
        getByName("main").assets.srcDirs(
            "../../branding",
            generatedVehicleProfileAssets,
        )
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_21
        targetCompatibility = JavaVersion.VERSION_21
    }

    packaging {
        resources.excludes += "/META-INF/{AL2.0,LGPL2.1}"
    }
}

tasks.named("preBuild").configure {
    dependsOn(syncVehicleProfileAssets)
}

dependencies {
    implementation(project(":app-automotive"))
    implementation(project(":core-model"))
    implementation(project(":core-protocol"))
    implementation(project(":core-ble"))
    implementation(project(":core-update"))
    implementation(project(":core-mock"))
    implementation(platform("androidx.compose:compose-bom:2024.12.01"))
    implementation("androidx.activity:activity-compose:1.10.0")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.7")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3")
    testImplementation(kotlin("test"))
    androidTestImplementation(platform("androidx.compose:compose-bom:2024.12.01"))
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.7.0")
    androidTestImplementation("androidx.test.ext:junit:1.3.0")
    androidTestImplementation("androidx.test:runner:1.7.0")
    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
