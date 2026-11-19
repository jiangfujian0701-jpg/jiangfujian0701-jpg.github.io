plugins { id("com.android.application") }

android {
    namespace = "nyc.npsa.app"
    compileSdk = 34
    defaultConfig {
        applicationId = "nyc.npsa.app"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }
    signingConfigs {
        create("fixed") {
            storeFile = file("keystore.jks")
            storePassword = "npsa-keystore-2026"
            keyAlias = "npsa"
            keyPassword = "npsa-keystore-2026"
        }
    }
    buildTypes {
        getByName("debug") { signingConfig = signingConfigs.getByName("fixed") }
        getByName("release") {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("fixed")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
