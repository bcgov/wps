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

// MARK: - Data structures for Keycloak options
public struct KeycloakOptions {
    let clientId: String
    let authorizationBaseUrl: String
    let redirectUrl: String
    let accessTokenEndpoint: String?
}

public struct KeycloakRefreshOptions {
    let clientId: String
    let accessTokenEndpoint: String
    let refreshToken: String
}

// MARK: - Concrete Implementations

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
        var allowedCharacters = CharacterSet.urlQueryAllowed
        allowedCharacters.remove(charactersIn: ":/")
        if let encodedRedirectUri = redirectUri.addingPercentEncoding(
            withAllowedCharacters: allowedCharacters)
        {
            queryPairs.append("redirect_uri=\(encodedRedirectUri)")
        }

        let queryString = queryPairs.joined(separator: "&")
        let fullURLString = "\(options.authorizationBaseUrl)?\(queryString)"

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

@objc public class Keycloak: NSObject, ASWebAuthenticationPresentationContextProviding {
    private var currentCodeVerifier: String?

    // Dependencies - can be injected for testing
    private let pkceGenerator: PKCEGeneratorProtocol
    private let urlBuilder: URLBuilderProtocol
    private let webAuthSession: WebAuthSessionProtocol

    // Default initializer for production use
    public override init() {
        let wrapper = ASWebAuthSessionWrapper()
        self.pkceGenerator = DefaultPKCEGenerator()
        self.urlBuilder = DefaultURLBuilder()
        self.webAuthSession = wrapper
        super.init()

        // Set self as presentation context provider after initialization
        wrapper.setPresentationContextProvider(self)
    }

    // Testable initializer with dependency injection
    init(
        pkceGenerator: PKCEGeneratorProtocol,
        urlBuilder: URLBuilderProtocol,
        webAuthSession: WebAuthSessionProtocol
    ) {
        self.pkceGenerator = pkceGenerator
        self.urlBuilder = urlBuilder
        self.webAuthSession = webAuthSession
        super.init()
    }

    @objc public func echo(_ value: String) -> String {
        print(value)
        return value
    }

    public func authenticate(
        options: KeycloakOptions, completion: @escaping (Result<[String: Any], Error>) -> Void
    ) {
        print("Keycloak: Starting authentication with clientId: \(options.clientId)")
        print("Keycloak: Base URL: \(options.authorizationBaseUrl)")
        print("Keycloak: Using redirect URI: \(options.redirectUrl)")

        // Generate PKCE parameters using injected generator
        let codeVerifier = pkceGenerator.generateCodeVerifier()
        let codeChallenge = pkceGenerator.generateCodeChallenge(from: codeVerifier)
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

        let callbackScheme = URLComponents(string: options.redirectUrl)?.scheme

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

            // Provide specific guidance for common errors
            var userFriendlyMessage = errorDescription
            if error == "invalid_redirect_uri" {
                userFriendlyMessage =
                    "The redirect URI '\(result["redirect_uri"] ?? "unknown")' is not configured in the Keycloak client. Please add it to the 'Valid Redirect URIs' in the Keycloak admin console."
            }

            completion(
                .failure(
                    NSError(
                        domain: "KeycloakError",
                        code: 3,
                        userInfo: [
                            NSLocalizedDescriptionKey: userFriendlyMessage,
                            "keycloakError": error,
                            "keycloakErrorDescription": errorDescription,
                        ]
                    )
                ))
            return
        }

        // Return the result (contains code, state, etc.)
        completion(.success(result))
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

        // Include the code verifier for PKCE token exchange
        if let codeVerifier = self.currentCodeVerifier {
            result["codeVerifier"] = codeVerifier
            print("Keycloak: Including code verifier in result for PKCE token exchange")
        }

        return result
    }

    public func refreshToken(
        options: KeycloakRefreshOptions,
        completion: @escaping (Result<[String: Any], Error>) -> Void
    ) {
        // Mock implementation for token refresh
        // In a real implementation, you would make an HTTP request to the token endpoint

        print("Keycloak: Refreshing token for clientId: \(options.clientId)")

        // TODO impl
    }

    // MARK: - ASWebAuthenticationPresentationContextProviding
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

// MARK: - Data Extension for Base64URL Encoding
extension Data {
    func base64URLEncodedString() -> String {
        return base64EncodedString()
            .replacingOccurrences(of: "+", with: "-")
            .replacingOccurrences(of: "/", with: "_")
            .replacingOccurrences(of: "=", with: "")
    }
}
