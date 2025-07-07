import AuthenticationServices
import Foundation
import UIKit

// Data structures for Keycloak options
public struct KeycloakOptions {
    let clientId: String
    let authorizationBaseUrl: String
    let responseType: String?
    let redirectUrl: String?
    let accessTokenEndpoint: String?
    let resourceUrl: String?
    let pkceEnabled: Bool
    let scope: String?
    let state: String?
    let additionalParameters: [String: String]?
    let logsEnabled: Bool
    let logoutUrl: String?
    let additionalResourceHeaders: [String: String]?
}

public struct KeycloakRefreshOptions {
    let clientId: String
    let accessTokenEndpoint: String
    let refreshToken: String
}

@objc public class Keycloak: NSObject, ASWebAuthenticationPresentationContextProviding {
    private var session: ASWebAuthenticationSession?

    @objc public func echo(_ value: String) -> String {
        print(value)
        return value
    }

    public func authenticate(
        options: KeycloakOptions, completion: @escaping (Result<[String: Any], Error>) -> Void
    ) {
        // For now, this is a basic implementation
        // In a real implementation, you would use ASWebAuthenticationSession or similar

        print("Keycloak: Starting authentication with clientId: \(options.clientId)")
        print("Keycloak: Base URL: \(options.authorizationBaseUrl)")

        let redirectUri = options.redirectUrl ?? "ca.bc.gov.asago://auth/callback"
        print("Keycloak: Using redirect URI: \(redirectUri)")

        // Build the query string manually to avoid double encoding
        var queryPairs: [String] = []
        queryPairs.append("client_id=\(options.clientId)")
        queryPairs.append("response_type=\(options.responseType ?? "code")")

        // Manually encode just the redirect URI value
        var allowedCharacters = CharacterSet.urlQueryAllowed
        allowedCharacters.remove(charactersIn: ":/")
        if let encodedRedirectUri = redirectUri.addingPercentEncoding(
            withAllowedCharacters: allowedCharacters)
        {
            queryPairs.append("redirect_uri=\(encodedRedirectUri)")
            print("Keycloak: Encoded redirect URI: \(encodedRedirectUri)")
        }

        if let scope = options.scope {
            if let encodedScope = scope.addingPercentEncoding(
                withAllowedCharacters: .urlQueryAllowed)
            {
                queryPairs.append("scope=\(encodedScope)")
            }
        }

        if let state = options.state {
            if let encodedState = state.addingPercentEncoding(
                withAllowedCharacters: .urlQueryAllowed)
            {
                queryPairs.append("state=\(encodedState)")
            }
        }

        let queryString = queryPairs.joined(separator: "&")
        let fullURLString = "\(options.authorizationBaseUrl)?\(queryString)"
        print("Keycloak: Final URL string: \(fullURLString)")

        guard let authURL = URL(string: fullURLString) else {
            completion(
                .failure(
                    NSError(
                        domain: "KeycloakError", code: 1,
                        userInfo: [NSLocalizedDescriptionKey: "Invalid authorization URL"])))
            return
        }

        print("Keycloak: Final authURL: \(authURL.absoluteString)")

        let callbackScheme = URLComponents(
            string: options.redirectUrl ?? "ca.bc.gov.asago://auth/callback")?
            .scheme

        // Ensure UI operations happen on the main thread
        DispatchQueue.main.async {
            let session = ASWebAuthenticationSession(
                url: authURL, callbackURLScheme: callbackScheme
            ) { callbackURL, error in
                if let error = error {
                    print("Keycloak: Authentication error: \(error.localizedDescription)")
                    completion(.failure(error))
                    return
                }

                guard let callbackURL = callbackURL else {
                    completion(
                        .failure(
                            NSError(
                                domain: "KeycloakError", code: 2,
                                userInfo: [NSLocalizedDescriptionKey: "No callback URL received"])))
                    return
                }

                print("Keycloak: Callback URL received: \(callbackURL)")

                // Parse the callback URL and extract all parameters
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

                // Check for errors
                if let error = result["error"] as? String {
                    let errorDescription = result["error_description"] as? String ?? error
                    print("Keycloak: Error from server - error: \(error)")
                    print("Keycloak: Error from server - description: \(errorDescription)")

                    // Provide specific guidance for common errors
                    var userFriendlyMessage = errorDescription
                    if error == "invalid_redirect_uri" {
                        userFriendlyMessage =
                            "The redirect URI '\(options.redirectUrl ?? "ca.bc.gov.asago://auth/callback")' is not configured in the Keycloak client. Please add it to the 'Valid Redirect URIs' in the Keycloak admin console."
                    }

                    completion(
                        .failure(
                            NSError(
                                domain: "KeycloakError", code: 3,
                                userInfo: [
                                    NSLocalizedDescriptionKey: userFriendlyMessage,
                                    "keycloakError": error,
                                    "keycloakErrorDescription": errorDescription,
                                ])))
                    return
                }

                // Return the result (contains code, state, etc.)
                completion(.success(result))
            }
            session.presentationContextProvider = self
            session.start()
            self.session = session
        }

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
