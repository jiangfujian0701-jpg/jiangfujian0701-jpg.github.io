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
    buildTypes {
        getByName("release") { isMinifyEnabled = false }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
