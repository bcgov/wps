import Foundation

@objc public class Echo: NSObject {
    
    public override init() {
        super.init()
        print("🔌 Echo: Implementation class initialized")
    }
    
    @objc public func echo(_ value: String) -> String {
        print("🔌 Echo: echo implementation called with value: \(value)")
        print(value)
        return value
    }
}