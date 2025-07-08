// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "KeycloakTestProject",
    platforms: [.iOS(.v14)],
    products: [
        .library(name: "KeycloakTestLib", targets: ["KeycloakTestLib"])
    ],
    targets: [
        .target(
            name: "KeycloakTestLib",
            dependencies: [],
            path: "Sources/KeycloakTestLib"
        ),
        .testTarget(
            name: "KeycloakTestLibTests",
            dependencies: ["KeycloakTestLib"],
            path: "Tests/KeycloakTestLibTests"
        )
    ]
)
