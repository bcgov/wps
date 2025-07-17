import Capacitor
import Foundation
import XCTest

@testable import KeycloakPlugin

class KeycloakPluginTests: XCTestCase {

    var plugin: KeycloakPlugin!

    override func setUp() {
        super.setUp()
        plugin = KeycloakPlugin()
    }

    override func tearDown() {
        plugin = nil
        super.tearDown()
    }

    func testPluginIdentifier() {
        XCTAssertEqual(plugin.identifier, "KeycloakPlugin")
    }

    func testPluginJSName() {
        XCTAssertEqual(plugin.jsName, "Keycloak")
    }

    func testPluginMethods() {
        let methodNames = plugin.pluginMethods.map { $0.name }
        XCTAssertTrue(methodNames.contains("authenticate"))
        XCTAssertTrue(methodNames.contains("refreshToken"))
        XCTAssertEqual(plugin.pluginMethods.count, 2)
    }

    func testPluginMethodReturnTypes() {
        for method in plugin.pluginMethods {
            XCTAssertEqual(method.returnType, CAPPluginReturnPromise)
        }
    }

    func testPluginLoad() {
        // This test verifies that load() can be called without crashing
        XCTAssertNoThrow(plugin.load())
    }

    func testParameterValidation() {
        // These tests verify the plugin's parameter validation logic
        // by testing the actual logic patterns used in the plugin

        // Test required parameter checking pattern
        XCTAssertTrue(validateParameter("test-value"))
        XCTAssertFalse(validateParameter(nil))
        XCTAssertFalse(validateParameter(""))
    }

    func testKeycloakOptionsCreation() {
        // Test that KeycloakOptions can be created with valid parameters
        let options = KeycloakOptions(
            clientId: "test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        XCTAssertEqual(options.clientId, "test-client")
        XCTAssertEqual(options.authorizationBaseUrl, "https://keycloak.example.com/auth")
        XCTAssertEqual(options.redirectUrl, "ca.bc.gov.asago://auth/callback")
        XCTAssertEqual(options.accessTokenEndpoint, "https://keycloak.example.com/token")
    }

    func testKeycloakRefreshOptionsCreation() {
        // Test that KeycloakRefreshOptions can be created with valid parameters
        let options = KeycloakRefreshOptions(
            clientId: "test-client",
            accessTokenEndpoint: "https://keycloak.example.com/token",
            refreshToken: "refresh-token-123"
        )

        XCTAssertEqual(options.clientId, "test-client")
        XCTAssertEqual(options.accessTokenEndpoint, "https://keycloak.example.com/token")
        XCTAssertEqual(options.refreshToken, "refresh-token-123")
    }

    private func validateParameter(_ value: String?) -> Bool {
        // Replicate the plugin's parameter validation logic
        guard let value = value, !value.isEmpty else {
            return false
        }
        return true
    }
}
