/**
 * This is a placeholder configuration file. In Openshift/dockerfile, this file is replaced by
 * a mapping.
 *
 * In local development values are taken from process.env
 * REACT_APP_KEYCLOAK_AUTH_URL is an exception - because of the way keycloak is loaded, it's
 * needed before process.env is available.
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const config = {
  REACT_APP_SM_LOGOUT_URL: 'https://logontest7.gov.bc.ca/clp-cgi/logoff.cgi?retnow=1&returl=',
  REACT_APP_KEYCLOAK_REALM: '8wl6x4cp',
  REACT_APP_KEYCLOAK_CLIENT: 'wps-web',
  REACT_APP_KEYCLOAK_AUTH_URL: 'https://dev.oidc.gov.bc.ca/auth',
  API_BASE_URL: 'http://localhost:8080/api',
  RASTER_SERVER_BASE_URL: 'http://localhost:8090'
}
