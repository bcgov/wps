import XCTest
@testable import KeycloakPlugin

class KeycloakTests: XCTestCase {
    func testEcho() {
        // This is an example of a functional test case for a plugin.
        // Use XCTAssert and related functions to verify your tests produce the correct results.

        let implementation = Keycloak()
        let value = "Hello, World!"
        let result = implementation.echo(value)

        XCTAssertEqual(value, result)
    }
}
