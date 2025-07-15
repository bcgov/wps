import AuthenticationServices
import CryptoKit
import Foundation

protocol PKCEGeneratorProtocol {
    func generateCodeVerifier() -> String
    func generateCodeChallenge(from verifier: String) -> String
}

protocol URLBuilderProtocol {
    func buildAuthorizationURL(options: KeycloakOptions, codeChallenge: String) -> URL?
}

protocol WebAuthSessionProtocol {
    func start(url: URL, callbackScheme: String?, completion: @escaping (URL?, Error?) -> Void)
}

protocol HTTPClientProtocol {
    func performRequest(
        request: URLRequest, completion: @escaping (Data?, URLResponse?, Error?) -> Void)
}

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

class DefaultPKCEGenerator: PKCEGeneratorProtocol {
    func generateCodeVerifier() -> String {
        var buffer = [UInt8](repeating: 0, count: 32)
        _ = SecRandomCopyBytes(kSecRandomDefault, buffer.count, &buffer)
        return Data(buffer).base64URLEncodedString()
    }

    func generateCodeChallenge(from verifier: String) -> String {
        let challenge = Data(verifier.utf8)
        let hash = SHA256.hash(data: challenge)
        return Data(hash).base64URLEncodedString()
    }
}

class DefaultURLBuilder: URLBuilderProtocol {
    func buildAuthorizationURL(options: KeycloakOptions, codeChallenge: String) -> URL? {
        let redirectUri = options.redirectUrl

        // Build the query string manually to avoid double encoding
        var queryPairs: [String] = []
        queryPairs.append("client_id=\(options.clientId)")
        queryPairs.append("response_type=code")

        // Add PKCE parameters
        queryPairs.append("code_challenge=\(codeChallenge)")
        queryPairs.append("code_challenge_method=S256")

        // Manually encode just the redirect URI value
        var allowedCharacters: CharacterSet = CharacterSet.urlQueryAllowed
        allowedCharacters.remove(charactersIn: ":/")
        if let encodedRedirectUri = redirectUri.addingPercentEncoding(
            withAllowedCharacters: allowedCharacters)
        {
            queryPairs.append("redirect_uri=\(encodedRedirectUri)")
        }

        let queryString: String = queryPairs.joined(separator: "&")
        let fullURLString: String = "\(options.authorizationBaseUrl)?\(queryString)"

        return URL(string: fullURLString)
    }
}

class ASWebAuthSessionWrapper: WebAuthSessionProtocol {
    private var session: ASWebAuthenticationSession?
    private weak var presentationContextProvider: ASWebAuthenticationPresentationContextProviding?

    init(presentationContextProvider: ASWebAuthenticationPresentationContextProviding? = nil) {
        self.presentationContextProvider = presentationContextProvider
    }

    func setPresentationContextProvider(
        _ provider: ASWebAuthenticationPresentationContextProviding?
    ) {
        self.presentationContextProvider = provider
    }

    func start(url: URL, callbackScheme: String?, completion: @escaping (URL?, Error?) -> Void) {
        DispatchQueue.main.async {
            self.session = ASWebAuthenticationSession(url: url, callbackURLScheme: callbackScheme) {
                callbackURL, error in
                completion(callbackURL, error)
            }
            self.session?.presentationContextProvider = self.presentationContextProvider
            self.session?.start()
        }
    }
}

class DefaultHTTPClient: HTTPClientProtocol {
    private let session = URLSession.shared

    func performRequest(
        request: URLRequest, completion: @escaping (Data?, URLResponse?, Error?) -> Void
    ) {
        session.dataTask(with: request, completionHandler: completion).resume()
    }
}

@objc public class Keycloak: NSObject, ASWebAuthenticationPresentationContextProviding {
    private var currentCodeVerifier: String?
    private var currentOptions: KeycloakOptions?
    private var refreshTimer: Timer?
    private var autoRefreshOptions:
        (clientId: String, accessTokenEndpoint: String, refreshToken: String)?
    private weak var plugin: KeycloakPlugin?

    private let pkceGenerator: PKCEGeneratorProtocol
    private let urlBuilder: URLBuilderProtocol
    private let webAuthSession: WebAuthSessionProtocol
    private let httpClient: HTTPClientProtocol

    // Default initializer for production use
    public override init() {
        let wrapper: ASWebAuthSessionWrapper = ASWebAuthSessionWrapper()
        self.pkceGenerator = DefaultPKCEGenerator()
        self.urlBuilder = DefaultURLBuilder()
        self.webAuthSession = wrapper
        self.httpClient = DefaultHTTPClient()
        super.init()

        // Set self as presentation context provider after initialization
        wrapper.setPresentationContextProvider(self)
    }

    // Testable initializer with dependency injection
    init(
        pkceGenerator: PKCEGeneratorProtocol,
        urlBuilder: URLBuilderProtocol,
        webAuthSession: WebAuthSessionProtocol,
        httpClient: HTTPClientProtocol
    ) {
        self.pkceGenerator = pkceGenerator
        self.urlBuilder = urlBuilder
        self.webAuthSession = webAuthSession
        self.httpClient = httpClient
        super.init()
    }

    public func setPlugin(_ plugin: KeycloakPlugin) {
        self.plugin = plugin
    }

    public func authenticate(
        options: KeycloakOptions, completion: @escaping (Result<[String: Any], Error>) -> Void
    ) {
        print("Keycloak: Starting authentication with clientId: \(options.clientId)")
        print("Keycloak: Base URL: \(options.authorizationBaseUrl)")
        print("Keycloak: Using redirect URI: \(options.redirectUrl)")

        // Store options for later use in token exchange
        self.currentOptions = options

        // Generate PKCE parameters using injected generator
        let codeVerifier: String = pkceGenerator.generateCodeVerifier()
        let codeChallenge: String = pkceGenerator.generateCodeChallenge(from: codeVerifier)
        print("Keycloak: Generated PKCE code_challenge: \(codeChallenge)")

        // Store the code verifier for later use
        self.currentCodeVerifier = codeVerifier

        // Build authorization URL using injected URL builder
        guard
            let authURL = urlBuilder.buildAuthorizationURL(
                options: options, codeChallenge: codeChallenge)
        else {
            completion(
                .failure(
                    NSError(
                        domain: "KeycloakError",
                        code: 1,
                        userInfo: [NSLocalizedDescriptionKey: "Invalid authorization URL"]
                    )
                ))
            return
        }

        print("Keycloak: Final authURL: \(authURL.absoluteString)")

        let callbackScheme: String? = URLComponents(string: options.redirectUrl)?.scheme

        // Use injected web auth session
        webAuthSession.start(url: authURL, callbackScheme: callbackScheme) {
            [weak self] callbackURL, error in
            self?.handleAuthenticationResponse(
                callbackURL: callbackURL, error: error, completion: completion)
        }
    }

    // Extracted method for handling authentication response - easier to test
    private func handleAuthenticationResponse(
        callbackURL: URL?,
        error: Error?,
        completion: @escaping (Result<[String: Any], Error>) -> Void
    ) {
        if let error = error {
            print("Keycloak: Authentication error: \(error.localizedDescription)")
            completion(.failure(error))
            return
        }

        guard let callbackURL = callbackURL else {
            completion(
                .failure(
                    NSError(
                        domain: "KeycloakError",
                        code: 2,
                        userInfo: [NSLocalizedDescriptionKey: "No callback URL received"]
                    )
                ))
            return
        }

        print("Keycloak: Callback URL received: \(callbackURL)")

        // Parse the callback URL and extract all parameters
        let result = parseCallbackURL(callbackURL)

        // Check for errors in the callback
        if let error = result["error"] as? String {
            let errorDescription = result["error_description"] as? String ?? error
            print("Keycloak: Error from server - error: \(error)")
            print("Keycloak: Error from server - description: \(errorDescription)")

            // Return structured error response instead of throwing
            let errorResponse: [String: Any] = [
                "isAuthenticated": false,
                "redirectUrl": result["redirectUrl"] ?? "",
                "error": error,
                "errorDescription": errorDescription,
            ]

            // Provide specific guidance for common errors
            if error == "invalid_redirect_uri" {
                var enhancedResponse = errorResponse
                enhancedResponse["errorDescription"] =
                    "The redirect URI '\(result["redirect_uri"] ?? "unknown")' is not configured in the Keycloak client. Please add it to the 'Valid Redirect URIs' in the Keycloak admin console."
                completion(.success(enhancedResponse))
            } else {
                completion(.success(errorResponse))
            }
            return
        }

        // Check if we have an authorization code to exchange for tokens
        guard let authorizationCode = result["code"] as? String else {
            // No authorization code found, return unsuccessful authentication
            let failureResponse: [String: Any] = [
                "isAuthenticated": false,
                "redirectUrl": result["redirectUrl"] ?? "",
                "error": result["error"] ?? "No authorization code received",
                "errorDescription": result["error_description"]
                    ?? "Authentication did not complete successfully",
            ]
            completion(.success(failureResponse))
            return
        }

        print("Keycloak: Authorization code received, proceeding with automatic token exchange")
        // Exchange authorization code for tokens using PKCE
        exchangeCodeForTokens(authorizationCode: authorizationCode, completion: completion)
    }

    // Extracted method for parsing callback URL - easier to test
    private func parseCallbackURL(_ callbackURL: URL) -> [String: Any] {
        let components = URLComponents(url: callbackURL, resolvingAgainstBaseURL: false)
        var result: [String: Any] = [
            "redirectUrl": callbackURL.absoluteString
        ]

        if let queryItems = components?.queryItems {
            for item in queryItems {
                if let value = item.value {
                    result[item.name] = value
                }
            }
        }

        return result
    }

    public func refreshToken(
        options: KeycloakRefreshOptions,
        completion: @escaping (Result<[String: Any], Error>) -> Void
    ) {
        print("Keycloak: Refreshing token for clientId: \(options.clientId)")
        print("Keycloak: Token endpoint: \(options.accessTokenEndpoint)")

        guard let url = URL(string: options.accessTokenEndpoint) else {
            completion(
                .failure(
                    NSError(
                        domain: "KeycloakError",
                        code: 11,
                        userInfo: [NSLocalizedDescriptionKey: "Invalid token endpoint URL"]
                    )
                ))
            return
        }

        // Create the refresh token request
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")

        // Build the request body for refresh token grant
        var bodyComponents = URLComponents()
        bodyComponents.queryItems = [
            URLQueryItem(name: "grant_type", value: "refresh_token"),
            URLQueryItem(name: "client_id", value: options.clientId),
            URLQueryItem(name: "refresh_token", value: options.refreshToken),
        ]

        request.httpBody = bodyComponents.percentEncodedQuery?.data(using: .utf8)

        // Perform the refresh token request
        httpClient.performRequest(request: request) { data, response, error in
            if let error = error {
                print("Keycloak: Refresh token network error: \(error.localizedDescription)")
                completion(.failure(error))
                return
            }

            guard let data = data else {
                completion(
                    .failure(
                        NSError(
                            domain: "KeycloakError",
                            code: 12,
                            userInfo: [
                                NSLocalizedDescriptionKey: "No data received from token endpoint"
                            ]
                        )
                    ))
                return
            }

            // Parse the token response
            do {
                if let jsonResponse = try JSONSerialization.jsonObject(with: data, options: [])
                    as? [String: Any]
                {
                    print("Keycloak: Token refresh successful")

                    // Check for errors in the token response
                    if let error = jsonResponse["error"] as? String {
                        let errorDescription = jsonResponse["error_description"] as? String ?? error
                        print("Keycloak: Token refresh error: \(error) - \(errorDescription)")
                        completion(
                            .failure(
                                NSError(
                                    domain: "KeycloakError",
                                    code: 13,
                                    userInfo: [
                                        NSLocalizedDescriptionKey: errorDescription,
                                        "keycloakError": error,
                                        "keycloakErrorDescription": errorDescription,
                                    ]
                                )
                            ))
                        return
                    }

                    // Transform the refresh token response
                    var structuredResponse: [String: Any] = [:]

                    // Map standard OAuth token response fields
                    if let accessToken = jsonResponse["access_token"] as? String {
                        structuredResponse["accessToken"] = accessToken
                    }

                    if let refreshToken = jsonResponse["refresh_token"] as? String {
                        structuredResponse["refreshToken"] = refreshToken
                    }

                    if let tokenType = jsonResponse["token_type"] as? String {
                        structuredResponse["tokenType"] = tokenType
                    }

                    if let expiresIn = jsonResponse["expires_in"] {
                        structuredResponse["expiresIn"] = expiresIn
                    }

                    if let scope = jsonResponse["scope"] as? String {
                        structuredResponse["scope"] = scope
                    }

                    // Include any additional fields from the original response
                    for (key, value) in jsonResponse {
                        if !["access_token", "refresh_token", "token_type", "expires_in", "scope"]
                            .contains(key)
                        {
                            structuredResponse[key] = value
                        }
                    }

                    // Return the structured response
                    completion(.success(structuredResponse))
                } else {
                    completion(
                        .failure(
                            NSError(
                                domain: "KeycloakError",
                                code: 14,
                                userInfo: [
                                    NSLocalizedDescriptionKey:
                                        "Invalid JSON response from token endpoint"
                                ]
                            )
                        ))
                }
            } catch {
                print(
                    "Keycloak: Failed to parse refresh token response JSON: \(error.localizedDescription)"
                )
                completion(.failure(error))
            }
        }
    }

    // Exchange authorization code for tokens using PKCE
    private func exchangeCodeForTokens(
        authorizationCode: String,
        completion: @escaping (Result<[String: Any], Error>) -> Void
    ) {
        guard let options: KeycloakOptions = currentOptions else {
            completion(
                .failure(
                    NSError(
                        domain: "KeycloakError",
                        code: 4,
                        userInfo: [
                            NSLocalizedDescriptionKey:
                                "Missing authentication options for token exchange"
                        ]
                    )
                ))
            return
        }

        // accessTokenEndpoint is now required, so we can use it directly
        let tokenEndpoint: String = options.accessTokenEndpoint

        guard let codeVerifier: String = currentCodeVerifier else {
            completion(
                .failure(
                    NSError(
                        domain: "KeycloakError",
                        code: 6,
                        userInfo: [NSLocalizedDescriptionKey: "Missing PKCE code verifier"]
                    )
                ))
            return
        }

        guard let url: URL = URL(string: tokenEndpoint) else {
            completion(
                .failure(
                    NSError(
                        domain: "KeycloakError",
                        code: 7,
                        userInfo: [NSLocalizedDescriptionKey: "Invalid token endpoint URL"]
                    )
                ))
            return
        }

        print("Keycloak: Exchanging authorization code for tokens")
        print("Keycloak: Token endpoint: \(tokenEndpoint)")

        // Create the token request
        var request: URLRequest = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")

        // Build the request body with PKCE parameters
        var bodyComponents: URLComponents = URLComponents()
        bodyComponents.queryItems = [
            URLQueryItem(name: "grant_type", value: "authorization_code"),
            URLQueryItem(name: "client_id", value: options.clientId),
            URLQueryItem(name: "code", value: authorizationCode),
            URLQueryItem(name: "redirect_uri", value: options.redirectUrl),
            URLQueryItem(name: "code_verifier", value: codeVerifier),
        ]

        request.httpBody = bodyComponents.percentEncodedQuery?.data(using: .utf8)

        // Perform the token exchange request
        httpClient.performRequest(request: request) { [weak self] data, response, error in
            if let error = error {
                print("Keycloak: Token exchange network error: \(error.localizedDescription)")
                completion(.failure(error))
                return
            }

            guard let data: Data = data else {
                completion(
                    .failure(
                        NSError(
                            domain: "KeycloakError",
                            code: 8,
                            userInfo: [
                                NSLocalizedDescriptionKey: "No data received from token endpoint"
                            ]
                        )
                    ))
                return
            }

            // Parse the token response
            do {
                if let jsonResponse: [String: Any] = try JSONSerialization.jsonObject(
                    with: data, options: [])
                    as? [String: Any]
                {
                    print("Keycloak: Token exchange successful")

                    // Check for errors in the token response
                    if let error: String = jsonResponse["error"] as? String {
                        let errorDescription: String =
                            jsonResponse["error_description"] as? String ?? error
                        print("Keycloak: Token exchange error: \(error) - \(errorDescription)")
                        completion(
                            .failure(
                                NSError(
                                    domain: "KeycloakError",
                                    code: 9,
                                    userInfo: [
                                        NSLocalizedDescriptionKey: errorDescription,
                                        "keycloakError": error,
                                        "keycloakErrorDescription": errorDescription,
                                    ]
                                )
                            ))
                        return
                    }

                    // Clear stored values after successful exchange
                    self?.currentCodeVerifier = nil
                    self?.currentOptions = nil

                    // Transform the token response to include isAuthenticated flag
                    var structuredResponse: [String: Any] = [
                        "isAuthenticated": true
                    ]

                    // Map standard OAuth token response fields
                    if let accessToken = jsonResponse["access_token"] as? String {
                        structuredResponse["accessToken"] = accessToken
                    }

                    if let refreshToken = jsonResponse["refresh_token"] as? String {
                        structuredResponse["refreshToken"] = refreshToken
                    }

                    if let idToken = jsonResponse["id_token"] as? String {
                        structuredResponse["idToken"] = idToken
                    }

                    if let tokenType = jsonResponse["token_type"] as? String {
                        structuredResponse["tokenType"] = tokenType
                    }

                    if let expiresIn = jsonResponse["expires_in"] {
                        structuredResponse["expiresIn"] = expiresIn
                    }

                    if let scope = jsonResponse["scope"] as? String {
                        structuredResponse["scope"] = scope
                    }

                    // Include any additional fields from the original response
                    for (key, value) in jsonResponse {
                        if ![
                            "access_token", "refresh_token", "id_token", "token_type", "expires_in",
                            "scope",
                        ].contains(key) {
                            structuredResponse[key] = value
                        }
                    }

                    // Set up automatic token refresh - always enabled
                    if let refreshToken = jsonResponse["refresh_token"] as? String,
                        let expiresIn = jsonResponse["expires_in"] as? Int
                    {
                        self?.scheduleTokenRefresh(
                            clientId: options.clientId,
                            accessTokenEndpoint: options.accessTokenEndpoint,
                            refreshToken: refreshToken,
                            expiresIn: expiresIn
                        )
                    }

                    // Return the structured response
                    completion(.success(structuredResponse))
                } else {
                    completion(
                        .failure(
                            NSError(
                                domain: "KeycloakError",
                                code: 10,
                                userInfo: [
                                    NSLocalizedDescriptionKey:
                                        "Invalid JSON response from token endpoint"
                                ]
                            )
                        ))
                }
            } catch {
                print(
                    "Keycloak: Failed to parse token response JSON: \(error.localizedDescription)")
                completion(.failure(error))
            }
        }
    }

    private func scheduleTokenRefresh(
        clientId: String,
        accessTokenEndpoint: String,
        refreshToken: String,
        expiresIn: Int
    ) {
        // Cancel any existing timer
        refreshTimer?.invalidate()

        // Store refresh options for future refreshes
        autoRefreshOptions = (
            clientId: clientId, accessTokenEndpoint: accessTokenEndpoint, refreshToken: refreshToken
        )

        // Schedule refresh 5 minutes (300 seconds) before expiration
        let bufferTime = 300
        let refreshTime = max(expiresIn - bufferTime, 10)  // Minimum 10 seconds

        print("Keycloak: Scheduling token refresh in \(refreshTime) seconds")

        refreshTimer = Timer.scheduledTimer(
            withTimeInterval: TimeInterval(refreshTime), repeats: false
        ) { [weak self] _ in
            self?.performAutomaticRefresh()
        }
    }

    private func performAutomaticRefresh() {
        guard let options = autoRefreshOptions else {
            print("Keycloak: No auto-refresh options available")
            return
        }

        print("Keycloak: Performing automatic token refresh")

        let refreshOptions = KeycloakRefreshOptions(
            clientId: options.clientId,
            accessTokenEndpoint: options.accessTokenEndpoint,
            refreshToken: options.refreshToken
        )

        refreshToken(options: refreshOptions) { [weak self] result in
            switch result {
            case .success(let response):
                print("Keycloak: Automatic token refresh successful")

                // Create KeycloakTokenResponse object
                let tokenResponse = KeycloakTokenResponse(
                    accessToken: response["accessToken"] as? String ?? "",
                    refreshToken: response["refreshToken"] as? String,
                    tokenType: response["tokenType"] as? String,
                    expiresIn: response["expiresIn"] as? Int,
                    scope: response["scope"] as? String
                )

                // Send event to JavaScript
                DispatchQueue.main.async {
                    self?.plugin?.notifyListeners(
                        "tokenRefresh", data: tokenResponse.toDictionary())
                }

                // Schedule next refresh if we got new tokens
                if let newRefreshToken = response["refreshToken"] as? String,
                    let expiresIn = response["expiresIn"] as? Int
                {
                    self?.scheduleTokenRefresh(
                        clientId: options.clientId,
                        accessTokenEndpoint: options.accessTokenEndpoint,
                        refreshToken: newRefreshToken,
                        expiresIn: expiresIn
                    )
                }

            case .failure(let error):
                print("Keycloak: Automatic token refresh failed: \(error.localizedDescription)")
            }
        }
    }

    public func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor
    {
        // Get the key window from the connected scenes
        guard
            let windowScene = UIApplication.shared.connectedScenes
                .first(where: { $0.activationState == .foregroundActive }) as? UIWindowScene,
            let window = windowScene.windows.first(where: { $0.isKeyWindow })
        else {
            // Fallback to creating a new window if no key window is found
            return UIWindow()
        }
        return window
    }
}

extension Data {
    func base64URLEncodedString() -> String {
        return base64EncodedString()
            .replacingOccurrences(of: "+", with: "-")
            .replacingOccurrences(of: "/", with: "_")
            .replacingOccurrences(of: "=", with: "")
    }
}
