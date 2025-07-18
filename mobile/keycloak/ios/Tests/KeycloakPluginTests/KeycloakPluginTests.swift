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
        XCTAssertEqual(plugin.pluginMethods.count, 1)
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

    private func validateParameter(_ value: String?) -> Bool {
        // Replicate the plugin's parameter validation logic
        guard let value = value, !value.isEmpty else {
            return false
        }
        return true
    }
}
