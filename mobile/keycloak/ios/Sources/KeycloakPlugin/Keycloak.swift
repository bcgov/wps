import AppAuth
import AuthenticationServices
import Capacitor
import Foundation
import UIKit

public struct KeycloakOptions {
    let clientId: String
    let authorizationBaseUrl: String
    let redirectUrl: String
    let accessTokenEndpoint: String
}

public struct KeycloakRefreshOptions {
    let clientId: String
    let accessTokenEndpoint: String
    let refreshToken: String
}

public struct KeycloakTokenResponse {
    let accessToken: String
    let refreshToken: String?
    let tokenType: String?
    let expiresIn: Int?
    let scope: String?

    func toDictionary() -> [String: Any] {
        var dict: [String: Any] = ["accessToken": accessToken]
        if let refreshToken = refreshToken { dict["refreshToken"] = refreshToken }
        if let tokenType = tokenType { dict["tokenType"] = tokenType }
        if let expiresIn = expiresIn { dict["expiresIn"] = expiresIn }
        if let scope = scope { dict["scope"] = scope }
        return dict
    }
}

@objc public class Keycloak: NSObject {
    private var refreshTimer: Timer?
    private var autoRefreshOptions: (clientId: String, accessTokenEndpoint: String, refreshToken: String)?
    private weak var plugin: KeycloakPlugin?

    public override init() {
        super.init()
    }

    public func setPlugin(_ plugin: KeycloakPlugin) {
        self.plugin = plugin
    }

    public func authenticate(
        options: KeycloakOptions, 
        completion: @escaping (Result<[String: Any], Error>) -> Void
    ) {
        print("Keycloak: Starting authentication with clientId: \(options.clientId)")
        print("Keycloak: Base URL: \(options.authorizationBaseUrl)")
        print("Keycloak: Using redirect URI: \(options.redirectUrl)")

        // Create service configuration
        guard let authorizationURL = URL(string: options.authorizationBaseUrl) else {
            completion(.failure(NSError(
                domain: "KeycloakError",
                code: 1,
                userInfo: [NSLocalizedDescriptionKey: "Invalid authorization base URL"]
            )))
            return
        }

        guard let tokenURL = URL(string: options.accessTokenEndpoint) else {
            completion(.failure(NSError(
                domain: "KeycloakError",
                code: 2,
                userInfo: [NSLocalizedDescriptionKey: "Invalid token endpoint URL"]
            )))
            return
        }

        guard let redirectURL = URL(string: options.redirectUrl) else {
            completion(.failure(NSError(
                domain: "KeycloakError",
                code: 3,
                userInfo: [NSLocalizedDescriptionKey: "Invalid redirect URL"]
            )))
            return
        }

        // Use the provided URLs directly since they should already be complete
        let configuration = OIDServiceConfiguration(
            authorizationEndpoint: authorizationURL,
            tokenEndpoint: tokenURL
        )

        // Create authorization request with PKCE
        let request = OIDAuthorizationRequest(
            configuration: configuration,
            clientId: options.clientId,
            clientSecret: nil,
            scopes: ["openid", "profile", "email"],
            redirectURL: redirectURL,
            responseType: OIDResponseTypeCode,
            additionalParameters: nil
        )

        // Ensure we're on the main thread for UI operations
        DispatchQueue.main.async { [weak self] in
            // Get presentation context from the plugin's view controller
            guard let presentingViewController = self?.plugin?.bridge?.viewController else {
                print("Keycloak: Could not find presenting view controller from plugin")
                completion(.failure(NSError(
                    domain: "KeycloakError",
                    code: 4,
                    userInfo: [NSLocalizedDescriptionKey: "Could not find presenting view controller"]
                )))
                return
            }
            
            print("Keycloak: Found presenting view controller: \(presentingViewController)")
            print("Keycloak: Starting authorization request")
            
            // Get the app delegate to store the authorization flow
            guard let appDelegate = UIApplication.shared.delegate as? KeycloakAppDelegate else {
                print("Keycloak: Could not find AppDelegate conforming to KeycloakAppDelegate protocol")
                completion(.failure(NSError(
                    domain: "KeycloakError",
                    code: 5,
                    userInfo: [NSLocalizedDescriptionKey: "Could not find AppDelegate conforming to KeycloakAppDelegate protocol"]
                )))
                return
            }
            
            // Perform authorization request and store in AppDelegate
            appDelegate.currentAuthorizationFlow = OIDAuthState.authState(
                byPresenting: request,
                presenting: presentingViewController
            ) { [weak self] authState, error in
                // Clear the authorization flow from AppDelegate
                appDelegate.currentAuthorizationFlow = nil
                
                self?.handleAuthorizationResponse(
                    authState: authState,
                    error: error,
                    completion: completion
                )
            }
        }
    }

    private func handleAuthorizationResponse(
        authState: OIDAuthState?,
        error: Error?,
        completion: @escaping (Result<[String: Any], Error>) -> Void
    ) {
        if let error = error {
            print("Keycloak: Authorization error: \(error.localizedDescription)")
            completion(.failure(error))
            return
        }

        guard let authState = authState else {
            completion(.failure(NSError(
                domain: "KeycloakError",
                code: 6,
                userInfo: [NSLocalizedDescriptionKey: "No auth state received"]
            )))
            return
        }

        guard let accessToken = authState.lastTokenResponse?.accessToken else {
            completion(.failure(NSError(
                domain: "KeycloakError",
                code: 7,
                userInfo: [NSLocalizedDescriptionKey: "No access token received"]
            )))
            return
        }

        print("Keycloak: Authentication successful")

        // Create response
        var response: [String: Any] = [
            "isAuthenticated": true,
            "accessToken": accessToken
        ]

        if let refreshToken = authState.lastTokenResponse?.refreshToken {
            response["refreshToken"] = refreshToken
        }

        if let tokenType = authState.lastTokenResponse?.tokenType {
            response["tokenType"] = tokenType
        }

        if let expiresIn = authState.lastTokenResponse?.accessTokenExpirationDate {
            let timeInterval = expiresIn.timeIntervalSinceNow
            response["expiresIn"] = Int(timeInterval)
        }

        if let scope = authState.lastTokenResponse?.scope {
            response["scope"] = scope
        }

        if let idToken = authState.lastTokenResponse?.idToken {
            response["idToken"] = idToken
        }

        // Set up automatic token refresh
        if let refreshToken = authState.lastTokenResponse?.refreshToken,
           let expirationDate = authState.lastTokenResponse?.accessTokenExpirationDate {
            let expiresIn = Int(expirationDate.timeIntervalSinceNow)
            scheduleTokenRefresh(
                authState: authState,
                expiresIn: expiresIn
            )
        }

        completion(.success(response))
    }

    public func refreshToken(
        options: KeycloakRefreshOptions,
        completion: @escaping (Result<[String: Any], Error>) -> Void
    ) {
        print("Keycloak: Refreshing token for clientId: \(options.clientId)")
        print("Keycloak: Token endpoint: \(options.accessTokenEndpoint)")

        guard let tokenURL = URL(string: options.accessTokenEndpoint) else {
            completion(.failure(NSError(
                domain: "KeycloakError",
                code: 8,
                userInfo: [NSLocalizedDescriptionKey: "Invalid token endpoint URL"]
            )))
            return
        }

        // Create a minimal configuration for token refresh
        let configuration = OIDServiceConfiguration(
            authorizationEndpoint: tokenURL, // Not used for refresh
            tokenEndpoint: tokenURL
        )

        // Create token refresh request
        let request = OIDTokenRequest(
            configuration: configuration,
            grantType: OIDGrantTypeRefreshToken,
            authorizationCode: nil,
            redirectURL: nil,
            clientID: options.clientId,
            clientSecret: nil,
            scope: nil,
            refreshToken: options.refreshToken,
            codeVerifier: nil,
            additionalParameters: nil
        )

        // Perform token refresh
        OIDAuthorizationService.perform(request) { response, error in
            if let error = error {
                print("Keycloak: Token refresh error: \(error.localizedDescription)")
                completion(.failure(error))
                return
            }

            guard let response = response else {
                completion(.failure(NSError(
                    domain: "KeycloakError",
                    code: 9,
                    userInfo: [NSLocalizedDescriptionKey: "No response received from token endpoint"]
                )))
                return
            }

            print("Keycloak: Token refresh successful")

            // Create structured response
            var structuredResponse: [String: Any] = [:]

            if let accessToken = response.accessToken {
                structuredResponse["accessToken"] = accessToken
            }

            if let refreshToken = response.refreshToken {
                structuredResponse["refreshToken"] = refreshToken
            }

            if let tokenType = response.tokenType {
                structuredResponse["tokenType"] = tokenType
            }

            if let expirationDate = response.accessTokenExpirationDate {
                let expiresIn = Int(expirationDate.timeIntervalSinceNow)
                structuredResponse["expiresIn"] = expiresIn
            }

            if let scope = response.scope {
                structuredResponse["scope"] = scope
            }

            completion(.success(structuredResponse))
        }
    }

    private func scheduleTokenRefresh(authState: OIDAuthState, expiresIn: Int) {
        // Cancel any existing timer
        refreshTimer?.invalidate()

        // Schedule refresh 5 minutes (300 seconds) before expiration
        let bufferTime = 300
        let refreshTime = max(expiresIn - bufferTime, 10) // Minimum 10 seconds

        print("Keycloak: Scheduling token refresh in \(refreshTime) seconds")

        refreshTimer = Timer.scheduledTimer(withTimeInterval: TimeInterval(refreshTime), repeats: false) { [weak self] _ in
            self?.performAutomaticRefresh(authState: authState)
        }
    }

    private func performAutomaticRefresh(authState: OIDAuthState) {
        print("Keycloak: Performing automatic token refresh")

        authState.performAction { [weak self] accessToken, idToken, error in
            if let error = error {
                print("Keycloak: Automatic token refresh failed: \(error.localizedDescription)")
                return
            }

            guard let accessToken = accessToken else {
                print("Keycloak: No access token received during automatic refresh")
                return
            }

            print("Keycloak: Automatic token refresh successful")

            // Create token response for notification
            let tokenResponse = KeycloakTokenResponse(
                accessToken: accessToken,
                refreshToken: authState.lastTokenResponse?.refreshToken,
                tokenType: authState.lastTokenResponse?.tokenType,
                expiresIn: authState.lastTokenResponse?.accessTokenExpirationDate.map { Int($0.timeIntervalSinceNow) },
                scope: authState.lastTokenResponse?.scope
            )

            // Send event to JavaScript
            DispatchQueue.main.async {
                self?.plugin?.notifyListeners("tokenRefresh", data: tokenResponse.toDictionary())
            }

            // Schedule next refresh
            if let expirationDate = authState.lastTokenResponse?.accessTokenExpirationDate {
                let expiresIn = Int(expirationDate.timeIntervalSinceNow)
                self?.scheduleTokenRefresh(authState: authState, expiresIn: expiresIn)
            }
        }
    }
}
