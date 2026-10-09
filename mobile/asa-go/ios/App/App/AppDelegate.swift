import AppAuth
import Capacitor
import Keycloak
import UIKit
import FirebaseCore
import FirebaseMessaging

@UIApplicationMain
class AppDelegate: UIResponder, UIApplicationDelegate, KeycloakAppDelegate {

    var currentAuthorizationFlow: OIDExternalUserAgentSession?

    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
    ) -> Bool {
        // Override point for customization after application launch.
        FirebaseApp.configure()
        return true
    }

    func resumeAuthorizationFlow(with url: URL) -> Bool {
        guard let authorizationFlow = currentAuthorizationFlow,
            authorizationFlow.resumeExternalUserAgentFlow(with: url)
        else {
            return false
        }
        currentAuthorizationFlow = nil
        return true
    }


  func application(
    _ application: UIApplication,
    didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data
  ) {
    NotificationCenter.default.post(
      name: .capacitorDidRegisterForRemoteNotifications,
      object: deviceToken
    )
  }

  func application(
    _ application: UIApplication,
    didFailToRegisterForRemoteNotificationsWithError error: Error
  ) {
    NotificationCenter.default.post(
      name: .capacitorDidFailToRegisterForRemoteNotifications,
      object: error
    )
  }

  func application(
    _ application: UIApplication,
    didReceiveRemoteNotification userInfo: [AnyHashable: Any],
    fetchCompletionHandler completionHandler: @escaping (UIBackgroundFetchResult) -> Void
  ) {
    NotificationCenter.default.post(
      name: Notification.Name.init("didReceiveRemoteNotification"),
      object: completionHandler,
      userInfo: userInfo
    )
  }

}
