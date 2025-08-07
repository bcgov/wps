"""Dependency functions used for authenticating and auditing requests"""

import logging
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt import InvalidTokenError
from sentry_sdk import set_user
from wps_shared import config
from wps_shared.db.crud.api_access_audits import create_api_access_audit_log
from wps_shared.tests.common import ASA_TEST_IDIR_GUID

logger = logging.getLogger(__name__)

# Parse request header and pass the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


async def permissive_oauth2_scheme(request: Request):
    """Returns parsed auth token if authorized, None otherwise."""
    try:
        return await oauth2_scheme.__call__(request)
    except HTTPException as exception:
        logger.error("Could not validate the credential %s", exception)
        return None


async def sfms_authenticate(request: Request):
    """Returns parsed auth token if authorized, None otherwise."""
    secret = request.headers.get("Secret")
    if not secret or secret != config.get("SFMS_SECRET"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


async def authenticate(token: str = Depends(permissive_oauth2_scheme)):
    """Returns Decoded token when validation of the token is successful.
    Returns empty dictionary on failure to decode"""
    # RSA public key format
    keycloak_public_key = (
        "-----BEGIN PUBLIC KEY-----\n"
        + config.get("KEYCLOAK_PUBLIC_KEY")
        + "\n-----END PUBLIC KEY-----"
    )
    keycloak_client = config.get("KEYCLOAK_CLIENT")

    try:
        decoded_token = jwt.decode(
            token, keycloak_public_key, algorithms=["RS256"], audience=keycloak_client
        )
        return decoded_token
    except InvalidTokenError as exception:
        logger.error("Could not validate the credential %s", exception)
        return {}


async def default_authenticate(request: Request, token=Depends(authenticate)):
    """
    Only allows non-mobile test IDIRs
    """
    guid = token.get("idir_user_guid", None)
    if str(guid).upper() == ASA_TEST_IDIR_GUID:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return token


async def _audit_with_token(request: Request, token: dict):
    """Core audit logic that can be reused."""
    path = request.url.path
    username = token.get("idir_username", None)
    create_api_access_audit_log(username, bool(token), path)
    return token


async def audit(request: Request, token=Depends(permissive_oauth2_scheme)):
    """Audits attempted requests based on bearer token."""
    # Use the same authentication logic as default_authenticate for consistency
    try:
        decoded_token = await authenticate(token)
        # Apply the same test IDIR check as default_authenticate
        guid = decoded_token.get("idir_user_guid", None)
        if str(guid).upper() == ASA_TEST_IDIR_GUID:
            decoded_token = {}
    except Exception:
        decoded_token = {}

    return await _audit_with_token(request, decoded_token)


async def audit_asa(request: Request, token=Depends(permissive_oauth2_scheme)):
    """Audits attempted requests based on bearer token."""
    # Use the same authentication logic but without test IDIR check (like asa_authentication_required)
    try:
        decoded_token = await authenticate(token)
    except Exception:
        decoded_token = {}

    return await _audit_with_token(request, decoded_token)


async def _require_authentication(token: dict):
    """Core authentication requirement logic."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, headers={"WWW-Authenticate": "Bearer"}
        )
    set_user({"email": token.get("email", None)})
    return token


async def authentication_required(token=Depends(default_authenticate)):
    """Raises HTTPException with status code 401 if authentication fails."""
    return await _require_authentication(token)


async def asa_authentication_required(token=Depends(authenticate)):
    """Raises HTTPException with status code 401 if authentication fails."""
    return await _require_authentication(token)


async def check_token_for_role(role: str, token):
    """Return token if role exists in roles, 401 exception otherwise"""
    roles = token.get("client_roles", {})
    if role not in roles:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, headers={"WWW-Authenticate": "Bearer"}
        )
    return token


def create_role_auth_dependency(role: str):
    """Factory function to create role-based authentication dependencies."""

    async def auth_with_role_required(token=Depends(authentication_required)):
        return await check_token_for_role(role, token)

    return auth_with_role_required


# Role-based authentication dependencies
auth_with_set_fire_starts_role_required = create_role_auth_dependency("hfi_set_fire_starts")
auth_with_select_station_role_required = create_role_auth_dependency("hfi_select_station")
auth_with_station_admin_role_required = create_role_auth_dependency("hfi_station_admin")
auth_with_set_fuel_type_role_required = create_role_auth_dependency("hfi_set_fuel_type")
auth_with_set_ready_state_required = create_role_auth_dependency("hfi_set_ready_state")
auth_with_forecaster_role_required = create_role_auth_dependency("morecast2_write_forecast")
