import Capacitor
import Foundation

/// Please read the Capacitor iOS Plugin Development Guide
/// here: https://capacitorjs.com/docs/plugins/ios
@objc(KeycloakPlugin)
public class KeycloakPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "KeycloakPlugin"
    public let jsName = "Keycloak"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "echo", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "authenticate", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "refreshToken", returnType: CAPPluginReturnPromise),
    ]
    private let implementation = Keycloak()

    @objc func echo(_ call: CAPPluginCall) {
        let value = call.getString("value") ?? ""
        call.resolve([
            "value": implementation.echo(value)
        ])
    }

    @objc func authenticate(_ call: CAPPluginCall) {
        guard let clientId = call.getString("clientId") else {
            call.reject("Missing required parameter: clientId")
            return
        }

        guard let authorizationBaseUrl = call.getString("authorizationBaseUrl") else {
            call.reject("Missing required parameter: authorizationBaseUrl")
            return
        }

        let options = KeycloakOptions(
            clientId: clientId,
            authorizationBaseUrl: authorizationBaseUrl,
            responseType: call.getString("responseType"),
            redirectUrl: call.getString("redirectUrl"),
            accessTokenEndpoint: call.getString("accessTokenEndpoint"),
            resourceUrl: call.getString("resourceUrl"),
            pkceEnabled: call.getBool("pkceEnabled") ?? true,
            scope: call.getString("scope"),
            state: call.getString("state"),
            additionalParameters: call.getObject("additionalParameters") as? [String: String],
            logsEnabled: call.getBool("logsEnabled") ?? false,
            logoutUrl: call.getString("logoutUrl"),
            additionalResourceHeaders: call.getObject("additionalResourceHeaders")
                as? [String: String]
        )

        implementation.authenticate(options: options) { result in
            switch result {
            case .success(let response):
                call.resolve(response)
            case .failure(let error):
                call.reject("Authentication failed", error.localizedDescription)
            }
        }
    }

    @objc func refreshToken(_ call: CAPPluginCall) {
        guard let clientId = call.getString("clientId") else {
            call.reject("Missing required parameter: clientId")
            return
        }

        guard let accessTokenEndpoint = call.getString("accessTokenEndpoint") else {
            call.reject("Missing required parameter: accessTokenEndpoint")
            return
        }

        guard let refreshToken = call.getString("refreshToken") else {
            call.reject("Missing required parameter: refreshToken")
            return
        }

        let options = KeycloakRefreshOptions(
            clientId: clientId,
            accessTokenEndpoint: accessTokenEndpoint,
            refreshToken: refreshToken
        )

        implementation.refreshToken(options: options) { result in
            switch result {
            case .success(let response):
                call.resolve(response)
            case .failure(let error):
                call.reject("Token refresh failed", error.localizedDescription)
            }
        }
    }
}
