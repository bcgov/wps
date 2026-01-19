// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "Keycloak",
    platforms: [.iOS(.v14)],
    products: [
        .library(
            name: "Keycloak",
            targets: ["KeycloakPlugin"])
    ],
    dependencies: [
        .package(url: "https://github.com/ionic-team/capacitor-swift-pm.git", from: "7.4.5"),
        .package(url: "https://github.com/openid/AppAuth-iOS.git", from: "2.0.0"),
    ],
    targets: [
        .target(
            name: "KeycloakPlugin",
            dependencies: [
                .product(name: "Capacitor", package: "capacitor-swift-pm"),
                .product(name: "Cordova", package: "capacitor-swift-pm"),
                .product(name: "AppAuth", package: "AppAuth-iOS"),
            ],
            path: "ios/Sources/KeycloakPlugin"),
        .testTarget(
            name: "KeycloakPluginTests",
            dependencies: ["KeycloakPlugin"],
            path: "ios/Tests/KeycloakPluginTests"),
    ]
)
