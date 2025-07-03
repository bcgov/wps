import Foundation
import Capacitor

@objc(EchoPlugin)
public class EchoPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "EchoPlugin"
    public let jsName = "Echo"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "echo", returnType: CAPPluginReturnPromise)
    ]
    private let implementation = Echo()

    // Debug: Called when plugin is loaded
    public override func load() {
        print("🔌 EchoPlugin: Plugin loaded successfully!")
        print("🔌 EchoPlugin: Plugin identifier: \(identifier)")
        print("🔌 EchoPlugin: Plugin JS name: \(jsName)")
        super.load()
    }

    @objc func echo(_ call: CAPPluginCall) {
        print("🔌 EchoPlugin: echo method called")
        let value = call.getString("value") ?? ""
        print("🔌 EchoPlugin: received value: \(value)")
        
        let result = implementation.echo(value)
        print("🔌 EchoPlugin: returning value: \(result)")
        
        call.resolve([
            "value": result
        ])
    }
}