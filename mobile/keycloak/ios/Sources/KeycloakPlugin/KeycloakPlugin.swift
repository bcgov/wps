import AppAuth
import Capacitor
import Foundation
import OSLog
import UIKit

// Protocol to define the AppDelegate interface for authentication
public protocol KeycloakAppDelegate: AnyObject {
    var currentAuthorizationFlow: OIDExternalUserAgentSession? { get set }
}

/// Please read the Capacitor iOS Plugin Development Guide
/// here: https://capacitorjs.com/docs/plugins/ios
@objc(KeycloakPlugin)
public class KeycloakPlugin: CAPPlugin, CAPBridgedPlugin {
    private var authState: OIDAuthState?
    private let logger = Logger(subsystem: "com.bcgov.wps.keycloak", category: "authentication")
    private var tokenRefreshThreshold: TimeInterval = 60  // 1 minute before expiration

    // Services for dependency injection
    private let services: KeycloakServices

    public let identifier = "KeycloakPlugin"
    public let jsName = "Keycloak"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "authenticate", returnType: CAPPluginReturnPromise)
    ]

    // Default initializer uses default services
    public override init() {
        self.services = KeycloakServices()
        super.init()
    }

    // Internal initializer for testing with injected services
    internal init(services: KeycloakServices) {
        self.services = services
        super.init()
    }

    @objc func authenticate(_ call: CAPPluginCall) {
        // Validate parameters using the injected validator
        let validationResult = services.parameterValidator.validateAuthenticationParameters(call)

        let parameters: AuthenticationParameters
        switch validationResult {
        case .success(let validatedParameters):
            parameters = validatedParameters
        case .failure(let error):
            call.reject(error.localizedDescription)
            return
        }

        services.authenticationFlowService.performAuthenticationFlow(
            parameters: parameters,
            call: call
        ) { [weak self] authState in
            self?.authState = authState
            if authState != nil {
                self?.setupTokenRefreshTimer()
            }
        }
    }

    private func setupTokenRefreshTimer() {
        services.tokenTimerService.setupTokenRefreshTimer(
            authState: authState,
            tokenRefreshThreshold: tokenRefreshThreshold
        ) { [weak self] in
            self?.performAutomaticTokenRefresh()
        }
    }

    private func stopTokenRefreshTimer() {
        services.tokenTimerService.stopTokenRefreshTimer()
    }

    private func performAutomaticTokenRefresh() {
        services.tokenRefreshService.performAutomaticTokenRefresh(
            authState: authState,
            onSuccess: { [weak self] tokenResponse in
                // Notify JavaScript layer about token refresh
                self?.notifyListeners("tokenRefreshed", data: tokenResponse)
            },
            onFailure: { [weak self] error in
                // Notify JavaScript layer about refresh failure
                self?.notifyListeners("tokenRefreshFailed", data: ["error": error])
            },
            onTokenRefreshed: { [weak self] in
                self?.setupTokenRefreshTimer()  // Schedule next refresh
            }
        )
    }

    private func performTokenRefresh(completion: @escaping (Bool, [String: Any]?, String?) -> Void)
    {
        services.tokenRefreshService.performTokenRefresh(
            authState: authState, completion: completion)
    }

    private func createTokenResponse(from authState: OIDAuthState) -> [String: Any] {
        return services.tokenResponseService.createTokenResponse(from: authState)
    }

    deinit {
        stopTokenRefreshTimer()
    }
}
