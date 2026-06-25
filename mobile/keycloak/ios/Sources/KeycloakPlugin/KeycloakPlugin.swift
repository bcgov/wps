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
    private var isAppInBackground = false
    private var lifecycleObservers: [NSObjectProtocol] = []

    // Services for dependency injection
    private let services: KeycloakServices

    public let identifier = "KeycloakPlugin"
    public let jsName = "Keycloak"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "authenticate", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "clearAuthState", returnType: CAPPluginReturnPromise),
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

    public override func load() {
        super.load()
        registerLifecycleObservers()

        guard let restoredAuthState = services.authStateStorageService.loadAuthState() else {
            return
        }

        if restoredAuthState.isAuthorized {
            authState = restoredAuthState
            if !isAppInBackground {
                startTokenRefreshManager(authState: restoredAuthState)
            }
        } else {
            services.authStateStorageService.clearAuthState()
        }
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

        if let existingAuthState = authState ?? services.authStateStorageService.loadAuthState() {
            if existingAuthState.isAuthorized {
                refreshExistingAuthState(
                    authState: existingAuthState,
                    call: call,
                    fallbackAuthenticationParameters: parameters
                )
                return
            }

            authState = nil
            services.authStateStorageService.clearAuthState()
        }

        performAuthentication(parameters: parameters, call: call)
    }

    @objc func clearAuthState(_ call: CAPPluginCall) {
        clearStoredAuthState()
        call.resolve()
    }

    private func refreshExistingAuthState(
        authState: OIDAuthState,
        call: CAPPluginCall,
        fallbackAuthenticationParameters parameters: AuthenticationParameters
    ) {
        services.tokenRefreshService.performTokenRefresh(authState: authState) {
            [weak self] success, tokenResponse, _ in
            guard let self = self else { return }

            if success {
                self.authState = authState
                self.services.authStateStorageService.saveAuthState(authState)
                self.startTokenRefreshManager(authState: authState)
                let response =
                    tokenResponse
                    ?? self.services.tokenResponseService.createTokenResponse(from: authState)
                call.resolve(response)
            } else {
                self.authState = nil
                self.services.authStateStorageService.clearAuthState()
                self.performAuthentication(parameters: parameters, call: call)
            }
        }
    }

    private func performAuthentication(parameters: AuthenticationParameters, call: CAPPluginCall) {
        services.authenticationFlowService.performAuthenticationFlow(
            parameters: parameters,
            call: call
        ) { [weak self] authState in
            guard let self = self else { return }

            self.authState = authState

            if let authState = authState {
                self.services.authStateStorageService.saveAuthState(authState)
                self.startTokenRefreshManager(authState: authState)
            }
        }
    }

    private func startTokenRefreshManager(authState: OIDAuthState) {
        guard !isAppInBackground else {
            return
        }

        services.tokenRefreshManagerService.startTokenRefreshManager(
            authState: authState,
            tokenRefreshThreshold: tokenRefreshThreshold,
            onTokenRefreshed: { [weak self, weak authState] tokenResponse in
                if let authState = authState {
                    self?.services.authStateStorageService.saveAuthState(authState)
                }
                // notify JavaScript layer about token refresh
                self?.notifyListeners("tokenRefresh", data: tokenResponse)
            },
            onTokenRefreshFailed: { [weak self] error in
                self?.clearStoredAuthState()
                // notify JavaScript layer about refresh failure
                self?.notifyListeners("tokenRefreshFailed", data: ["error": error])
            }
        )
    }

    private func registerLifecycleObservers() {
        removeLifecycleObservers()

        let notificationCenter = NotificationCenter.default
        lifecycleObservers = [
            notificationCenter.addObserver(
                forName: UIApplication.didEnterBackgroundNotification,
                object: nil,
                queue: .main
            ) { [weak self] _ in
                self?.handleAppDidEnterBackground()
            },
            notificationCenter.addObserver(
                forName: UIApplication.didBecomeActiveNotification,
                object: nil,
                queue: .main
            ) { [weak self] _ in
                self?.handleAppDidBecomeActive()
            },
        ]
    }

    private func removeLifecycleObservers() {
        lifecycleObservers.forEach(NotificationCenter.default.removeObserver)
        lifecycleObservers.removeAll()
    }

    private func handleAppDidEnterBackground() {
        isAppInBackground = true
        services.tokenRefreshManagerService.stopTokenRefreshManager()
        logger.debug("App entered background - automatic token refresh stopped")
    }

    private func handleAppDidBecomeActive() {
        isAppInBackground = false
        refreshStoredAuthStateOnForeground()
    }

    private func refreshStoredAuthStateOnForeground() {
        guard let existingAuthState = authState ?? services.authStateStorageService.loadAuthState()
        else {
            return
        }

        guard existingAuthState.isAuthorized else {
            authState = nil
            services.authStateStorageService.clearAuthState()
            return
        }

        services.tokenRefreshService.performTokenRefresh(authState: existingAuthState) {
            [weak self] success, tokenResponse, error in
            guard let self = self, !self.isAppInBackground else { return }

            if success {
                self.authState = existingAuthState
                self.services.authStateStorageService.saveAuthState(existingAuthState)
                self.startTokenRefreshManager(authState: existingAuthState)
                if let tokenResponse = tokenResponse {
                    self.notifyListeners("tokenRefresh", data: tokenResponse)
                }
            } else {
                self.clearStoredAuthState()
                self.notifyListeners(
                    "tokenRefreshFailed",
                    data: ["error": error ?? "Failed to refresh stored auth state"]
                )
            }
        }
    }

    private func clearStoredAuthState() {
        authState = nil
        services.authStateStorageService.clearAuthState()
        services.tokenRefreshManagerService.stopTokenRefreshManager()
    }

    deinit {
        removeLifecycleObservers()
        services.tokenRefreshManagerService.stopTokenRefreshManager()
    }
}
