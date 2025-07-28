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
        guard let clientId = call.getString("clientId") else {
            call.reject("Missing required parameter: clientId")
            return
        }

        guard let authorizationBaseUrl = call.getString("authorizationBaseUrl") else {
            call.reject("Missing required parameter: authorizationBaseUrl")
            return
        }

        guard let redirectUrl = call.getString("redirectUrl") else {
            call.reject("Missing required parameter: redirectUrl")
            return
        }

        guard let tokenUrl = call.getString("accessTokenEndpoint") else {
            call.reject("Missing required parameter: accessTokenEndpoint")
            return
        }

        // Convert string URLs to URL objects
        guard let authorizationEndpointURL = URL(string: authorizationBaseUrl) else {
            call.reject("Invalid authorizationBaseUrl")
            return
        }

        guard let tokenEndpointURL = URL(string: tokenUrl) else {
            call.reject("Invalid accessTokenEndpoint")
            return
        }

        guard let redirectURL = URL(string: redirectUrl) else {
            call.reject("Invalid redirectUrl")
            return
        }

        let configuration = OIDServiceConfiguration(
            authorizationEndpoint: authorizationEndpointURL,
            tokenEndpoint: tokenEndpointURL)

        let request = OIDAuthorizationRequest(
            configuration: configuration,
            clientId: clientId,
            scopes: [OIDScopeOpenID, OIDScopeProfile, "offline_access"],
            redirectURL: redirectURL,
            responseType: OIDResponseTypeCode,
            additionalParameters: nil)

        services.uiService.executeOnMainQueue {
            guard let appDelegate = self.services.uiService.getAppDelegate() else {
                call.reject("AppDelegate must conform to KeycloakAppDelegate protocol")
                return
            }

            guard
                let presentingViewController = self.services.uiService.getPresentingViewController()
            else {
                call.reject("Unable to find presenting view controller")
                return
            }

            appDelegate.currentAuthorizationFlow = self.services.authenticationService
                .performAuthentication(
                    request: request,
                    appDelegate: appDelegate,
                    presentingViewController: presentingViewController
                ) { authState, error in
                    if let authState = authState {
                        self.authState = authState

                        // Setup automatic token refresh
                        self.setupTokenRefreshTimer()

                        let tokenResponse = self.services.tokenResponseService.createTokenResponse(
                            from: authState)
                        call.resolve(tokenResponse)

                        self.logger.debug(
                            "Got authorization tokens. Access token: \(authState.lastTokenResponse?.accessToken ?? "nil", privacy: .private)"
                        )

                    } else {
                        self.logger.error(
                            "Authorization error: \(error?.localizedDescription ?? "Unknown error")"
                        )
                        self.authState = nil
                        call.reject(
                            "Authentication failed", error?.localizedDescription ?? "Unknown error")
                    }
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
