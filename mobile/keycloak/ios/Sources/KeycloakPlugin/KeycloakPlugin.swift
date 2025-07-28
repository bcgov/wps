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
    private var refreshTimer: Timer?
    private var tokenRefreshThreshold: TimeInterval = 60  // 1 minute before expiration

    public let identifier = "KeycloakPlugin"
    public let jsName = "Keycloak"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "authenticate", returnType: CAPPluginReturnPromise)
    ]

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

        DispatchQueue.main.sync {

            guard let appDelegate = UIApplication.shared.delegate as? KeycloakAppDelegate else {
                call.reject("AppDelegate must conform to KeycloakAppDelegate protocol")
                return
            }

            let keyWindow = UIApplication.shared.windows.filter { $0.isKeyWindow }.first
            var ivc: UIViewController? = nil

            if var topController = keyWindow?.rootViewController {
                while let presentedViewController = topController.presentedViewController {
                    topController = presentedViewController
                }
                ivc = topController
            }

            appDelegate.currentAuthorizationFlow =
                OIDAuthState.authState(byPresenting: request, presenting: ivc!) {
                    authState, error in
                    if let authState = authState {
                        self.authState = authState

                        // Setup automatic token refresh
                        self.setupTokenRefreshTimer()

                        call.resolve([
                            "isAuthenticated": true,
                            "accessToken": authState.lastTokenResponse?.accessToken as Any,
                            "refreshToken": authState.lastTokenResponse?.refreshToken as Any,
                            "tokenType": authState.lastTokenResponse?.tokenType as Any,
                            "expiresIn": authState.lastTokenResponse?.accessTokenExpirationDate
                                as Any,
                            "scope": authState.lastTokenResponse?.scope as Any,
                            "idToken": authState.lastTokenResponse?.idToken as Any,
                        ])
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
        // Stop any existing timer
        stopTokenRefreshTimer()

        guard let authState = self.authState,
            let expirationDate = authState.lastTokenResponse?.accessTokenExpirationDate
        else {
            return
        }

        // Calculate when to refresh (threshold seconds before expiration)
        let refreshDate = expirationDate.addingTimeInterval(-tokenRefreshThreshold)
        let timeUntilRefresh = refreshDate.timeIntervalSinceNow

        // Only set timer if refresh time is in the future
        if timeUntilRefresh > 0 {
            refreshTimer = Timer.scheduledTimer(withTimeInterval: timeUntilRefresh, repeats: false)
            { [weak self] _ in
                self?.performAutomaticTokenRefresh()
            }

            logger.debug("Token refresh timer set for \(timeUntilRefresh) seconds")
        } else {
            // Token is close to expiration or already expired, refresh immediately
            performAutomaticTokenRefresh()
        }
    }

    private func stopTokenRefreshTimer() {
        refreshTimer?.invalidate()
        refreshTimer = nil
    }

    private func performAutomaticTokenRefresh() {
        logger.debug("Performing automatic token refresh")

        performTokenRefresh { [weak self] success, tokenResponse, error in
            if success {
                self?.logger.debug("Automatic token refresh successful")
                self?.setupTokenRefreshTimer()  // Schedule next refresh

                // Notify JavaScript layer about token refresh
                self?.notifyListeners("tokenRefreshed", data: tokenResponse ?? [:])
            } else {
                self?.logger.error("Automatic token refresh failed: \(error ?? "Unknown error")")

                // Notify JavaScript layer about refresh failure
                self?.notifyListeners(
                    "tokenRefreshFailed", data: ["error": error ?? "Unknown error"])
            }
        }
    }

    private func performTokenRefresh(completion: @escaping (Bool, [String: Any]?, String?) -> Void)
    {
        guard let authState = self.authState else {
            completion(false, nil, "No authentication state available")
            return
        }

        authState.performAction { [weak self] accessToken, idToken, error in
            if let error = error {
                self?.logger.error("Token refresh error: \(error.localizedDescription)")
                completion(false, nil, error.localizedDescription)
            } else {
                self?.logger.debug("Token refresh successful")

                // Update stored auth state
                if let authState = self?.authState {
                    let tokenResponse = self?.createTokenResponse(from: authState)
                    completion(true, tokenResponse, nil)
                } else {
                    completion(false, nil, "Auth state became nil after refresh")
                }
            }
        }
    }

    private func createTokenResponse(from authState: OIDAuthState) -> [String: Any] {
        return [
            "isAuthenticated": true,
            "accessToken": authState.lastTokenResponse?.accessToken as Any,
            "refreshToken": authState.lastTokenResponse?.refreshToken as Any,
            "tokenType": authState.lastTokenResponse?.tokenType as Any,
            "expiresIn": authState.lastTokenResponse?.accessTokenExpirationDate as Any,
            "scope": authState.lastTokenResponse?.scope as Any,
            "idToken": authState.lastTokenResponse?.idToken as Any,
        ]
    }

    deinit {
        stopTokenRefreshTimer()
    }
}
