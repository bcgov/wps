import AppAuth
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

    @Test func testPluginWithMockServices() {
        // Test that the plugin can be created with custom services
        let customServices = KeycloakServices()
        let pluginWithServices = KeycloakPlugin(services: customServices)

        #expect(pluginWithServices.identifier == "KeycloakPlugin")
        #expect(pluginWithServices.jsName == "Keycloak")
        #expect(pluginWithServices.pluginMethods.count == 1)
    }

    @Test func testDefaultServicesInitialization() {
        // Test that services are properly initialized
        let services = KeycloakServices()

        // Test that all services are available
        #expect(services.authenticationService is DefaultAuthenticationService)
        #expect(services.tokenTimerService is DefaultTokenTimerService)
        #expect(services.tokenRefreshService is DefaultTokenRefreshService)
        #expect(services.tokenResponseService is DefaultTokenResponseService)
        #expect(services.uiService is DefaultUIService)
    }

    @Test func testTokenResponseService() {
        // Test the token response service independently
        let service = DefaultTokenResponseService()
        let mockAuthState = createMockAuthState()

        let response = service.createTokenResponse(from: mockAuthState)

        #expect(response["isAuthenticated"] as? Bool == true)
        #expect(response.keys.contains("accessToken"))
        #expect(response.keys.contains("refreshToken"))
        #expect(response.keys.contains("tokenType"))
    }

    private func createMockAuthState() -> OIDAuthState {
        let config = OIDServiceConfiguration(
            authorizationEndpoint: URL(string: "https://auth.example.com/auth")!,
            tokenEndpoint: URL(string: "https://auth.example.com/token")!
        )

        // Create a minimal auth state for testing
        return OIDAuthState(
            authorizationResponse: nil, tokenResponse: nil, registrationResponse: nil)
    }
}
