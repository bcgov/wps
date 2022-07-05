class MockJWTDecodeWithRole:
    """ Mock pyjwt module with role """

    def __init__(self, role):
        self.decoded_token = {
            "preferred_username": "test_username",
            "resource_access": {
                "wps-web": {
                    "roles": [
                        role
                    ]
                }
            }}

    def __getitem__(self, key):
        return self.decoded_token[key]

    def get(self, key, _):
        "Returns the mock decoded token"
        return self.decoded_token[key]

    def decode(self):
        "Returns the mock decoded token"
        return self.decoded_token
