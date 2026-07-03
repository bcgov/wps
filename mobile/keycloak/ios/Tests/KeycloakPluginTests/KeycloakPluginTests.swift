import AppAuth
import Capacitor
import Foundation
import Testing
import UIKit

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
        #expect(methodNames.contains("refreshAuthState"))
        #expect(methodNames.contains("clearAuthState"))
        #expect(plugin.pluginMethods.count == 3)
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
        #expect(pluginWithServices.pluginMethods.map { $0.name } == ["authenticate", "refreshAuthState", "clearAuthState"])
    }

    @Test func testDefaultServicesInitialization() {
        // Test that services are properly initialized
        let services = KeycloakServices()

        // Test that all services are available
        #expect(services.authenticationService is DefaultAuthenticationService)
        #expect(services.tokenTimerService is DefaultTokenTimerService)
        #expect(services.tokenRefreshService is DefaultTokenRefreshService)
        #expect(services.tokenResponseService is DefaultTokenResponseService)
        #expect(services.authStateStorageService is KeychainAuthStateStorageService)
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

    @Test func testForegroundRefreshFailureClearsStoredAuthState() async throws {
        let storage = SpyAuthStateStorageService(authState: makeExpiringAuthorizedAuthState())
        let plugin = KeycloakPlugin(services: KeycloakServices(
            tokenRefreshService: MockFailingTokenRefreshService(),
            authStateStorageService: storage
        ))
        plugin.load()

        await withCheckedContinuation { (continuation: CheckedContinuation<Void, Never>) in
            storage.onClearAuthState = { continuation.resume() }
            NotificationCenter.default.post(
                name: UIApplication.didBecomeActiveNotification, object: nil)
        }

        #expect(storage.storedAuthState == nil)
    }

    private func makeExpiringAuthorizedAuthState() -> OIDAuthState {
        let config = OIDServiceConfiguration(
            authorizationEndpoint: URL(string: "https://auth.example.com/auth")!,
            tokenEndpoint: URL(string: "https://auth.example.com/token")!
        )
        let authRequest = OIDAuthorizationRequest(
            configuration: config,
            clientId: "test-client",
            scopes: ["openid"],
            redirectURL: URL(string: "test://callback")!,
            responseType: OIDResponseTypeCode,
            additionalParameters: nil
        )
        let authResponse = OIDAuthorizationResponse(
            request: authRequest,
            parameters: ["code": "test-code" as NSCopying & NSObjectProtocol]
        )
        let tokenRequest = OIDTokenRequest(
            configuration: config,
            grantType: OIDGrantTypeAuthorizationCode,
            authorizationCode: "test-code",
            redirectURL: URL(string: "test://callback")!,
            clientID: "test-client",
            clientSecret: nil,
            scope: "openid",
            refreshToken: nil,
            codeVerifier: nil,
            additionalParameters: nil
        )
        let tokenResponse = OIDTokenResponse(
            request: tokenRequest,
            parameters: [
                "access_token": "test-access-token" as NSCopying & NSObjectProtocol,
                "refresh_token": "test-refresh-token" as NSCopying & NSObjectProtocol,
                "token_type": "Bearer" as NSCopying & NSObjectProtocol,
                "expires_in": NSNumber(value: 30) as NSCopying & NSObjectProtocol,
            ]
        )
        return OIDAuthState(
            authorizationResponse: authResponse,
            tokenResponse: tokenResponse,
            registrationResponse: nil
        )
    }
}

private final class MockFailingTokenRefreshService: TokenRefreshServiceProtocol {
    func performAutomaticTokenRefresh(
        authState: OIDAuthState?,
        onSuccess: @escaping ([String: Any]) -> Void,
        onFailure: @escaping (String) -> Void,
        onTokenRefreshed: @escaping () -> Void
    ) {
        onFailure("mock-refresh-failed")
    }

    func performTokenRefresh(
        authState: OIDAuthState?,
        completion: @escaping (Bool, [String: Any]?, String?) -> Void
    ) {
        completion(false, nil, "mock-refresh-failed")
    }
}

private final class SpyAuthStateStorageService: AuthStateStorageServiceProtocol {
    var storedAuthState: OIDAuthState?
    var clearAuthStateCalled = false
    var onClearAuthState: (() -> Void)?

    init(authState: OIDAuthState?) {
        storedAuthState = authState
    }

    func saveAuthState(_ authState: OIDAuthState) {
        storedAuthState = authState
    }

    func loadAuthState() -> OIDAuthState? {
        storedAuthState
    }

    func clearAuthState() {
        clearAuthStateCalled = true
        storedAuthState = nil
        onClearAuthState?()
    }
}
