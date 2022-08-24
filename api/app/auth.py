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
        return await oauth2_scheme.__call__(request)  # pylint: disable=unnecessary-dunder-call
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
            token, keycloak_public_key, algorithms=['RS256'])
        return decoded_token
    except InvalidTokenError as exception:
        logger.error('Could not validate the credential %s', exception)
        return {}


async def audit(request: Request, token=Depends(authenticate)):
    """ Audits attempted requests based on bearer token. """
    path = request.url.path
    username = token.get('preferred_username', None)

    create_api_access_audit_log(username, bool(token), path)
    return token


async def authentication_required(token=Depends(authenticate)):
    """ Raises HTTPExcecption with status code 401 if authentation fails."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={'WWW-Authenticate': 'Bearer'}
        )
    return token


async def check_token_for_role(role: str, token):
    """ Return token if role exists in roles, 401 exception otherwise """
    roles = token.get('resource_access', {}).get('wps-web', {}).get('roles', {})
    if role not in roles:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={'WWW-Authenticate': 'Bearer'}
        )
    return token


async def auth_with_set_fire_starts_role_required(token=Depends(authentication_required)):
    """ Only return requests that have set fire starts permission """
    return await check_token_for_role('hfi_set_fire_starts', token)


async def auth_with_select_station_role_required(token=Depends(authentication_required)):
    """ Only return requests that have set fire starts permission """
    return await check_token_for_role('hfi_select_station', token)


async def auth_with_station_admin_role_required(token=Depends(authentication_required)):
    """ Only return requests that have station admin permission """
    return await check_token_for_role('hfi_station_admin', token)


async def auth_with_set_fuel_type_role_required(token=Depends(authentication_required)):
    """ Only return requests that have set fuel type permission """
    return await check_token_for_role('hfi_set_fuel_type', token)


async def auth_with_set_ready_state_required(token=Depends(authentication_required)):
    """ Only return requests that have set ready state permission """
    return await check_token_for_role('hfi_set_ready_state', token)
