from google.oauth2.credentials import Credentials
import ee
import json
import jwt
from datetime import datetime, timedelta

def main():
    # construct jwt token
    token = jwt_token()

    # from google.oauth2.credentials import Credentials - only works with python 3.8.* or earlier.
    credentials = Credentials(token=token)
    ee.Initialize(credentials)

    print(ee.Image("NASA/NASADEM_HGT/001").get("title").getInfo())
    

def jwt_token():
    """
    https://developers.google.com/identity/protocols/oauth2#serviceaccount
    """

    # https://developers.google.com/identity/protocols/oauth2/service-account
    # https://developers.google.com/earth-engine/reference/rest?hl=en_GB
    # https://developers.google.com/identity/protocols/oauth2/service-account#python_2

    # we take our service account details as provided by the google console:
    with open('/Users/sybrand/Workspace/fire-350717-ca75193a59cc.json') as f:
        service_account = json.load(f)

    iat = datetime.now()
    exp = iat + timedelta(seconds=3600)

    payload = {
        'iss': service_account['client_email'],
        'sub': service_account['client_email'],
        'aud': 'https://earthengine.googleapis.com/',
        'iat': int(iat.timestamp()),
        'exp': int(exp.timestamp())
    }

    additional_headers = {
        'kid': service_account['private_key_id']
    }

    # sign the payload using the private key
    token = jwt.encode(payload, service_account['private_key'], headers=additional_headers, algorithm='RS256')
    print('access token:', token)

    return token


if __name__ == '__main__':
    main()