import Foundation
import XCTest

@testable import KeycloakPlugin

// MARK: - Mock Implementations for Testing

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

class KeycloakTests: XCTestCase {

    var keycloak: Keycloak!
    var mockPKCEGenerator: MockPKCEGenerator!
    var mockURLBuilder: MockURLBuilder!
    var mockWebAuthSession: MockWebAuthSession!

    override func setUp() {
        super.setUp()

        mockPKCEGenerator = MockPKCEGenerator()
        mockURLBuilder = MockURLBuilder()
        mockWebAuthSession = MockWebAuthSession()

        keycloak = Keycloak(
            pkceGenerator: mockPKCEGenerator,
            urlBuilder: mockURLBuilder,
            webAuthSession: mockWebAuthSession
        )
    }

    func testSuccessfulAuthentication() {
        // Arrange
        let options = KeycloakOptions(
            clientId: "test-client",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: nil
        )

        mockWebAuthSession.mockCallbackURL = URL(
            string: "ca.bc.gov.asago://auth/callback?code=test-auth-code&state=test-state")

        let expectation = XCTestExpectation(description: "Authentication should succeed")

        // Act
        keycloak.authenticate(options: options) { result in
            // Assert
            switch result {
            case .success(let data):
                XCTAssertEqual(data["code"] as? String, "test-auth-code")
                XCTAssertEqual(data["state"] as? String, "test-state")
                XCTAssertEqual(data["codeVerifier"] as? String, "test-code-verifier-123")
                XCTAssertNotNil(data["redirectUrl"])
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
            accessTokenEndpoint: nil
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
            case .success:
                XCTFail("Expected failure but got success")
            case .failure(let error as NSError):
                XCTAssertEqual(error.domain, "KeycloakError")
                XCTAssertEqual(error.code, 3)
                XCTAssertTrue(error.localizedDescription.contains("redirect URI"))
                expectation.fulfill()
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
            accessTokenEndpoint: nil
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
            accessTokenEndpoint: nil
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
            accessTokenEndpoint: nil
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
}

class URLBuilderTests: XCTestCase {

    func testBuildAuthorizationURL() {
        let urlBuilder = DefaultURLBuilder()
        let options = KeycloakOptions(
            clientId: "test-client-123",
            authorizationBaseUrl: "https://keycloak.example.com/auth",
            redirectUrl: "ca.bc.gov.asago://auth/callback",
            accessTokenEndpoint: nil
        )

        let url = urlBuilder.buildAuthorizationURL(
            options: options, codeChallenge: "test-challenge")

        XCTAssertNotNil(url)
        XCTAssertTrue(url!.absoluteString.contains("client_id=test-client-123"))
        XCTAssertTrue(url!.absoluteString.contains("response_type=code"))
        XCTAssertTrue(url!.absoluteString.contains("code_challenge=test-challenge"))
        XCTAssertTrue(url!.absoluteString.contains("code_challenge_method=S256"))
        XCTAssertTrue(
            url!.absoluteString.contains("redirect_uri=ca.bc.gov.asago%3A%2F%2Fauth%2Fcallback"))
    }
}

class PKCEGeneratorTests: XCTestCase {

    func testGenerateCodeVerifier() {
        let generator = DefaultPKCEGenerator()
        let verifier1 = generator.generateCodeVerifier()
        let verifier2 = generator.generateCodeVerifier()

        // Verifiers should be different each time
        XCTAssertNotEqual(verifier1, verifier2)

        // Verifiers should be valid base64url strings
        XCTAssertFalse(verifier1.contains("+"))
        XCTAssertFalse(verifier1.contains("/"))
        XCTAssertFalse(verifier1.contains("="))
    }

    func testGenerateCodeChallenge() {
        let generator = DefaultPKCEGenerator()
        let verifier = "test-verifier"
        let challenge = generator.generateCodeChallenge(from: verifier)

        // Challenge should be deterministic for the same verifier
        let challenge2 = generator.generateCodeChallenge(from: verifier)
        XCTAssertEqual(challenge, challenge2)

        // Challenge should be different from verifier
        XCTAssertNotEqual(challenge, verifier)

        // Challenge should be valid base64url string
        XCTAssertFalse(challenge.contains("+"))
        XCTAssertFalse(challenge.contains("/"))
        XCTAssertFalse(challenge.contains("="))
    }
}
