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

/// Protocol for validating authentication parameters
public protocol AuthenticationParameterValidatorProtocol {
    func validateAuthenticationParameters(_ call: CAPPluginCall) -> Result<
        AuthenticationParameters, ValidationError
    >
}

/// Protocol for handling the complete authentication flow
public protocol AuthenticationFlowServiceProtocol {
    func performAuthenticationFlow(
        parameters: AuthenticationParameters,
        call: CAPPluginCall,
        completion: @escaping (OIDAuthState?) -> Void
    )
}

/// Protocol for managing token refresh lifecycle
public protocol TokenRefreshManagerServiceProtocol {
    func startTokenRefreshManager(
        authState: OIDAuthState,
        tokenRefreshThreshold: TimeInterval,
        onTokenRefreshed: @escaping ([String: Any]) -> Void,
        onTokenRefreshFailed: @escaping (String) -> Void
    )
    func stopTokenRefreshManager()
}

public class AuthenticationParameterValidator: AuthenticationParameterValidatorProtocol {

    public init() {}

    public func validateAuthenticationParameters(_ call: CAPPluginCall) -> Result<
        AuthenticationParameters, ValidationError
    > {

        // Validate required string parameters
        guard let clientId = call.getString("clientId") else {
            return .failure(.missingParameter("clientId"))
        }

        guard let authorizationBaseUrl = call.getString("authorizationBaseUrl") else {
            return .failure(.missingParameter("authorizationBaseUrl"))
        }

        guard let redirectUrl = call.getString("redirectUrl") else {
            return .failure(.missingParameter("redirectUrl"))
        }

        guard let tokenUrl = call.getString("accessTokenEndpoint") else {
            return .failure(.missingParameter("accessTokenEndpoint"))
        }

        // Validate URL formats
        guard let authorizationEndpointURL = URL(string: authorizationBaseUrl) else {
            return .failure(.invalidURL("authorizationBaseUrl", authorizationBaseUrl))
        }

        guard let tokenEndpointURL = URL(string: tokenUrl) else {
            return .failure(.invalidURL("accessTokenEndpoint", tokenUrl))
        }

        guard let redirectURL = URL(string: redirectUrl) else {
            return .failure(.invalidURL("redirectUrl", redirectUrl))
        }

        let parameters = AuthenticationParameters(
            clientId: clientId,
            authorizationEndpointURL: authorizationEndpointURL,
            tokenEndpointURL: tokenEndpointURL,
            redirectURL: redirectURL
        )

        return .success(parameters)
    }
}

/// Struct containing validated authentication parameters
public struct AuthenticationParameters {
    public let clientId: String
    public let authorizationEndpointURL: URL
    public let tokenEndpointURL: URL
    public let redirectURL: URL

    public init(
        clientId: String, authorizationEndpointURL: URL, tokenEndpointURL: URL, redirectURL: URL
    ) {
        self.clientId = clientId
        self.authorizationEndpointURL = authorizationEndpointURL
        self.tokenEndpointURL = tokenEndpointURL
        self.redirectURL = redirectURL
    }
}

/// Enumeration of possible validation errors
public enum ValidationError: Error, Equatable {
    case missingParameter(String)
    case invalidURL(String, String)  // parameter name, invalid value

    public var localizedDescription: String {
        switch self {
        case .missingParameter(let parameter):
            return "Missing required parameter: \(parameter)"
        case .invalidURL(let parameter, let value):
            return "Invalid \(parameter): \(value)"
        }
    }
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

/// Default implementation of the authentication parameter validator
public class DefaultAuthenticationParameterValidator: AuthenticationParameterValidatorProtocol {

    public init() {}

    public func validateAuthenticationParameters(_ call: CAPPluginCall) -> Result<
        AuthenticationParameters, ValidationError
    > {

        // Validate required string parameters
        guard let clientId = call.getString("clientId") else {
            return .failure(.missingParameter("clientId"))
        }

        guard let authorizationBaseUrl = call.getString("authorizationBaseUrl") else {
            return .failure(.missingParameter("authorizationBaseUrl"))
        }

        guard let redirectUrl = call.getString("redirectUrl") else {
            return .failure(.missingParameter("redirectUrl"))
        }

        guard let tokenUrl = call.getString("accessTokenEndpoint") else {
            return .failure(.missingParameter("accessTokenEndpoint"))
        }

        // Validate URL formats
        guard let authorizationEndpointURL = URL(string: authorizationBaseUrl) else {
            return .failure(.invalidURL("authorizationBaseUrl", authorizationBaseUrl))
        }

        guard let tokenEndpointURL = URL(string: tokenUrl) else {
            return .failure(.invalidURL("accessTokenEndpoint", tokenUrl))
        }

        guard let redirectURL = URL(string: redirectUrl) else {
            return .failure(.invalidURL("redirectUrl", redirectUrl))
        }

        let parameters = AuthenticationParameters(
            clientId: clientId,
            authorizationEndpointURL: authorizationEndpointURL,
            tokenEndpointURL: tokenEndpointURL,
            redirectURL: redirectURL
        )

        return .success(parameters)
    }
}

/// Default implementation of AuthenticationFlowServiceProtocol
public class DefaultAuthenticationFlowService: AuthenticationFlowServiceProtocol {
    private let authenticationService: AuthenticationServiceProtocol
    private let tokenResponseService: TokenResponseServiceProtocol
    private let uiService: UIServiceProtocol
    private let logger = Logger(
        subsystem: "com.bcgov.wps.keycloak", category: "authentication-flow")

    public init(
        authenticationService: AuthenticationServiceProtocol,
        tokenResponseService: TokenResponseServiceProtocol,
        uiService: UIServiceProtocol
    ) {
        self.authenticationService = authenticationService
        self.tokenResponseService = tokenResponseService
        self.uiService = uiService
    }

    public func performAuthenticationFlow(
        parameters: AuthenticationParameters,
        call: CAPPluginCall,
        completion: @escaping (OIDAuthState?) -> Void
    ) {
        let configuration = OIDServiceConfiguration(
            authorizationEndpoint: parameters.authorizationEndpointURL,
            tokenEndpoint: parameters.tokenEndpointURL
        )

        let request = OIDAuthorizationRequest(
            configuration: configuration,
            clientId: parameters.clientId,
            scopes: [OIDScopeOpenID, OIDScopeProfile, "offline_access"],
            redirectURL: parameters.redirectURL,
            responseType: OIDResponseTypeCode,
            additionalParameters: nil
        )

        uiService.executeOnMainQueue {
            guard let appDelegate = self.uiService.getAppDelegate() else {
                call.reject("AppDelegate must conform to KeycloakAppDelegate protocol")
                return
            }

            guard let presentingViewController = self.uiService.getPresentingViewController() else {
                call.reject("Unable to find presenting view controller")
                return
            }

            appDelegate.currentAuthorizationFlow = self.authenticationService.performAuthentication(
                request: request,
                appDelegate: appDelegate,
                presentingViewController: presentingViewController
            ) { authState, error in
                self.handleAuthenticationResult(
                    authState: authState,
                    error: error,
                    call: call,
                    completion: completion
                )
            }
        }
    }

    private func handleAuthenticationResult(
        authState: OIDAuthState?,
        error: Error?,
        call: CAPPluginCall,
        completion: @escaping (OIDAuthState?) -> Void
    ) {
        if let authState = authState {
            let tokenResponse = tokenResponseService.createTokenResponse(from: authState)
            call.resolve(tokenResponse)

            logger.debug(
                "Got authorization tokens. Access token: \(authState.lastTokenResponse?.accessToken ?? "nil", privacy: .private)"
            )

            completion(authState)
        } else {
            logger.error(
                "Authorization error: \(error?.localizedDescription ?? "Unknown error")"
            )
            call.reject(
                "Authentication failed", error?.localizedDescription ?? "Unknown error"
            )

            completion(nil)
        }
    }
}

/// Default implementation of TokenRefreshManagerServiceProtocol
public class DefaultTokenRefreshManagerService: TokenRefreshManagerServiceProtocol {
    private let tokenTimerService: TokenTimerServiceProtocol
    private let tokenRefreshService: TokenRefreshServiceProtocol
    private var currentAuthState: OIDAuthState?
    private var tokenRefreshThreshold: TimeInterval = 60
    private var onTokenRefreshed: (([String: Any]) -> Void)?
    private var onTokenRefreshFailed: ((String) -> Void)?

    public init(
        tokenTimerService: TokenTimerServiceProtocol,
        tokenRefreshService: TokenRefreshServiceProtocol
    ) {
        self.tokenTimerService = tokenTimerService
        self.tokenRefreshService = tokenRefreshService
    }

    public func startTokenRefreshManager(
        authState: OIDAuthState,
        tokenRefreshThreshold: TimeInterval,
        onTokenRefreshed: @escaping ([String: Any]) -> Void,
        onTokenRefreshFailed: @escaping (String) -> Void
    ) {
        self.currentAuthState = authState
        self.tokenRefreshThreshold = tokenRefreshThreshold
        self.onTokenRefreshed = onTokenRefreshed
        self.onTokenRefreshFailed = onTokenRefreshFailed

        setupTokenRefreshTimer(with: authState)
    }

    public func stopTokenRefreshManager() {
        tokenTimerService.stopTokenRefreshTimer()
        currentAuthState = nil
        onTokenRefreshed = nil
        onTokenRefreshFailed = nil
    }

    private func setupTokenRefreshTimer(with authState: OIDAuthState) {
        tokenTimerService.setupTokenRefreshTimer(
            authState: authState,
            tokenRefreshThreshold: tokenRefreshThreshold
        ) { [weak self] in
            self?.performAutomaticTokenRefresh()
        }
    }

    private func performAutomaticTokenRefresh() {
        tokenRefreshService.performAutomaticTokenRefresh(
            authState: currentAuthState,
            onSuccess: { [weak self] tokenResponse in
                self?.onTokenRefreshed?(tokenResponse)
            },
            onFailure: { [weak self] error in
                self?.onTokenRefreshFailed?(error)
            },
            onTokenRefreshed: { [weak self] in
                guard let self = self, let authState = self.currentAuthState else { return }
                self.setupTokenRefreshTimer(with: authState)
            }
        )
    }
}

/// Container for all services used by KeycloakPlugin
public struct KeycloakServices {
    public let authenticationService: AuthenticationServiceProtocol
    public let authenticationFlowService: AuthenticationFlowServiceProtocol
    public let tokenTimerService: TokenTimerServiceProtocol
    public let tokenRefreshService: TokenRefreshServiceProtocol
    public let tokenRefreshManagerService: TokenRefreshManagerServiceProtocol
    public let tokenResponseService: TokenResponseServiceProtocol
    public let uiService: UIServiceProtocol
    public let parameterValidator: AuthenticationParameterValidatorProtocol

    public init(
        authenticationService: AuthenticationServiceProtocol = DefaultAuthenticationService(),
        tokenTimerService: TokenTimerServiceProtocol = DefaultTokenTimerService(),
        tokenRefreshService: TokenRefreshServiceProtocol = DefaultTokenRefreshService(),
        tokenResponseService: TokenResponseServiceProtocol = DefaultTokenResponseService(),
        uiService: UIServiceProtocol = DefaultUIService(),
        parameterValidator: AuthenticationParameterValidatorProtocol =
            DefaultAuthenticationParameterValidator()
    ) {
        self.authenticationService = authenticationService
        self.authenticationFlowService = DefaultAuthenticationFlowService(
            authenticationService: authenticationService,
            tokenResponseService: tokenResponseService,
            uiService: uiService
        )
        self.tokenTimerService = tokenTimerService
        self.tokenRefreshService = tokenRefreshService
        self.tokenRefreshManagerService = DefaultTokenRefreshManagerService(
            tokenTimerService: tokenTimerService,
            tokenRefreshService: tokenRefreshService
        )
        self.tokenResponseService = tokenResponseService
        self.uiService = uiService
        self.parameterValidator = parameterValidator
    }
}
