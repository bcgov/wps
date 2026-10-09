import Capacitor
import UIKit

class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?

    func scene(
        _ scene: UIScene, willConnectTo session: UISceneSession,
        options connectionOptions: UIScene.ConnectionOptions
    ) {
        // the scene manifest loads Main.storyboard; Capacitor defers launch links until plugins load
        SceneDelegateProxy.shared.scene(scene, willConnectTo: session, options: connectionOptions)
    }

    func scene(_ scene: UIScene, openURLContexts urlContexts: Set<UIOpenURLContext>) {
        let appDelegate = UIApplication.shared.delegate as? AppDelegate
        // consume login callbacks before forwarding ordinary links to the web app
        let unhandledContexts = urlContexts.filter { context in
            appDelegate?.resumeAuthorizationFlow(with: context.url) != true
        }
        SceneDelegateProxy.shared.scene(scene, openURLContexts: unhandledContexts)
    }

    func scene(_ scene: UIScene, continue userActivity: NSUserActivity) {
        SceneDelegateProxy.shared.scene(scene, continue: userActivity)
    }
}
