import AppAuth
import Capacitor
import Foundation
import OSLog

#if canImport(UIKit)
    import UIKit
#endif

/// Protocol for authentication flow operations
public protocol AuthenticationServiceProtocol {
    func performAuthentication(
        request: OIDAuthorizationRequest,
        appDelegate: KeycloakAppDelegate,
        presentingViewController: UIViewController,
        completion: @escaping (OIDAuthState?, Error?) -> Void
    ) -> OIDExternalUserAgentSession?
}

/// Protocol for token refresh timer management
public protocol TokenTimerServiceProtocol {
    func setupTokenRefreshTimer(
        authState: OIDAuthState?,
        tokenRefreshThreshold: TimeInterval,
        onRefresh: @escaping () -> Void
    )
    func stopTokenRefreshTimer()
}

/// Protocol for token refresh operations
public protocol TokenRefreshServiceProtocol {
    func performAutomaticTokenRefresh(
        authState: OIDAuthState?,
        onSuccess: @escaping ([String: Any]) -> Void,
        onFailure: @escaping (String) -> Void,
        onTokenRefreshed: @escaping () -> Void
    )

    func performTokenRefresh(
        authState: OIDAuthState?,
        completion: @escaping (Bool, [String: Any]?, String?) -> Void
    )
}

/// Protocol for token response creation
public protocol TokenResponseServiceProtocol {
    func createTokenResponse(from authState: OIDAuthState) -> [String: Any]
}

/// Protocol for UI operations
public protocol UIServiceProtocol {
    func getAppDelegate() -> KeycloakAppDelegate?
    func getPresentingViewController() -> UIViewController?
    func executeOnMainQueue<T>(_ block: @escaping () -> T) -> T
}

/// Default implementation of AuthenticationServiceProtocol
public class DefaultAuthenticationService: AuthenticationServiceProtocol {
    public init() {}

    public func performAuthentication(
        request: OIDAuthorizationRequest,
        appDelegate: KeycloakAppDelegate,
        presentingViewController: UIViewController,
        completion: @escaping (OIDAuthState?, Error?) -> Void
    ) -> OIDExternalUserAgentSession? {
        return OIDAuthState.authState(
            byPresenting: request, presenting: presentingViewController, callback: completion)
    }
}

/// Default implementation of TokenTimerServiceProtocol
public class DefaultTokenTimerService: TokenTimerServiceProtocol {
    private var refreshTimer: Timer?
    private let logger = Logger(subsystem: "com.bcgov.wps.keycloak", category: "timer")

    public init() {}

    public func setupTokenRefreshTimer(
        authState: OIDAuthState?,
        tokenRefreshThreshold: TimeInterval,
        onRefresh: @escaping () -> Void
    ) {
        // Stop any existing timer
        stopTokenRefreshTimer()

        guard let authState = authState,
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
            { _ in
                onRefresh()
            }

            logger.debug("Token refresh timer set for \(timeUntilRefresh) seconds")
        } else {
            // Token is close to expiration or already expired, refresh immediately
            onRefresh()
        }
    }

    public func stopTokenRefreshTimer() {
        refreshTimer?.invalidate()
        refreshTimer = nil
    }

    deinit {
        stopTokenRefreshTimer()
    }
}

/// Default implementation of TokenRefreshServiceProtocol
public class DefaultTokenRefreshService: TokenRefreshServiceProtocol {
    private let logger = Logger(subsystem: "com.bcgov.wps.keycloak", category: "token-refresh")

    public init() {}

    public func performAutomaticTokenRefresh(
        authState: OIDAuthState?,
        onSuccess: @escaping ([String: Any]) -> Void,
        onFailure: @escaping (String) -> Void,
        onTokenRefreshed: @escaping () -> Void
    ) {
        logger.debug("Performing automatic token refresh")

        performTokenRefresh(authState: authState) { [weak self] success, tokenResponse, error in
            if success {
                self?.logger.debug("Automatic token refresh successful")
                onTokenRefreshed()  // Schedule next refresh
                onSuccess(tokenResponse ?? [:])
            } else {
                let errorMessage = error ?? "Unknown error"
                self?.logger.error("Automatic token refresh failed: \(errorMessage)")
                onFailure(errorMessage)
            }
        }
    }

    public func performTokenRefresh(
        authState: OIDAuthState?,
        completion: @escaping (Bool, [String: Any]?, String?) -> Void
    ) {
        guard let authState = authState else {
            completion(false, nil, "No authentication state available")
            return
        }

        authState.performAction { [weak self] accessToken, idToken, error in
            if let error = error {
                self?.logger.error("Token refresh error: \(error.localizedDescription)")
                completion(false, nil, error.localizedDescription)
            } else {
                self?.logger.debug("Token refresh successful")

                let tokenResponse = DefaultTokenResponseService().createTokenResponse(
                    from: authState)
                completion(true, tokenResponse, nil)
            }
        }
    }
}

/// Default implementation of TokenResponseServiceProtocol
public class DefaultTokenResponseService: TokenResponseServiceProtocol {
    public init() {}

    public func createTokenResponse(from authState: OIDAuthState) -> [String: Any] {
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
}

/// Default implementation of UIServiceProtocol
public class DefaultUIService: UIServiceProtocol {
    public init() {}

    public func getAppDelegate() -> KeycloakAppDelegate? {
        #if canImport(UIKit)
            return UIApplication.shared.delegate as? KeycloakAppDelegate
        #else
            return nil
        #endif
    }

    public func getPresentingViewController() -> UIViewController? {
        #if canImport(UIKit)
            let keyWindow = UIApplication.shared.windows.filter { $0.isKeyWindow }.first
            var ivc: UIViewController?

            if var topController = keyWindow?.rootViewController {
                while let presentedViewController = topController.presentedViewController {
                    topController = presentedViewController
                }
                ivc = topController
            }

            return ivc
        #else
            return nil
        #endif
    }

    public func executeOnMainQueue<T>(_ block: @escaping () -> T) -> T {
        if Thread.isMainThread {
            return block()
        } else {
            return DispatchQueue.main.sync(execute: block)
        }
    }
}

/// Container for all services used by KeycloakPlugin
public struct KeycloakServices {
    public let authenticationService: AuthenticationServiceProtocol
    public let tokenTimerService: TokenTimerServiceProtocol
    public let tokenRefreshService: TokenRefreshServiceProtocol
    public let tokenResponseService: TokenResponseServiceProtocol
    public let uiService: UIServiceProtocol

    public init(
        authenticationService: AuthenticationServiceProtocol = DefaultAuthenticationService(),
        tokenTimerService: TokenTimerServiceProtocol = DefaultTokenTimerService(),
        tokenRefreshService: TokenRefreshServiceProtocol = DefaultTokenRefreshService(),
        tokenResponseService: TokenResponseServiceProtocol = DefaultTokenResponseService(),
        uiService: UIServiceProtocol = DefaultUIService()
    ) {
        self.authenticationService = authenticationService
        self.tokenTimerService = tokenTimerService
        self.tokenRefreshService = tokenRefreshService
        self.tokenResponseService = tokenResponseService
        self.uiService = uiService
    }
}
