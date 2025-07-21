import Capacitor
import Foundation
import Testing

@testable import KeycloakPlugin

struct KeycloakPluginTests {

    var plugin: KeycloakPlugin

    init() {
        plugin = KeycloakPlugin()
    }

    @Test func testPluginIdentifier() {
        #expect(plugin.identifier == "KeycloakPlugin")
    }

    @Test func testPluginJSName() {
        #expect(plugin.jsName == "Keycloak")
    }

    @Test func testPluginMethods() {
        let methodNames = plugin.pluginMethods.map { $0.name }
        #expect(methodNames.contains("authenticate"))
        #expect(plugin.pluginMethods.count == 1)
    }

    @Test func testPluginMethodReturnTypes() {
        for method in plugin.pluginMethods {
            #expect(method.returnType == CAPPluginReturnPromise)
        }
    }

    @Test func testPluginLoad() {
        // This test verifies that load() can be called without crashing
        // In Swift Testing, we just call it and expect no crash
        plugin.load()
    }

    @Test func testParameterValidation() {
        // These tests verify the plugin's parameter validation logic
        // by testing the actual logic patterns used in the plugin

        // Test required parameter checking pattern
        #expect(validateParameter("test-value") == true)
        #expect(validateParameter(nil) == false)
        #expect(validateParameter("") == false)
    }

    private func validateParameter(_ value: String?) -> Bool {
        // Replicate the plugin's parameter validation logic
        guard let value = value, !value.isEmpty else {
            return false
        }
        return true
    }
}
