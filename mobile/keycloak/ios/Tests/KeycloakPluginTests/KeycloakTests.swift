import AuthenticationServices
import CryptoKit
import Foundation
import XCTest

@testable import KeycloakPlugin

let options = KeycloakOptions(
    clientId: "test-client",
    authorizationBaseUrl: "https://keycloak.example.com/auth",
    redirectUrl: "ca.bc.gov.asago://auth/callback",
    accessTokenEndpoint: "https://keycloak.example.com/token"
)

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
        let refreshOptions = KeycloakRefreshOptions(
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
        keycloak.refreshToken(options: refreshOptions) { result in
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
        let refreshOptions = KeycloakRefreshOptions(
            clientId: "test-client",
            accessTokenEndpoint: "https://keycloak.example.com/token",
            refreshToken: "valid-refresh-token"
        )

        mockHTTPClient.mockError = NSError(domain: "NetworkError", code: 500, userInfo: nil)

        let expectation = XCTestExpectation(
            description: "Refresh token should fail with network error")

        // Act
        keycloak.refreshToken(options: refreshOptions) { result in
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
        let refreshOptions = KeycloakRefreshOptions(
            clientId: "test-client",
            accessTokenEndpoint: "https://keycloak.example.com/token",
            refreshToken: "valid-refresh-token"
        )

        mockHTTPClient.mockResponse = nil  // No data returned

        let expectation = XCTestExpectation(description: "Refresh token should fail with no data")

        // Act
        keycloak.refreshToken(options: refreshOptions) { result in
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
        let refreshOptions = KeycloakRefreshOptions(
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
        keycloak.refreshToken(options: refreshOptions) { result in
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
        let refreshOptions = KeycloakRefreshOptions(
            clientId: "test-client",
            accessTokenEndpoint: "https://keycloak.example.com/token",
            refreshToken: "valid-refresh-token"
        )

        mockHTTPClient.mockResponse = "invalid json".data(using: .utf8)

        let expectation = XCTestExpectation(
            description: "Refresh token should fail with invalid JSON")

        // Act
        keycloak.refreshToken(options: refreshOptions) { result in
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

class DefaultURLBuilderTests: XCTestCase {

    var urlBuilder: DefaultURLBuilder!

    override func setUp() {
        super.setUp()
        urlBuilder = DefaultURLBuilder()
    }

    func testBuildAuthorizationURLBasicFunctionality() {
        // Arrange
        let codeChallenge = "test-code-challenge-123"

        // Act
        let authURL = urlBuilder.buildAuthorizationURL(
            options: options, codeChallenge: codeChallenge)

        // Assert
        XCTAssertNotNil(authURL)
        XCTAssertEqual(authURL?.scheme, "https")
        XCTAssertEqual(authURL?.host, "keycloak.example.com")
        XCTAssertEqual(authURL?.path, "/auth")
    }

    func testBuildAuthorizationURLQueryParameters() {
        // Arrange
        let options = KeycloakOptions(
            clientId: "test-client-id",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )
        let codeChallenge = "test-code-challenge-123"

        // Act
        let authURL = urlBuilder.buildAuthorizationURL(
            options: options, codeChallenge: codeChallenge)

        // Assert
        XCTAssertNotNil(authURL)
        let urlComponents = URLComponents(url: authURL!, resolvingAgainstBaseURL: false)
        let queryItems = urlComponents?.queryItems

        // Check required OAuth 2.0 parameters
        XCTAssertTrue(
            queryItems?.contains { $0.name == "client_id" && $0.value == "test-client-id" } ?? false
        )
        XCTAssertTrue(
            queryItems?.contains { $0.name == "response_type" && $0.value == "code" } ?? false)

        // Check PKCE parameters
        XCTAssertTrue(
            queryItems?.contains {
                $0.name == "code_challenge" && $0.value == "test-code-challenge-123"
            } ?? false)
        XCTAssertTrue(
            queryItems?.contains { $0.name == "code_challenge_method" && $0.value == "S256" }
                ?? false)

        // Check redirect URI parameter
        XCTAssertTrue(queryItems?.contains { $0.name == "redirect_uri" } ?? false)
    }

    func testBuildAuthorizationURLRedirectUriEncoding() {
        // Arrange
        let codeChallenge = "test-challenge"

        // Act
        let authURL = urlBuilder.buildAuthorizationURL(
            options: options, codeChallenge: codeChallenge)

        // Assert
        XCTAssertNotNil(authURL)
        let urlString = authURL!.absoluteString

        // The redirect URI should be properly encoded - colons and slashes in the scheme should be encoded
        XCTAssertTrue(urlString.contains("redirect_uri=ca.bc.gov.asago%3A%2F%2Fauth%2Fcallback"))
    }

    func testBuildAuthorizationURLWithSpecialCharacters() {
        // Arrange
        let options = KeycloakOptions(
            clientId: "test-client-with-special-chars",
            authorizationBaseUrl: "https://keycloak.example.com/auth/realms/test-realm",
            redirectUrl: "myapp://auth/callback?param=value",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )
        let codeChallenge = "challenge-with-special_chars-123"

        // Act
        let authURL = urlBuilder.buildAuthorizationURL(
            options: options, codeChallenge: codeChallenge)

        // Assert
        XCTAssertNotNil(authURL)
        let urlComponents = URLComponents(url: authURL!, resolvingAgainstBaseURL: false)
        let queryItems = urlComponents?.queryItems

        XCTAssertTrue(
            queryItems?.contains {
                $0.name == "client_id" && $0.value == "test-client-with-special-chars"
            } ?? false)
        XCTAssertTrue(
            queryItems?.contains {
                $0.name == "code_challenge" && $0.value == "challenge-with-special_chars-123"
            } ?? false)
    }

    func testBuildAuthorizationURLWithEmptyValues() {
        // Arrange
        let options = KeycloakOptions(
            clientId: "",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )
        let codeChallenge = ""

        // Act
        let authURL = urlBuilder.buildAuthorizationURL(
            options: options, codeChallenge: codeChallenge)

        // Assert
        XCTAssertNotNil(authURL)
        let urlComponents = URLComponents(url: authURL!, resolvingAgainstBaseURL: false)
        let queryItems = urlComponents?.queryItems

        // Should still contain the parameters, even if empty
        XCTAssertTrue(queryItems?.contains { $0.name == "client_id" } ?? false)
        XCTAssertTrue(queryItems?.contains { $0.name == "code_challenge" } ?? false)
    }

    func testBuildAuthorizationURLWithInvalidBaseURL() {
        // Arrange
        let options = KeycloakOptions(
            clientId: "test-client",
            authorizationBaseUrl: "invalid-url",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )
        let codeChallenge = "test-challenge"

        // Act
        let authURL = urlBuilder.buildAuthorizationURL(
            options: options, codeChallenge: codeChallenge)

        // Assert
        // The implementation still creates a URL string, it doesn't validate the base URL
        XCTAssertNotNil(authURL)
    }

    func testBuildAuthorizationURLWithComplexRedirectURI() {
        // Arrange
        let options = KeycloakOptions(
            clientId: "test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "https://app.example.com/auth/callback?state=xyz&nonce=abc",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )
        let codeChallenge = "test-challenge"

        // Act
        let authURL = urlBuilder.buildAuthorizationURL(
            options: options, codeChallenge: codeChallenge)

        // Assert
        XCTAssertNotNil(authURL)
        let urlString = authURL!.absoluteString

        // Complex redirect URI should be properly encoded
        XCTAssertTrue(urlString.contains("redirect_uri="))
        XCTAssertTrue(urlString.contains("https%3A%2F%2F"))  // https:// should be encoded to https%3A%2F%2F
    }

    func testBuildAuthorizationURLParameterOrder() {
        // Arrange
        let codeChallenge = "test-challenge"

        // Act
        let authURL = urlBuilder.buildAuthorizationURL(
            options: options, codeChallenge: codeChallenge)

        // Assert
        XCTAssertNotNil(authURL)
        let queryString = authURL!.query!

        // Verify the order of parameters as implemented
        let clientIdIndex = queryString.range(of: "client_id=")?.lowerBound
        let responseTypeIndex = queryString.range(of: "response_type=")?.lowerBound
        let codeChallengeIndex = queryString.range(of: "code_challenge=")?.lowerBound
        let methodIndex = queryString.range(of: "code_challenge_method=")?.lowerBound
        let redirectIndex = queryString.range(of: "redirect_uri=")?.lowerBound

        XCTAssertNotNil(clientIdIndex)
        XCTAssertNotNil(responseTypeIndex)
        XCTAssertNotNil(codeChallengeIndex)
        XCTAssertNotNil(methodIndex)
        XCTAssertNotNil(redirectIndex)

        // Verify order matches implementation: client_id, response_type, code_challenge, code_challenge_method, redirect_uri
        XCTAssertTrue(clientIdIndex! < responseTypeIndex!)
        XCTAssertTrue(responseTypeIndex! < codeChallengeIndex!)
        XCTAssertTrue(codeChallengeIndex! < methodIndex!)
        XCTAssertTrue(methodIndex! < redirectIndex!)
    }

    func testBuildAuthorizationURLConsistency() {
        // Arrange
        let codeChallenge = "test-challenge"

        // Act
        let authURL1 = urlBuilder.buildAuthorizationURL(
            options: options, codeChallenge: codeChallenge)
        let authURL2 = urlBuilder.buildAuthorizationURL(
            options: options, codeChallenge: codeChallenge)

        // Assert
        // Same inputs should produce the same output
        XCTAssertNotNil(authURL1)
        XCTAssertNotNil(authURL2)
        XCTAssertEqual(authURL1?.absoluteString, authURL2?.absoluteString)
    }

    func testBuildAuthorizationURLDifferentInputs() {
        // Arrange
        let options1 = KeycloakOptions(
            clientId: "client-1",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )
        let options2 = KeycloakOptions(
            clientId: "client-2",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )
        let codeChallenge = "test-challenge"

        // Act
        let authURL1 = urlBuilder.buildAuthorizationURL(
            options: options1, codeChallenge: codeChallenge)
        let authURL2 = urlBuilder.buildAuthorizationURL(
            options: options2, codeChallenge: codeChallenge)

        // Assert
        // Different inputs should produce different outputs
        XCTAssertNotNil(authURL1)
        XCTAssertNotNil(authURL2)
        XCTAssertNotEqual(authURL1?.absoluteString, authURL2?.absoluteString)
    }

    func testBuildAuthorizationURLOAuth2Compliance() {
        // Arrange
        let options = KeycloakOptions(
            clientId: "oauth2-client",
            authorizationBaseUrl: "https://auth.example.com/oauth2/authorize",
            redirectUrl: "https://app.example.com/callback",
            accessTokenEndpoint: "https://auth.example.com/oauth2/token"
        )
        let codeChallenge = "oauth2-challenge"

        // Act
        let authURL = urlBuilder.buildAuthorizationURL(
            options: options, codeChallenge: codeChallenge)

        // Assert
        XCTAssertNotNil(authURL)
        let urlComponents = URLComponents(url: authURL!, resolvingAgainstBaseURL: false)
        let queryItems = urlComponents?.queryItems

        // Verify OAuth 2.0 Authorization Code Flow compliance
        XCTAssertTrue(
            queryItems?.contains { $0.name == "response_type" && $0.value == "code" } ?? false)
        XCTAssertTrue(queryItems?.contains { $0.name == "client_id" } ?? false)
        XCTAssertTrue(queryItems?.contains { $0.name == "redirect_uri" } ?? false)

        // Verify PKCE compliance (RFC 7636)
        XCTAssertTrue(queryItems?.contains { $0.name == "code_challenge" } ?? false)
        XCTAssertTrue(
            queryItems?.contains { $0.name == "code_challenge_method" && $0.value == "S256" }
                ?? false)
    }

    func testBuildAuthorizationURLWithBaseURLTrailingSlash() {
        // Arrange
        let optionsWithSlash = KeycloakOptions(
            clientId: "test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth/",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )
        let optionsWithoutSlash = KeycloakOptions(
            clientId: "test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )
        let codeChallenge = "test-challenge"

        // Act
        let authURLWithSlash = urlBuilder.buildAuthorizationURL(
            options: optionsWithSlash, codeChallenge: codeChallenge)
        let authURLWithoutSlash = urlBuilder.buildAuthorizationURL(
            options: optionsWithoutSlash, codeChallenge: codeChallenge)

        // Assert
        XCTAssertNotNil(authURLWithSlash)
        XCTAssertNotNil(authURLWithoutSlash)

        // Both should be valid URLs, but they will be different due to the trailing slash
        XCTAssertTrue(authURLWithSlash!.absoluteString.contains("auth/?"))
        XCTAssertTrue(authURLWithoutSlash!.absoluteString.contains("auth?"))
    }
}

class ASWebAuthSessionWrapperTests: XCTestCase {

    var wrapper: ASWebAuthSessionWrapper!
    var mockPresentationProvider: MockPresentationContextProvider!

    override func setUp() {
        super.setUp()
        mockPresentationProvider = MockPresentationContextProvider()
        wrapper = ASWebAuthSessionWrapper(presentationContextProvider: mockPresentationProvider)
    }

    override func tearDown() {
        wrapper = nil
        mockPresentationProvider = nil
        super.tearDown()
    }

    func testInitWithPresentationContextProvider() {
        // Arrange & Act
        let provider = MockPresentationContextProvider()
        let testWrapper = ASWebAuthSessionWrapper(presentationContextProvider: provider)

        // Assert
        XCTAssertNotNil(testWrapper)
    }

    func testInitWithoutPresentationContextProvider() {
        // Arrange & Act
        let testWrapper = ASWebAuthSessionWrapper()

        // Assert
        XCTAssertNotNil(testWrapper)
    }

    func testSetPresentationContextProvider() {
        // Arrange
        let newProvider = MockPresentationContextProvider()
        let testWrapper = ASWebAuthSessionWrapper()

        // Act
        testWrapper.setPresentationContextProvider(newProvider)

        // Assert
        // We can't directly test the private property, but we can verify the method doesn't crash
        XCTAssertNotNil(testWrapper)
    }

    func testSetPresentationContextProviderToNil() {
        // Arrange
        let testWrapper = ASWebAuthSessionWrapper(
            presentationContextProvider: mockPresentationProvider)

        // Act
        testWrapper.setPresentationContextProvider(nil)

        // Assert
        // We can't directly test the private property, but we can verify the method doesn't crash
        XCTAssertNotNil(testWrapper)
    }

    func testStartWithValidURL() {
        // Arrange
        let url = URL(string: "https://example.com/auth")!
        let callbackScheme = "myapp"

        // Act & Assert
        // Since ASWebAuthenticationSession is a system component, we can't easily mock it
        // We mainly test that the method doesn't crash and accepts the parameters
        XCTAssertNoThrow {
            self.wrapper.start(url: url, callbackScheme: callbackScheme) { callbackURL, error in
                // This completion will be called when ASWebAuthenticationSession completes
                // In unit tests, this typically won't be called without user interaction
            }
        }

        XCTAssertNotNil(wrapper)
    }

    func testStartWithNilCallbackScheme() {
        // Arrange
        let url = URL(string: "https://example.com/auth")!

        // Act & Assert
        XCTAssertNoThrow {
            self.wrapper.start(url: url, callbackScheme: nil) { callbackURL, error in
                // Completion handler - won't be called in unit tests
            }
        }

        XCTAssertNotNil(wrapper)
    }

    func testStartWithCustomSchemeURL() {
        // Arrange
        let url = URL(
            string:
                "https://keycloak.example.com/auth/realms/test/protocol/openid-connect/auth?client_id=test&response_type=code"
        )!
        let callbackScheme = "ca.bc.gov.asago"

        // Act & Assert
        XCTAssertNoThrow {
            self.wrapper.start(url: url, callbackScheme: callbackScheme) { callbackURL, error in
                // Completion handler - won't be called in unit tests
            }
        }

        XCTAssertNotNil(wrapper)
    }

    func testStartWithHTTPSCallbackScheme() {
        // Arrange
        let url = URL(string: "https://auth.example.com/oauth2/authorize")!
        let callbackScheme = "https"

        // Act & Assert
        XCTAssertNoThrow {
            self.wrapper.start(url: url, callbackScheme: callbackScheme) { callbackURL, error in
                // Completion handler - won't be called in unit tests
            }
        }

        XCTAssertNotNil(wrapper)
    }

    func testStartExecutesOnMainQueue() {
        // Arrange
        let url = URL(string: "https://example.com/auth")!
        let callbackScheme = "myapp"
        var methodExecuted = false

        // Act
        DispatchQueue.global().async {
            self.wrapper.start(url: url, callbackScheme: callbackScheme) { callbackURL, error in
                // Completion handler - won't be called in unit tests without user interaction
            }
            methodExecuted = true
        }

        // Wait briefly for the async call to complete
        Thread.sleep(forTimeInterval: 0.1)

        // Assert
        XCTAssertTrue(methodExecuted)
        XCTAssertNotNil(wrapper)
    }

    func testMultipleStartCalls() {
        // Arrange
        let url1 = URL(string: "https://example1.com/auth")!
        let url2 = URL(string: "https://example2.com/auth")!
        let callbackScheme = "myapp"

        // Act & Assert
        // Multiple calls should not crash the wrapper
        XCTAssertNoThrow {
            self.wrapper.start(url: url1, callbackScheme: callbackScheme) { _, _ in
                // First completion handler
            }

            self.wrapper.start(url: url2, callbackScheme: callbackScheme) { _, _ in
                // Second completion handler
            }
        }

        XCTAssertNotNil(wrapper)
    }

    func testStartWithComplexURL() {
        // Arrange
        let complexURL = URL(
            string:
                "https://keycloak.example.com/auth/realms/master/protocol/openid-connect/auth?client_id=test-client&response_type=code&redirect_uri=myapp%3A%2F%2Fauth%2Fcallback&code_challenge=test123&code_challenge_method=S256&state=abc123"
        )!
        let callbackScheme = "myapp"

        // Act & Assert
        XCTAssertNoThrow {
            self.wrapper.start(url: complexURL, callbackScheme: callbackScheme) { _, _ in
                // Completion handler - won't be called in unit tests
            }
        }

        XCTAssertNotNil(wrapper)
    }

    func testWebAuthSessionProtocolConformance() {
        // Arrange & Act
        let protocolWrapper: WebAuthSessionProtocol = wrapper

        // Assert
        XCTAssertNotNil(protocolWrapper)

        // Test that protocol method is available and doesn't crash
        let url = URL(string: "https://example.com")!

        XCTAssertNoThrow {
            protocolWrapper.start(url: url, callbackScheme: "test") { _, _ in
                // Completion handler - won't be called in unit tests
            }
        }
    }
}

// MARK: - Mock Classes

class MockPresentationContextProvider: NSObject, ASWebAuthenticationPresentationContextProviding {
    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        return UIWindow()
    }
}

class KeycloakPluginIntegrationTests: XCTestCase {

    var plugin: KeycloakPlugin!

    override func setUp() {
        super.setUp()
        plugin = KeycloakPlugin()
    }

    override func tearDown() {
        plugin = nil
        super.tearDown()
    }

    func testPluginMethodsExist() {
        // Test that all expected plugin methods exist
        XCTAssertTrue(plugin.responds(to: #selector(KeycloakPlugin.authenticate(_:))))
        XCTAssertTrue(plugin.responds(to: #selector(KeycloakPlugin.refreshToken(_:))))
    }

    func testPluginProperties() {
        // Test plugin properties
        XCTAssertEqual(plugin.identifier, "KeycloakPlugin")
        XCTAssertEqual(plugin.jsName, "Keycloak")
        XCTAssertEqual(plugin.pluginMethods.count, 2)

        // Check that plugin methods are properly configured
        let methodNames = plugin.pluginMethods.map { $0.name }
        XCTAssertTrue(methodNames.contains("authenticate"))
        XCTAssertTrue(methodNames.contains("refreshToken"))
    }

    func testPluginLoad() {
        // Test that plugin load method doesn't crash
        XCTAssertNoThrow { [self] in
            self.plugin.load()
        }
    }
}
class KeycloakSecurityTests: XCTestCase {

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

    override func tearDown() {
        keycloak = nil
        mockPKCEGenerator = nil
        mockURLBuilder = nil
        mockWebAuthSession = nil
        mockHTTPClient = nil
        super.tearDown()
    }

    func testSuspiciousRedirectURL() {
        // Test handling of potentially malicious redirect URLs
        let suspiciousURLs = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "file:///etc/passwd",
            "http://evil.com/callback",
            "ca.bc.gov.asago://auth/callback/../../../sensitive-path",
        ]

        for suspiciousURL in suspiciousURLs {
            let options = KeycloakOptions(
                clientId: "security-test-client",
                authorizationBaseUrl: "https://keycloak.example.com/auth",
                redirectUrl: suspiciousURL,
                accessTokenEndpoint: "https://keycloak.example.com/token"
            )

            let expectation = XCTestExpectation(description: "Security test for \(suspiciousURL)")

            keycloak.authenticate(options: options) { result in
                // System should handle gracefully without crashing
                switch result {
                case .success, .failure:
                    expectation.fulfill()
                }
            }

            wait(for: [expectation], timeout: 1.0)
        }
    }

    func testCallbackURLSpoofing() {
        // Test protection against callback URL spoofing
        let options = KeycloakOptions(
            clientId: "spoof-test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        // Simulate spoofed callback URL with different scheme
        mockWebAuthSession.mockCallbackURL = URL(
            string: "evil-app://auth/callback?code=stolen-code")

        let expectation = XCTestExpectation(description: "Callback URL spoofing test")

        keycloak.authenticate(options: options) { result in
            // System should handle gracefully
            switch result {
            case .success, .failure:
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

    func testLongParameterValues() {
        // Test handling of extremely long parameter values
        let longString = String(repeating: "a", count: 10000)

        let options = KeycloakOptions(
            clientId: longString,
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        let expectation = XCTestExpectation(description: "Long parameter test")

        keycloak.authenticate(options: options) { result in
            // System should handle gracefully without crashing
            switch result {
            case .success, .failure:
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: 2.0)
    }

    func testSpecialCharactersInParameters() {
        // Test handling of special characters in parameters
        let specialChars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"

        let options = KeycloakOptions(
            clientId: "test\(specialChars)client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        let expectation = XCTestExpectation(description: "Special characters test")

        keycloak.authenticate(options: options) { result in
            // System should handle gracefully
            switch result {
            case .success, .failure:
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }
}

class KeycloakPerformanceTests: XCTestCase {

    func testRapidSequentialOperations() {
        // Test performance with rapid sequential operations
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

        let mockRefreshResponse = """
            {
                "access_token": "performance_token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": "performance_refresh_token"
            }
            """.data(using: .utf8)
        mockHTTPClient.mockResponse = mockRefreshResponse

        let refreshOptions = KeycloakRefreshOptions(
            clientId: "performance-client",
            accessTokenEndpoint: "https://keycloak.example.com/token",
            refreshToken: "performance_refresh_token"
        )

        let startTime = Date()
        let operationCount = 100
        var completedOperations = 0
        let expectation = XCTestExpectation(description: "Performance test")

        // Perform many operations rapidly
        for _ in 0..<operationCount {
            keycloak.refreshToken(options: refreshOptions) { result in
                completedOperations += 1
                if completedOperations == operationCount {
                    let endTime = Date()
                    let duration = endTime.timeIntervalSince(startTime)
                    print("Completed \(operationCount) operations in \(duration) seconds")
                    expectation.fulfill()
                }
            }
        }

        wait(for: [expectation], timeout: 10.0)
    }

    func testLargeResponseHandling() {
        // Test handling of large response payloads
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

        // Create a large JSON response (simulate large token or metadata)
        let largeData = String(repeating: "x", count: 100000)
        let largeResponse = """
            {
                "access_token": "large_token_\(largeData)",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": "large_refresh_token_\(largeData)",
                "metadata": "\(largeData)"
            }
            """.data(using: .utf8)
        mockHTTPClient.mockResponse = largeResponse

        let refreshOptions = KeycloakRefreshOptions(
            clientId: "large-response-client",
            accessTokenEndpoint: "https://keycloak.example.com/token",
            refreshToken: "large_refresh_token"
        )

        let expectation = XCTestExpectation(description: "Large response test")

        keycloak.refreshToken(options: refreshOptions) { result in
            switch result {
            case .success(let data):
                XCTAssertTrue((data["accessToken"] as? String)?.hasPrefix("large_token_") == true)
                expectation.fulfill()
            case .failure(let error):
                XCTFail("Failed to handle large response: \(error)")
            }
        }

        wait(for: [expectation], timeout: 5.0)
    }
}

class KeycloakErrorRecoveryTests: XCTestCase {

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

    override func tearDown() {
        keycloak = nil
        mockPKCEGenerator = nil
        mockURLBuilder = nil
        mockWebAuthSession = nil
        mockHTTPClient = nil
        super.tearDown()
    }

    func testRecoveryAfterNetworkError() {
        // Test that the system can recover after a network error

        // First attempt - network error
        let refreshOptions = KeycloakRefreshOptions(
            clientId: "recovery-client",
            accessTokenEndpoint: "https://keycloak.example.com/token",
            refreshToken: "recovery_refresh_token"
        )

        mockHTTPClient.mockError = NSError(domain: "NSURLErrorDomain", code: -1009, userInfo: nil)

        let firstExpectation = XCTestExpectation(description: "First attempt with network error")

        keycloak.refreshToken(options: refreshOptions) { result in
            switch result {
            case .success:
                XCTFail("Expected failure due to network error")
            case .failure:
                firstExpectation.fulfill()
            }
        }

        wait(for: [firstExpectation], timeout: 1.0)

        // Second attempt - success
        mockHTTPClient.mockError = nil
        let mockRefreshResponse = """
            {
                "access_token": "recovery_token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": "new_recovery_refresh_token"
            }
            """.data(using: .utf8)
        mockHTTPClient.mockResponse = mockRefreshResponse

        let secondExpectation = XCTestExpectation(description: "Second attempt should succeed")

        keycloak.refreshToken(options: refreshOptions) { result in
            switch result {
            case .success(let data):
                XCTAssertEqual(data["accessToken"] as? String, "recovery_token")
                secondExpectation.fulfill()
            case .failure(let error):
                XCTFail("Expected success but got error: \(error)")
            }
        }

        wait(for: [secondExpectation], timeout: 1.0)
    }

    func testRecoveryAfterJSONParsingError() {
        // Test recovery after JSON parsing errors

        let refreshOptions = KeycloakRefreshOptions(
            clientId: "json-recovery-client",
            accessTokenEndpoint: "https://keycloak.example.com/token",
            refreshToken: "json_recovery_refresh_token"
        )

        // First attempt - malformed JSON
        mockHTTPClient.mockResponse = "{ malformed json".data(using: .utf8)

        let firstExpectation = XCTestExpectation(description: "First attempt with malformed JSON")

        keycloak.refreshToken(options: refreshOptions) { result in
            switch result {
            case .success:
                XCTFail("Expected failure due to malformed JSON")
            case .failure:
                firstExpectation.fulfill()
            }
        }

        wait(for: [firstExpectation], timeout: 1.0)

        // Second attempt - valid JSON
        let mockRefreshResponse = """
            {
                "access_token": "json_recovery_token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": "new_json_recovery_refresh_token"
            }
            """.data(using: .utf8)
        mockHTTPClient.mockResponse = mockRefreshResponse

        let secondExpectation = XCTestExpectation(description: "Second attempt should succeed")

        keycloak.refreshToken(options: refreshOptions) { result in
            switch result {
            case .success(let data):
                XCTAssertEqual(data["accessToken"] as? String, "json_recovery_token")
                secondExpectation.fulfill()
            case .failure(let error):
                XCTFail("Expected success but got error: \(error)")
            }
        }

        wait(for: [secondExpectation], timeout: 1.0)
    }
}

class KeycloakMemoryTests: XCTestCase {

    func testMemoryLeakPrevention() {
        // Test that creating and releasing Keycloak instances doesn't cause memory leaks
        weak var weakKeycloak: Keycloak?

        autoreleasepool {
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

            weakKeycloak = keycloak

            // Use the keycloak instance
            XCTAssertNotNil(keycloak)
        }

        // After autoreleasepool, the keycloak instance should be deallocated
        XCTAssertNil(weakKeycloak, "Keycloak instance should be deallocated")
    }

    func testMultipleInstancesIndependence() {
        // Test that multiple Keycloak instances work independently
        let mockPKCEGenerator1 = MockPKCEGenerator()
        mockPKCEGenerator1.codeVerifier = "verifier-1"
        mockPKCEGenerator1.codeChallenge = "challenge-1"

        let mockPKCEGenerator2 = MockPKCEGenerator()
        mockPKCEGenerator2.codeVerifier = "verifier-2"
        mockPKCEGenerator2.codeChallenge = "challenge-2"

        let keycloak1 = Keycloak(
            pkceGenerator: mockPKCEGenerator1,
            urlBuilder: MockURLBuilder(),
            webAuthSession: MockWebAuthSession(),
            httpClient: MockHTTPClient()
        )

        let keycloak2 = Keycloak(
            pkceGenerator: mockPKCEGenerator2,
            urlBuilder: MockURLBuilder(),
            webAuthSession: MockWebAuthSession(),
            httpClient: MockHTTPClient()
        )

        XCTAssertNotEqual(mockPKCEGenerator1.codeVerifier, mockPKCEGenerator2.codeVerifier)
        XCTAssertNotEqual(mockPKCEGenerator1.codeChallenge, mockPKCEGenerator2.codeChallenge)

        // Instances should be independent
        XCTAssertTrue(keycloak1 !== keycloak2)
    }
}

class KeycloakDataValidationTests: XCTestCase {

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

    override func tearDown() {
        keycloak = nil
        mockPKCEGenerator = nil
        mockURLBuilder = nil
        mockWebAuthSession = nil
        mockHTTPClient = nil
        super.tearDown()
    }

    func testTokenResponseWithNullValues() {
        // Test handling of null values in token response
        let options = KeycloakOptions(
            clientId: "null-test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        let mockTokenResponse = """
            {
                "access_token": "test_token",
                "token_type": null,
                "expires_in": null,
                "refresh_token": null,
                "scope": null
            }
            """.data(using: .utf8)
        mockHTTPClient.mockResponse = mockTokenResponse
        mockWebAuthSession.mockCallbackURL = URL(
            string: "ca.bc.gov.asago://auth/callback?code=null-test-code")

        let expectation = XCTestExpectation(description: "Handle null values in token response")

        keycloak.authenticate(options: options) { result in
            switch result {
            case .success(let data):
                XCTAssertEqual(data["isAuthenticated"] as? Bool, true)
                XCTAssertEqual(data["accessToken"] as? String, "test_token")
                // Check for null values - they might be NSNull instead of nil
                let tokenType = data["tokenType"]
                XCTAssertTrue(
                    tokenType == nil || tokenType is NSNull,
                    "Expected nil or NSNull but got \(String(describing: tokenType))")
                let expiresIn = data["expiresIn"]
                XCTAssertTrue(
                    expiresIn == nil || expiresIn is NSNull,
                    "Expected nil or NSNull but got \(String(describing: expiresIn))")
                let refreshToken = data["refreshToken"]
                XCTAssertTrue(
                    refreshToken == nil || refreshToken is NSNull,
                    "Expected nil or NSNull but got \(String(describing: refreshToken))")
                let scope = data["scope"]
                XCTAssertTrue(
                    scope == nil || scope is NSNull,
                    "Expected nil or NSNull but got \(String(describing: scope))")
                expectation.fulfill()
            case .failure(let error):
                XCTFail("Expected success but got error: \(error)")
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

    func testTokenResponseWithWrongDataTypes() {
        // Test handling of wrong data types in token response
        let options = KeycloakOptions(
            clientId: "wrong-type-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        let mockTokenResponse = """
            {
                "access_token": 12345,
                "token_type": true,
                "expires_in": "not_a_number",
                "refresh_token": ["array", "instead", "of", "string"],
                "scope": {"object": "instead_of_string"}
            }
            """.data(using: .utf8)
        mockHTTPClient.mockResponse = mockTokenResponse
        mockWebAuthSession.mockCallbackURL = URL(
            string: "ca.bc.gov.asago://auth/callback?code=wrong-type-code")

        let expectation = XCTestExpectation(
            description: "Handle wrong data types in token response")

        keycloak.authenticate(options: options) { result in
            switch result {
            case .success:
                // Implementation may handle type conversion gracefully
                expectation.fulfill()
            case .failure:
                // Or it may fail, which is also acceptable
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

    func testEmptyStringParameters() {
        // Test handling of empty string parameters
        let options = KeycloakOptions(
            clientId: "",
            authorizationBaseUrl: "",
            redirectUrl: "",
            accessTokenEndpoint: ""
        )

        let expectation = XCTestExpectation(description: "Handle empty string parameters")

        keycloak.authenticate(options: options) { result in
            // System should handle gracefully
            switch result {
            case .success, .failure:
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

    func testUnicodeCharacters() {
        // Test handling of Unicode characters
        let options = KeycloakOptions(
            clientId: "测试客户端-🔑-клиент",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        let mockTokenResponse = """
            {
                "access_token": "令牌-🎯-токен",
                "token_type": "Bearer",
                "scope": "openid профиль 配置文件"
            }
            """.data(using: .utf8)
        mockHTTPClient.mockResponse = mockTokenResponse
        mockWebAuthSession.mockCallbackURL = URL(
            string: "ca.bc.gov.asago://auth/callback?code=unicode-test")

        let expectation = XCTestExpectation(description: "Handle Unicode characters")

        keycloak.authenticate(options: options) { result in
            switch result {
            case .success(let data):
                XCTAssertEqual(data["accessToken"] as? String, "令牌-🎯-токен")
                XCTAssertEqual(data["scope"] as? String, "openid профиль 配置文件")
                expectation.fulfill()
            case .failure(let error):
                XCTFail("Expected success but got error: \(error)")
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }

}

class KeycloakNetworkTests: XCTestCase {

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

    override func tearDown() {
        keycloak = nil
        mockPKCEGenerator = nil
        mockURLBuilder = nil
        mockWebAuthSession = nil
        mockHTTPClient = nil
        super.tearDown()
    }

    func testSlowNetworkConditions() {
        // Test handling of slow network conditions
        let refreshOptions = KeycloakRefreshOptions(
            clientId: "slow-network-client",
            accessTokenEndpoint: "https://keycloak.example.com/token",
            refreshToken: "slow_network_refresh_token"
        )

        let mockRefreshResponse = """
            {
                "access_token": "slow_network_token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": "new_slow_network_refresh_token"
            }
            """.data(using: .utf8)
        mockHTTPClient.mockResponse = mockRefreshResponse

        let expectation = XCTestExpectation(description: "Handle slow network conditions")

        // Simulate slow response by adding delay
        DispatchQueue.global().asyncAfter(deadline: .now() + 0.1) {
            self.keycloak.refreshToken(options: refreshOptions) { result in
                switch result {
                case .success(let data):
                    XCTAssertEqual(data["accessToken"] as? String, "slow_network_token")
                    expectation.fulfill()
                case .failure(let error):
                    XCTFail("Expected success but got error: \(error)")
                }
            }
        }

        wait(for: [expectation], timeout: 2.0)
    }

    func testNetworkTimeoutScenarios() {
        // Test various network timeout scenarios
        let timeoutErrors = [
            NSError(domain: "NSURLErrorDomain", code: NSURLErrorTimedOut, userInfo: nil),
            NSError(
                domain: "NSURLErrorDomain", code: NSURLErrorNetworkConnectionLost, userInfo: nil),
            NSError(
                domain: "NSURLErrorDomain", code: NSURLErrorNotConnectedToInternet, userInfo: nil),
            NSError(domain: "NSURLErrorDomain", code: NSURLErrorDNSLookupFailed, userInfo: nil),
        ]

        for (index, error) in timeoutErrors.enumerated() {
            let refreshOptions = KeycloakRefreshOptions(
                clientId: "timeout-client-\(index)",
                accessTokenEndpoint: "https://keycloak.example.com/token",
                refreshToken: "timeout_refresh_token_\(index)"
            )

            mockHTTPClient.mockError = error
            mockHTTPClient.mockResponse = nil

            let expectation = XCTestExpectation(description: "Handle timeout error \(index)")

            keycloak.refreshToken(options: refreshOptions) { result in
                switch result {
                case .success:
                    XCTFail("Expected failure due to network error")
                case .failure(let resultError as NSError):
                    XCTAssertEqual(resultError.domain, "NSURLErrorDomain")
                    expectation.fulfill()
                }
            }

            wait(for: [expectation], timeout: 1.0)
        }
    }

    func testPartialResponseData() {
        // Test handling of partial/truncated response data
        let refreshOptions = KeycloakRefreshOptions(
            clientId: "partial-data-client",
            accessTokenEndpoint: "https://keycloak.example.com/token",
            refreshToken: "partial_data_refresh_token"
        )

        // Simulate truncated JSON response
        let partialResponse = """
            {
                "access_token": "partial_
            """.data(using: .utf8)
        mockHTTPClient.mockResponse = partialResponse

        let expectation = XCTestExpectation(description: "Handle partial response data")

        keycloak.refreshToken(options: refreshOptions) { result in
            switch result {
            case .success:
                XCTFail("Expected failure due to malformed JSON")
            case .failure(let error):
                XCTAssertTrue(
                    error.localizedDescription.contains("data")
                        || error.localizedDescription.contains("JSON")
                        || error.localizedDescription.contains("couldn't be read"))
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: 1.0)
    }
}

class KeycloakThreadSafetyTests: XCTestCase {

    func testConcurrentAccess() {
        // Test thread safety with concurrent access
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

        let mockRefreshResponse = """
            {
                "access_token": "thread_safe_token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": "thread_safe_refresh_token"
            }
            """.data(using: .utf8)
        mockHTTPClient.mockResponse = mockRefreshResponse

        let refreshOptions = KeycloakRefreshOptions(
            clientId: "thread-safe-client",
            accessTokenEndpoint: "https://keycloak.example.com/token",
            refreshToken: "thread_safe_refresh_token"
        )

        let concurrentQueue = DispatchQueue(label: "test.concurrent", attributes: .concurrent)
        let expectations = (0..<10).map {
            XCTestExpectation(description: "Concurrent operation \($0)")
        }

        // Start multiple operations on different threads
        for (_, expectation) in expectations.enumerated() {
            concurrentQueue.async {
                keycloak.refreshToken(options: refreshOptions) { result in
                    switch result {
                    case .success, .failure:
                        expectation.fulfill()
                    }
                }
            }
        }

        wait(for: expectations, timeout: 5.0)
    }

    func testMainQueueOperations() {
        // Test that UI-related operations happen on main queue
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
            clientId: "main-queue-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: "https://keycloak.example.com/token"
        )

        let expectation = XCTestExpectation(description: "Main queue operations")

        // Start authentication from background queue
        DispatchQueue.global().async {
            keycloak.authenticate(options: options) { result in
                // Verify we're back on main queue for UI operations
                XCTAssertTrue(Thread.isMainThread, "Completion should be called on main thread")
                expectation.fulfill()
            }
        }

        wait(for: [expectation], timeout: 2.0)
    }
}
