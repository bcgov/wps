"""Dependency functions used for authenticating and auditing requests"""
import logging
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt import InvalidTokenError
from app import config
from app.db.crud.api_access_audits import create_api_access_audit_log

logger = logging.getLogger(__name__)

# Parse request header and pass the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


async def permissive_oauth2_scheme(request: Request):
    """ Returns parsed auth token if authorized, None otherwise. """
    try:
        return await oauth2_scheme.__call__(request)
    except HTTPException as exception:
        logger.error('Could not validate the credential %s', exception)
        return None


async def authenticate(token: str = Depends(permissive_oauth2_scheme)):
    """ Returns Decoded token when validation of the token is successful.
        Returns empty dictionary on failure to decode """
    # RSA public key format
    keycloak_public_key = '-----BEGIN PUBLIC KEY-----\n' + \
        config.get('KEYCLOAK_PUBLIC_KEY') + '\n-----END PUBLIC KEY-----'

    try:
        decoded_token = jwt.decode(
            token, keycloak_public_key, algorithm='RS256')
        return decoded_token
    except InvalidTokenError as exception:
        logger.error('Could not validate the credential %s', exception)
        return {}


async def audit(request: Request, token=Depends(authenticate)):
    """ Audits attempted requests based on bearer token. """
    path = request.url.path
    username = token.get('preferred_username', None)

    create_api_access_audit_log(username, bool(token), path)


async def authentication_required(token=Depends(authenticate)):
    """ Raises HTTPExcecption with status code 401 if authentation fails."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={'WWW-Authenticate': 'Bearer'}
        )
