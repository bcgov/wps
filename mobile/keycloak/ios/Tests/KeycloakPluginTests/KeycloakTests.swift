import AuthenticationServices
import CryptoKit
import Foundation
import XCTest

@testable import KeycloakPlugin

class MockPKCEGenerator: PKCEGeneratorProtocol {
    var codeVerifier: String = "test-code-verifier-123"
    var codeChallenge: String = "test-code-challenge-456"

    func generateCodeVerifier() -> String {
        return codeVerifier
    }

    func generateCodeChallenge(from verifier: String) -> String {
        return codeChallenge
    }
}

class MockURLBuilder: URLBuilderProtocol {
    var shouldReturnNil = false
    var lastOptions: KeycloakOptions?
    var lastCodeChallenge: String?

    func buildAuthorizationURL(options: KeycloakOptions, codeChallenge: String) -> URL? {
        lastOptions = options
        lastCodeChallenge = codeChallenge

        if shouldReturnNil {
            return nil
        }

        return URL(
            string:
                "https://keycloak.example.com/auth?client_id=\(options.clientId)&code_challenge=\(codeChallenge)"
        )
    }
}

class MockWebAuthSession: WebAuthSessionProtocol {
    var shouldCallCompletionWithError = false
    var shouldCallCompletionWithNilURL = false
    var mockCallbackURL: URL?
    var mockError: Error?
    var lastURL: URL?
    var lastCallbackScheme: String??

    func start(url: URL, callbackScheme: String?, completion: @escaping (URL?, Error?) -> Void) {
        lastURL = url
        lastCallbackScheme = callbackScheme

        // Simulate async behavior
        DispatchQueue.main.async {
            if self.shouldCallCompletionWithError {
                completion(
                    nil, self.mockError ?? NSError(domain: "TestError", code: 1, userInfo: nil))
            } else if self.shouldCallCompletionWithNilURL {
                completion(nil, nil)
            } else {
                completion(self.mockCallbackURL, nil)
            }
        }
    }
}

class MockHTTPClient: HTTPClientProtocol {
    var mockResponse: Data?
    var mockError: Error?
    var lastRequest: URLRequest?

    func performRequest(
        request: URLRequest, completion: @escaping (Data?, URLResponse?, Error?) -> Void
    ) {
        lastRequest = request

        // Simulate async behavior
        DispatchQueue.main.async {
            if let error = self.mockError {
                completion(nil, nil, error)
            } else {
                let httpResponse = HTTPURLResponse(
                    url: request.url!,
                    statusCode: 200,
                    httpVersion: nil,
                    headerFields: nil
                )
                completion(self.mockResponse, httpResponse, nil)
            }
        }
    }
}

class KeycloakTests: XCTestCase {

    var keycloak: Keycloak!
    var mockPKCEGenerator: MockPKCEGenerator!
    var mockURLBuilder: MockURLBuilder!
    var mockWebAuthSession: MockWebAuthSession!
    var mockHTTPClient: MockHTTPClient!

    override func setUp() {
        super.setUp()

        mockPKCEGenerator = MockPKCEGenerator()
        mockURLBuilder = MockURLBuilder()
        mockWebAuthSession = MockWebAuthSession()
        mockHTTPClient = MockHTTPClient()

        keycloak = Keycloak(
            pkceGenerator: mockPKCEGenerator,
            urlBuilder: mockURLBuilder,
            webAuthSession: mockWebAuthSession,
            httpClient: mockHTTPClient
        )
    }

    func testSuccessfulAuthentication() {
        // Arrange
        let options = KeycloakOptions(
            clientId: "test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        // Set up mock HTTP response for token exchange
        let mockTokenResponse = """
            {
                "access_token": "mock_access_token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": "mock_refresh_token"
            }
            """.data(using: .utf8)
        mockHTTPClient.mockResponse = mockTokenResponse

        mockWebAuthSession.mockCallbackURL = URL(
            string: "ca.bc.gov.asago://auth/callback?code=test-auth-code&state=test-state")

        let expectation = XCTestExpectation(description: "Authentication should succeed")

        // Act
        keycloak.authenticate(options: options) { result in
            // Assert
            switch result {
            case .success(let data):
                XCTAssertEqual(data["isAuthenticated"] as? Bool, true)
                XCTAssertEqual(data["accessToken"] as? String, "mock_access_token")
                XCTAssertEqual(data["tokenType"] as? String, "Bearer")
                XCTAssertEqual(data["expiresIn"] as? Int, 3600)
                XCTAssertEqual(data["refreshToken"] as? String, "mock_refresh_token")
                expectation.fulfill()
            case .failure(let error):
                XCTFail("Expected success but got error: \(error)")
            }
        }

        wait(for: [expectation], timeout: 1.0)

        // Verify mocks were called correctly
        XCTAssertEqual(mockURLBuilder.lastOptions?.clientId, "test-client")
        XCTAssertEqual(mockURLBuilder.lastCodeChallenge, "test-code-challenge-456")
        XCTAssertNotNil(mockWebAuthSession.lastURL)
    }

    func testAuthenticationWithKeycloakError() {
        // Arrange
        let options = KeycloakOptions(
            clientId: "test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        mockWebAuthSession.mockCallbackURL = URL(
            string:
                "ca.bc.gov.asago://auth/callback?error=invalid_redirect_uri&error_description=Invalid+redirect+URI"
        )

        let expectation = XCTestExpectation(
            description: "Authentication should fail with Keycloak error")

        // Act
        keycloak.authenticate(options: options) { result in
            // Assert
            switch result {
            case .success(let response):
                XCTAssertEqual(response["isAuthenticated"] as? Bool, false)
                XCTAssertEqual(response["error"] as? String, "invalid_redirect_uri")
                XCTAssertNotNil(response["errorDescription"])
                expectation.fulfill()
            case .failure:
                XCTFail("Expected success with error details but got failure")
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

    func testAuthenticationWithSessionError() {
        // Arrange
        let options = KeycloakOptions(
            clientId: "test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        mockWebAuthSession.shouldCallCompletionWithError = true
        mockWebAuthSession.mockError = NSError(
            domain: "TestSessionError", code: 999,
            userInfo: [NSLocalizedDescriptionKey: "Session failed"])

        let expectation = XCTestExpectation(
            description: "Authentication should fail with session error")

        // Act
        keycloak.authenticate(options: options) { result in
            // Assert
            switch result {
            case .success:
                XCTFail("Expected failure but got success")
            case .failure(let error as NSError):
                XCTAssertEqual(error.domain, "TestSessionError")
                XCTAssertEqual(error.code, 999)
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

    func testAuthenticationWithInvalidURL() {
        // Arrange
        let options = KeycloakOptions(
            clientId: "test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        mockURLBuilder.shouldReturnNil = true

        let expectation = XCTestExpectation(
            description: "Authentication should fail with invalid URL")

        // Act
        keycloak.authenticate(options: options) { result in
            // Assert
            switch result {
            case .success:
                XCTFail("Expected failure but got success")
            case .failure(let error as NSError):
                XCTAssertEqual(error.domain, "KeycloakError")
                XCTAssertEqual(error.code, 1)
                XCTAssertTrue(error.localizedDescription.contains("Invalid authorization URL"))
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

    func testPKCEParametersGeneration() {
        // Test that PKCE parameters are generated and used correctly
        let options = KeycloakOptions(
            clientId: "test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        mockWebAuthSession.mockCallbackURL = URL(
            string: "ca.bc.gov.asago://auth/callback?code=test-code")

        let expectation = XCTestExpectation(description: "PKCE parameters should be generated")

        keycloak.authenticate(options: options) { result in
            expectation.fulfill()
        }

        wait(for: [expectation], timeout: 1.0)

        // Verify PKCE parameters were used
        XCTAssertEqual(mockURLBuilder.lastCodeChallenge, "test-code-challenge-456")
    }

    // RefreshToken Tests

    func testSuccessfulRefreshToken() {
        // Arrange
        let options = KeycloakRefreshOptions(
            clientId: "test-client",
            accessTokenEndpoint: "https://keycloak.example.com/token",
            refreshToken: "valid-refresh-token"
        )

        let mockRefreshResponse = """
            {
                "access_token": "new_access_token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": "new_refresh_token",
                "scope": "openid profile"
            }
            """.data(using: .utf8)
        mockHTTPClient.mockResponse = mockRefreshResponse

        let expectation = XCTestExpectation(description: "Refresh token should succeed")

        // Act
        keycloak.refreshToken(options: options) { result in
            // Assert
            switch result {
            case .success(let data):
                XCTAssertEqual(data["accessToken"] as? String, "new_access_token")
                XCTAssertEqual(data["tokenType"] as? String, "Bearer")
                XCTAssertEqual(data["expiresIn"] as? Int, 3600)
                XCTAssertEqual(data["refreshToken"] as? String, "new_refresh_token")
                XCTAssertEqual(data["scope"] as? String, "openid profile")
                expectation.fulfill()
            case .failure(let error):
                XCTFail("Expected success but got error: \(error)")
            }
        }

        wait(for: [expectation], timeout: 1.0)

        // Verify HTTP request was made correctly
        XCTAssertNotNil(mockHTTPClient.lastRequest)
        XCTAssertEqual(mockHTTPClient.lastRequest?.httpMethod, "POST")
        XCTAssertEqual(
            mockHTTPClient.lastRequest?.url?.absoluteString, "https://keycloak.example.com/token")
    }

    func testRefreshTokenWithInvalidEndpoint() {
        // Arrange
        let options = KeycloakRefreshOptions(
            clientId: "test-client",
            accessTokenEndpoint: "invalid-url",
            refreshToken: "valid-refresh-token"
        )

        let expectation = XCTestExpectation(
            description: "Refresh token should fail with invalid URL")

        // Act
        keycloak.refreshToken(options: options) { result in
            // Assert
            switch result {
            case .success:
                XCTFail("Expected failure but got success")
            case .failure(let error as NSError):
                XCTAssertEqual(error.domain, "KeycloakError")
                XCTAssertEqual(error.code, 12)
                XCTAssertTrue(
                    error.localizedDescription.contains("No data received from token endpoint"))
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

    func testRefreshTokenWithNetworkError() {
        // Arrange
        let options = KeycloakRefreshOptions(
            clientId: "test-client",
            accessTokenEndpoint: "https://keycloak.example.com/token",
            refreshToken: "valid-refresh-token"
        )

        mockHTTPClient.mockError = NSError(domain: "NetworkError", code: 500, userInfo: nil)

        let expectation = XCTestExpectation(
            description: "Refresh token should fail with network error")

        // Act
        keycloak.refreshToken(options: options) { result in
            // Assert
            switch result {
            case .success:
                XCTFail("Expected failure but got success")
            case .failure(let error as NSError):
                XCTAssertEqual(error.domain, "NetworkError")
                XCTAssertEqual(error.code, 500)
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

    func testRefreshTokenWithNoData() {
        // Arrange
        let options = KeycloakRefreshOptions(
            clientId: "test-client",
            accessTokenEndpoint: "https://keycloak.example.com/token",
            refreshToken: "valid-refresh-token"
        )

        mockHTTPClient.mockResponse = nil  // No data returned

        let expectation = XCTestExpectation(description: "Refresh token should fail with no data")

        // Act
        keycloak.refreshToken(options: options) { result in
            // Assert
            switch result {
            case .success:
                XCTFail("Expected failure but got success")
            case .failure(let error as NSError):
                XCTAssertEqual(error.domain, "KeycloakError")
                XCTAssertEqual(error.code, 12)
                XCTAssertTrue(
                    error.localizedDescription.contains("No data received from token endpoint"))
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

    func testRefreshTokenWithKeycloakError() {
        // Arrange
        let options = KeycloakRefreshOptions(
            clientId: "test-client",
            accessTokenEndpoint: "https://keycloak.example.com/token",
            refreshToken: "invalid-refresh-token"
        )

        let mockErrorResponse = """
            {
                "error": "invalid_grant",
                "error_description": "Refresh token is invalid or expired"
            }
            """.data(using: .utf8)
        mockHTTPClient.mockResponse = mockErrorResponse

        let expectation = XCTestExpectation(
            description: "Refresh token should fail with Keycloak error")

        // Act
        keycloak.refreshToken(options: options) { result in
            // Assert
            switch result {
            case .success:
                XCTFail("Expected failure but got success")
            case .failure(let error as NSError):
                XCTAssertEqual(error.domain, "KeycloakError")
                XCTAssertEqual(error.code, 13)
                XCTAssertTrue(
                    error.localizedDescription.contains("Refresh token is invalid or expired"))
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

    func testRefreshTokenWithInvalidJSON() {
        // Arrange
        let options = KeycloakRefreshOptions(
            clientId: "test-client",
            accessTokenEndpoint: "https://keycloak.example.com/token",
            refreshToken: "valid-refresh-token"
        )

        mockHTTPClient.mockResponse = "invalid json".data(using: .utf8)

        let expectation = XCTestExpectation(
            description: "Refresh token should fail with invalid JSON")

        // Act
        keycloak.refreshToken(options: options) { result in
            // Assert
            switch result {
            case .success:
                XCTFail("Expected failure but got success")
            case .failure(let error):
                // The JSON parsing error should be from the JSONSerialization
                XCTAssertTrue(
                    error.localizedDescription.contains("format")
                        || error.localizedDescription.contains("JSON")
                        || error.localizedDescription.contains("data"))
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

    // Token Exchange Tests

    func testTokenExchangeWithNetworkError() {
        // Arrange
        let options = KeycloakOptions(
            clientId: "test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        mockWebAuthSession.mockCallbackURL = URL(
            string: "ca.bc.gov.asago://auth/callback?code=test-auth-code")

        mockHTTPClient.mockError = NSError(domain: "NetworkError", code: 404, userInfo: nil)

        let expectation = XCTestExpectation(
            description: "Token exchange should fail with network error")

        // Act
        keycloak.authenticate(options: options) { result in
            // Assert
            switch result {
            case .success:
                XCTFail("Expected failure but got success")
            case .failure(let error as NSError):
                XCTAssertEqual(error.domain, "NetworkError")
                XCTAssertEqual(error.code, 404)
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

    func testTokenExchangeWithInvalidTokenEndpoint() {
        // Arrange
        let options = KeycloakOptions(
            clientId: "test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "invalid-url"
        )

        mockWebAuthSession.mockCallbackURL = URL(
            string: "ca.bc.gov.asago://auth/callback?code=test-auth-code")

        let expectation = XCTestExpectation(
            description: "Token exchange should fail with invalid URL")

        // Act
        keycloak.authenticate(options: options) { result in
            // Assert
            switch result {
            case .success:
                XCTFail("Expected failure but got success")
            case .failure(let error as NSError):
                XCTAssertEqual(error.domain, "KeycloakError")
                XCTAssertEqual(error.code, 8)
                XCTAssertTrue(
                    error.localizedDescription.contains("No data received from token endpoint"))
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

    func testTokenExchangeWithKeycloakError() {
        // Arrange
        let options = KeycloakOptions(
            clientId: "test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        mockWebAuthSession.mockCallbackURL = URL(
            string: "ca.bc.gov.asago://auth/callback?code=invalid-auth-code")

        let mockErrorResponse = """
            {
                "error": "invalid_grant",
                "error_description": "Authorization code is invalid or expired"
            }
            """.data(using: .utf8)
        mockHTTPClient.mockResponse = mockErrorResponse

        let expectation = XCTestExpectation(
            description: "Token exchange should fail with Keycloak error")

        // Act
        keycloak.authenticate(options: options) { result in
            // Assert
            switch result {
            case .success:
                XCTFail("Expected failure but got success")
            case .failure(let error as NSError):
                XCTAssertEqual(error.domain, "KeycloakError")
                XCTAssertEqual(error.code, 9)
                XCTAssertTrue(
                    error.localizedDescription.contains("Authorization code is invalid or expired"))
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

    func testTokenExchangeWithNoData() {
        // Arrange
        let options = KeycloakOptions(
            clientId: "test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        mockWebAuthSession.mockCallbackURL = URL(
            string: "ca.bc.gov.asago://auth/callback?code=test-auth-code")

        mockHTTPClient.mockResponse = nil  // No data returned

        let expectation = XCTestExpectation(description: "Token exchange should fail with no data")

        // Act
        keycloak.authenticate(options: options) { result in
            // Assert
            switch result {
            case .success:
                XCTFail("Expected failure but got success")
            case .failure(let error as NSError):
                XCTAssertEqual(error.domain, "KeycloakError")
                XCTAssertEqual(error.code, 8)
                XCTAssertTrue(
                    error.localizedDescription.contains("No data received from token endpoint"))
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

    func testTokenExchangeWithInvalidJSON() {
        // Arrange
        let options = KeycloakOptions(
            clientId: "test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        mockWebAuthSession.mockCallbackURL = URL(
            string: "ca.bc.gov.asago://auth/callback?code=test-auth-code")

        mockHTTPClient.mockResponse = "invalid json".data(using: .utf8)

        let expectation = XCTestExpectation(
            description: "Token exchange should fail with invalid JSON")

        // Act
        keycloak.authenticate(options: options) { result in
            // Assert
            switch result {
            case .success:
                XCTFail("Expected failure but got success")
            case .failure(let error):
                // The JSON parsing error should be from the JSONSerialization
                XCTAssertTrue(
                    error.localizedDescription.contains("format")
                        || error.localizedDescription.contains("JSON")
                        || error.localizedDescription.contains("data"))
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

    // Callback URL Parsing Tests

    func testCallbackURLWithMissingCode() {
        // Arrange
        let options = KeycloakOptions(
            clientId: "test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        // Callback URL without authorization code
        mockWebAuthSession.mockCallbackURL = URL(
            string: "ca.bc.gov.asago://auth/callback?state=some-state")

        let expectation = XCTestExpectation(
            description: "Authentication should handle missing code")

        // Act
        keycloak.authenticate(options: options) { result in
            // Assert
            switch result {
            case .success(let data):
                XCTAssertEqual(data["isAuthenticated"] as? Bool, false)
                XCTAssertNotNil(data["error"])
                XCTAssertNotNil(data["errorDescription"])
                expectation.fulfill()
            case .failure:
                XCTFail("Expected success with error details but got failure")
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

    func testCallbackURLWithNilURL() {
        // Arrange
        let options = KeycloakOptions(
            clientId: "test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        mockWebAuthSession.shouldCallCompletionWithNilURL = true

        let expectation = XCTestExpectation(
            description: "Authentication should handle nil callback URL")

        // Act
        keycloak.authenticate(options: options) { result in
            // Assert
            switch result {
            case .success:
                XCTFail("Expected failure but got success")
            case .failure(let error as NSError):
                XCTAssertEqual(error.domain, "KeycloakError")
                XCTAssertEqual(error.code, 2)
                XCTAssertTrue(error.localizedDescription.contains("No callback URL received"))
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

    // Additional Error Cases

    func testAuthenticationWithSpecificRedirectURIError() {
        // Arrange
        let options = KeycloakOptions(
            clientId: "test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        mockWebAuthSession.mockCallbackURL = URL(
            string:
                "ca.bc.gov.asago://auth/callback?error=invalid_redirect_uri&error_description=Invalid+redirect+URI&redirect_uri=ca.bc.gov.asago://auth/callback"
        )

        let expectation = XCTestExpectation(
            description: "Authentication should handle invalid redirect URI with enhanced message")

        // Act
        keycloak.authenticate(options: options) { result in
            // Assert
            switch result {
            case .success(let response):
                XCTAssertEqual(response["isAuthenticated"] as? Bool, false)
                XCTAssertEqual(response["error"] as? String, "invalid_redirect_uri")
                let errorDescription = response["errorDescription"] as? String
                XCTAssertNotNil(errorDescription)
                XCTAssertTrue(errorDescription!.contains("Valid Redirect URIs"))
                XCTAssertTrue(errorDescription!.contains("Keycloak admin console"))
                expectation.fulfill()
            case .failure:
                XCTFail("Expected success with error details but got failure")
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

    func testSuccessfulAuthenticationWithAllTokenFields() {
        // Arrange
        let options = KeycloakOptions(
            clientId: "test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        // Set up mock HTTP response with all possible token fields
        let mockTokenResponse = """
            {
                "access_token": "mock_access_token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": "mock_refresh_token",
                "id_token": "mock_id_token",
                "scope": "openid profile email",
                "custom_field": "custom_value"
            }
            """.data(using: .utf8)
        mockHTTPClient.mockResponse = mockTokenResponse

        mockWebAuthSession.mockCallbackURL = URL(
            string: "ca.bc.gov.asago://auth/callback?code=test-auth-code&state=test-state")

        let expectation = XCTestExpectation(
            description: "Authentication should succeed with all fields")

        // Act
        keycloak.authenticate(options: options) { result in
            // Assert
            switch result {
            case .success(let data):
                XCTAssertEqual(data["isAuthenticated"] as? Bool, true)
                XCTAssertEqual(data["accessToken"] as? String, "mock_access_token")
                XCTAssertEqual(data["tokenType"] as? String, "Bearer")
                XCTAssertEqual(data["expiresIn"] as? Int, 3600)
                XCTAssertEqual(data["refreshToken"] as? String, "mock_refresh_token")
                XCTAssertEqual(data["idToken"] as? String, "mock_id_token")
                XCTAssertEqual(data["scope"] as? String, "openid profile email")
                XCTAssertEqual(data["custom_field"] as? String, "custom_value")
                expectation.fulfill()
            case .failure(let error):
                XCTFail("Expected success but got error: \(error)")
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

    // Presentation Anchor Tests

    func testPresentationAnchor() {
        // This test verifies that the presentationAnchor method returns a valid window
        // Note: This is a basic test as we can't easily mock UIApplication in unit tests
        let keycloakInstance = Keycloak()

        // Create a minimal mock session that conforms to ASWebAuthenticationSession
        class MockASWebAuthSession: ASWebAuthenticationSession {
            init() {
                super.init(url: URL(string: "https://example.com")!, callbackURLScheme: "test") {
                    _, _ in
                }
            }
        }

        let mockSession = MockASWebAuthSession()
        let anchor = keycloakInstance.presentationAnchor(for: mockSession)
        XCTAssertNotNil(anchor)
        XCTAssertTrue(anchor is UIWindow)
    }
}

// KeycloakTokenResponse Tests

class KeycloakTokenResponseTests: XCTestCase {

    func testTokenResponseToDictionaryWithAllFields() {
        // Arrange
        let tokenResponse = KeycloakTokenResponse(
            accessToken: "test_access_token",
            refreshToken: "test_refresh_token",
            tokenType: "Bearer",
            expiresIn: 3600,
            scope: "openid profile"
        )

        // Act
        let dictionary = tokenResponse.toDictionary()

        // Assert
        XCTAssertEqual(dictionary["accessToken"] as? String, "test_access_token")
        XCTAssertEqual(dictionary["refreshToken"] as? String, "test_refresh_token")
        XCTAssertEqual(dictionary["tokenType"] as? String, "Bearer")
        XCTAssertEqual(dictionary["expiresIn"] as? Int, 3600)
        XCTAssertEqual(dictionary["scope"] as? String, "openid profile")
    }

    func testTokenResponseToDictionaryWithMinimalFields() {
        // Arrange
        let tokenResponse = KeycloakTokenResponse(
            accessToken: "test_access_token",
            refreshToken: nil,
            tokenType: nil,
            expiresIn: nil,
            scope: nil
        )

        // Act
        let dictionary = tokenResponse.toDictionary()

        // Assert
        XCTAssertEqual(dictionary["accessToken"] as? String, "test_access_token")
        XCTAssertNil(dictionary["refreshToken"])
        XCTAssertNil(dictionary["tokenType"])
        XCTAssertNil(dictionary["expiresIn"])
        XCTAssertNil(dictionary["scope"])
        XCTAssertEqual(dictionary.count, 1)  // Only accessToken should be present
    }

    func testTokenResponseToDictionaryWithPartialFields() {
        // Arrange
        let tokenResponse = KeycloakTokenResponse(
            accessToken: "test_access_token",
            refreshToken: "test_refresh_token",
            tokenType: nil,
            expiresIn: 1800,
            scope: nil
        )

        // Act
        let dictionary = tokenResponse.toDictionary()

        // Assert
        XCTAssertEqual(dictionary["accessToken"] as? String, "test_access_token")
        XCTAssertEqual(dictionary["refreshToken"] as? String, "test_refresh_token")
        XCTAssertNil(dictionary["tokenType"])
        XCTAssertEqual(dictionary["expiresIn"] as? Int, 1800)
        XCTAssertNil(dictionary["scope"])
        XCTAssertEqual(dictionary.count, 3)  // accessToken, refreshToken, expiresIn
    }
}

// Data Extension Tests

class DataExtensionTests: XCTestCase {

    func testBase64URLEncodedString() {
        // Test basic encoding
        let testString = "Hello, World!"
        let data = testString.data(using: .utf8)!
        let base64URL = data.base64URLEncodedString()

        // Should not contain +, /, or =
        XCTAssertFalse(base64URL.contains("+"))
        XCTAssertFalse(base64URL.contains("/"))
        XCTAssertFalse(base64URL.contains("="))

        // Should contain - and _ instead
        // Test with data that would normally produce + and /
        let testData = Data([0xFF, 0xFE, 0xFD])
        let encoded = testData.base64URLEncodedString()

        XCTAssertFalse(encoded.contains("+"))
        XCTAssertFalse(encoded.contains("/"))
        XCTAssertFalse(encoded.contains("="))
    }

    func testBase64URLEncodingReplacements() {
        // Create data that will result in standard base64 characters that need replacement
        let testData = Data([0x3E, 0x3F, 0x40])  // This should produce '+' and '/' in standard base64
        let standardBase64 = testData.base64EncodedString()
        let base64URL = testData.base64URLEncodedString()

        // Verify that our implementation replaces the characters correctly
        let expectedBase64URL =
            standardBase64
            .replacingOccurrences(of: "+", with: "-")
            .replacingOccurrences(of: "/", with: "_")
            .replacingOccurrences(of: "=", with: "")

        XCTAssertEqual(base64URL, expectedBase64URL)
    }
}

// Integration Tests

class KeycloakIntegrationTests: XCTestCase {

    func testCompleteAuthenticationFlow() {
        // This test verifies the complete flow from start to finish
        let mockPKCEGenerator = MockPKCEGenerator()
        let mockURLBuilder = MockURLBuilder()
        let mockWebAuthSession = MockWebAuthSession()
        let mockHTTPClient = MockHTTPClient()

        let keycloak = Keycloak(
            pkceGenerator: mockPKCEGenerator,
            urlBuilder: mockURLBuilder,
            webAuthSession: mockWebAuthSession,
            httpClient: mockHTTPClient
        )

        let options = KeycloakOptions(
            clientId: "integration-test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        // Set up the complete flow
        mockWebAuthSession.mockCallbackURL = URL(
            string: "ca.bc.gov.asago://auth/callback?code=integration-auth-code&state=test-state")

        let mockTokenResponse = """
            {
                "access_token": "integration_access_token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": "integration_refresh_token",
                "scope": "openid profile email"
            }
            """.data(using: .utf8)
        mockHTTPClient.mockResponse = mockTokenResponse

        let expectation = XCTestExpectation(
            description: "Complete authentication flow should succeed")

        // Act
        keycloak.authenticate(options: options) { result in
            // Assert
            switch result {
            case .success(let data):
                XCTAssertEqual(data["isAuthenticated"] as? Bool, true)
                XCTAssertEqual(data["accessToken"] as? String, "integration_access_token")
                XCTAssertEqual(data["refreshToken"] as? String, "integration_refresh_token")

                // Verify all the mock interactions happened correctly
                XCTAssertEqual(mockURLBuilder.lastOptions?.clientId, "integration-test-client")
                XCTAssertEqual(mockURLBuilder.lastCodeChallenge, "test-code-challenge-456")
                XCTAssertNotNil(mockWebAuthSession.lastURL)
                XCTAssertNotNil(mockHTTPClient.lastRequest)
                XCTAssertEqual(mockHTTPClient.lastRequest?.httpMethod, "POST")

                expectation.fulfill()
            case .failure(let error):
                XCTFail("Expected success but got error: \(error)")
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }
}

class DefaultPKCEGeneratorTests: XCTestCase {

    var pkceGenerator: DefaultPKCEGenerator!

    override func setUp() {
        super.setUp()
        pkceGenerator = DefaultPKCEGenerator()
    }

    func testGenerateCodeVerifierLength() {
        // Act
        let codeVerifier = pkceGenerator.generateCodeVerifier()

        // Assert
        // Base64URL encoded 32 bytes should be 43 characters (without padding)
        // 32 bytes * 8 bits/byte = 256 bits
        // 256 bits / 6 bits per base64 char = 42.67, rounded up to 43 chars
        XCTAssertEqual(codeVerifier.count, 43)
    }

    func testGenerateCodeVerifierFormat() {
        // Act
        let codeVerifier = pkceGenerator.generateCodeVerifier()

        // Assert
        // Should only contain URL-safe base64 characters: A-Z, a-z, 0-9, -, _
        let allowedCharacters = CharacterSet(
            charactersIn: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
        let codeVerifierCharacterSet = CharacterSet(charactersIn: codeVerifier)

        XCTAssertTrue(allowedCharacters.isSuperset(of: codeVerifierCharacterSet))

        // Should not contain standard base64 characters that are replaced in base64URL
        XCTAssertFalse(codeVerifier.contains("+"))
        XCTAssertFalse(codeVerifier.contains("/"))
        XCTAssertFalse(codeVerifier.contains("="))
    }

    func testGenerateCodeVerifierUniqueness() {
        // Act
        let codeVerifier1 = pkceGenerator.generateCodeVerifier()
        let codeVerifier2 = pkceGenerator.generateCodeVerifier()
        let codeVerifier3 = pkceGenerator.generateCodeVerifier()

        // Assert
        // Each call should generate a unique code verifier due to random generation
        XCTAssertNotEqual(codeVerifier1, codeVerifier2)
        XCTAssertNotEqual(codeVerifier2, codeVerifier3)
        XCTAssertNotEqual(codeVerifier1, codeVerifier3)
    }

    func testGenerateCodeVerifierConsistentLength() {
        // Act & Assert
        // Generate multiple code verifiers and ensure they all have the same length
        for _ in 0..<10 {
            let codeVerifier = pkceGenerator.generateCodeVerifier()
            XCTAssertEqual(codeVerifier.count, 43)
        }
    }

    func testGenerateCodeVerifierNotEmpty() {
        // Act
        let codeVerifier = pkceGenerator.generateCodeVerifier()

        // Assert
        XCTAssertFalse(codeVerifier.isEmpty)
        XCTAssertGreaterThan(codeVerifier.count, 0)
    }

    func testGenerateCodeVerifierCryptographicStrength() {
        // This test verifies that the generated code verifiers have good entropy
        // by checking that multiple generations don't have obvious patterns

        // Act
        var codeVerifiers = Set<String>()
        let generationCount = 100

        for _ in 0..<generationCount {
            let codeVerifier = pkceGenerator.generateCodeVerifier()
            codeVerifiers.insert(codeVerifier)
        }

        // Assert
        // All generated code verifiers should be unique (high entropy)
        XCTAssertEqual(codeVerifiers.count, generationCount)
    }

    func testGenerateCodeVerifierBase64URLCompliance() {
        // Act
        let codeVerifier = pkceGenerator.generateCodeVerifier()

        // Assert
        // Should be decodable as base64URL
        // Add padding if needed for standard base64 decoding
        let paddedCodeVerifier = codeVerifier.padding(
            toLength: ((codeVerifier.count + 3) / 4) * 4, withPad: "=", startingAt: 0)
        let standardBase64 =
            paddedCodeVerifier
            .replacingOccurrences(of: "-", with: "+")
            .replacingOccurrences(of: "_", with: "/")

        let decodedData = Data(base64Encoded: standardBase64)
        XCTAssertNotNil(decodedData)
        XCTAssertEqual(decodedData?.count, 32)  // Should decode to 32 bytes
    }

    func testGenerateCodeVerifierRFC7636Compliance() {
        // Per RFC 7636, code verifier must be 43-128 characters long
        // and use unreserved characters A-Z, a-z, 0-9, -, ., _, ~

        // Act
        let codeVerifier = pkceGenerator.generateCodeVerifier()

        // Assert
        XCTAssertGreaterThanOrEqual(codeVerifier.count, 43)
        XCTAssertLessThanOrEqual(codeVerifier.count, 128)

        // Check for RFC 7636 unreserved characters
        // Note: Our implementation uses base64URL which is a subset of unreserved characters
        let rfc7636UnreservedChars = CharacterSet(
            charactersIn: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")
        let codeVerifierCharacterSet = CharacterSet(charactersIn: codeVerifier)

        XCTAssertTrue(rfc7636UnreservedChars.isSuperset(of: codeVerifierCharacterSet))
    }

    func testGenerateCodeChallengeBasicFunctionality() {
        // Arrange
        let codeVerifier = "test-code-verifier-123"

        // Act
        let codeChallenge = pkceGenerator.generateCodeChallenge(from: codeVerifier)

        // Assert
        XCTAssertFalse(codeChallenge.isEmpty)
        XCTAssertNotEqual(codeChallenge, codeVerifier)  // Should be different from input
        XCTAssertEqual(codeChallenge.count, 43)  // SHA256 hash base64URL encoded should be 43 chars
    }

    func testGenerateCodeChallengeConsistency() {
        // Arrange
        let codeVerifier = "test-code-verifier-123"

        // Act
        let codeChallenge1 = pkceGenerator.generateCodeChallenge(from: codeVerifier)
        let codeChallenge2 = pkceGenerator.generateCodeChallenge(from: codeVerifier)

        // Assert
        // Same input should always produce the same output (deterministic)
        XCTAssertEqual(codeChallenge1, codeChallenge2)
    }

    func testGenerateCodeChallengeDifferentInputs() {
        // Arrange
        let codeVerifier1 = "test-code-verifier-1"
        let codeVerifier2 = "test-code-verifier-2"

        // Act
        let codeChallenge1 = pkceGenerator.generateCodeChallenge(from: codeVerifier1)
        let codeChallenge2 = pkceGenerator.generateCodeChallenge(from: codeVerifier2)

        // Assert
        // Different inputs should produce different outputs
        XCTAssertNotEqual(codeChallenge1, codeChallenge2)
    }

    func testGenerateCodeChallengeFormat() {
        // Arrange
        let codeVerifier = "test-code-verifier-123"

        // Act
        let codeChallenge = pkceGenerator.generateCodeChallenge(from: codeVerifier)

        // Assert
        // Should only contain URL-safe base64 characters: A-Z, a-z, 0-9, -, _
        let allowedCharacters = CharacterSet(
            charactersIn: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
        let codeChallengeCharacterSet = CharacterSet(charactersIn: codeChallenge)

        XCTAssertTrue(allowedCharacters.isSuperset(of: codeChallengeCharacterSet))

        // Should not contain standard base64 characters that are replaced in base64URL
        XCTAssertFalse(codeChallenge.contains("+"))
        XCTAssertFalse(codeChallenge.contains("/"))
        XCTAssertFalse(codeChallenge.contains("="))
    }

    func testGenerateCodeChallengeLength() {
        // Arrange
        let shortVerifier = "abc"
        let longVerifier = "a" + String(repeating: "b", count: 100) + "c"

        // Act
        let shortChallenge = pkceGenerator.generateCodeChallenge(from: shortVerifier)
        let longChallenge = pkceGenerator.generateCodeChallenge(from: longVerifier)

        // Assert
        // SHA256 hash should always produce the same length output regardless of input length
        XCTAssertEqual(shortChallenge.count, 43)
        XCTAssertEqual(longChallenge.count, 43)
        XCTAssertNotEqual(shortChallenge, longChallenge)
    }

    func testGenerateCodeChallengeEmptyInput() {
        // Arrange
        let emptyVerifier = ""

        // Act
        let codeChallenge = pkceGenerator.generateCodeChallenge(from: emptyVerifier)

        // Assert
        // Should handle empty input gracefully
        XCTAssertFalse(codeChallenge.isEmpty)
        XCTAssertEqual(codeChallenge.count, 43)
    }

    func testGenerateCodeChallengeUnicodeInput() {
        // Arrange
        let unicodeVerifier = "test-验证码-🔐-challénge"

        // Act
        let codeChallenge = pkceGenerator.generateCodeChallenge(from: unicodeVerifier)

        // Assert
        // Should handle Unicode characters properly
        XCTAssertFalse(codeChallenge.isEmpty)
        XCTAssertEqual(codeChallenge.count, 43)

        // Should be consistent
        let secondChallenge = pkceGenerator.generateCodeChallenge(from: unicodeVerifier)
        XCTAssertEqual(codeChallenge, secondChallenge)
    }

    func testGenerateCodeChallengeSHA256Correctness() {
        // Arrange
        let knownVerifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"

        // Act
        let codeChallenge = pkceGenerator.generateCodeChallenge(from: knownVerifier)

        // Assert
        // Verify the SHA256 hash is correctly computed and base64URL encoded
        // We can verify this by manually calculating the expected result
        let expectedData = Data(knownVerifier.utf8)
        let expectedHash = SHA256.hash(data: expectedData)
        let expectedChallenge = Data(expectedHash).base64URLEncodedString()

        XCTAssertEqual(codeChallenge, expectedChallenge)
    }

    func testGenerateCodeChallengeRFC7636Compliance() {
        // Arrange
        let codeVerifier = "test-code-verifier-for-rfc-compliance"

        // Act
        let codeChallenge = pkceGenerator.generateCodeChallenge(from: codeVerifier)

        // Assert
        // Per RFC 7636, code challenge should be base64URL encoded SHA256 hash
        // Length should be 43 characters (256 bits / 6 bits per base64 char = 42.67, rounded up)
        XCTAssertEqual(codeChallenge.count, 43)

        // Should be URL-safe (no +, /, =)
        XCTAssertFalse(codeChallenge.contains("+"))
        XCTAssertFalse(codeChallenge.contains("/"))
        XCTAssertFalse(codeChallenge.contains("="))

        // Should be decodable back to 32 bytes (SHA256 output size)
        let paddedChallenge = codeChallenge.padding(
            toLength: ((codeChallenge.count + 3) / 4) * 4, withPad: "=", startingAt: 0)
        let standardBase64 =
            paddedChallenge
            .replacingOccurrences(of: "-", with: "+")
            .replacingOccurrences(of: "_", with: "/")

        let decodedData = Data(base64Encoded: standardBase64)
        XCTAssertNotNil(decodedData)
        XCTAssertEqual(decodedData?.count, 32)  // SHA256 produces 32 bytes
    }

    func testGenerateCodeChallengeWithGeneratedVerifier() {
        // Integration test: Use a generated code verifier to create a challenge

        // Arrange
        let generatedVerifier = pkceGenerator.generateCodeVerifier()

        // Act
        let codeChallenge = pkceGenerator.generateCodeChallenge(from: generatedVerifier)

        // Assert
        XCTAssertFalse(codeChallenge.isEmpty)
        XCTAssertEqual(codeChallenge.count, 43)
        XCTAssertNotEqual(codeChallenge, generatedVerifier)

        // Should be reproducible
        let secondChallenge = pkceGenerator.generateCodeChallenge(from: generatedVerifier)
        XCTAssertEqual(codeChallenge, secondChallenge)
    }
}
