import UIKit
import Capacitor

class AsaGoViewController: CAPBridgeViewController   {

    override func viewDidLoad() {
        super.viewDidLoad()
        // Do any additional setup after loading the view.
    }
    
    override open func capacitorDidLoad() {
        bridge?.registerPluginInstance(KeycloakPlugin())
    }
    
}
