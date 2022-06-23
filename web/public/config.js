/**
 * This is a placeholder configuration file. In Openshift/dockerfile, this file is replaced by
 * a mapping.
 *
 * In local development values are taken from process.env
 * REACT_APP_KEYCLOAK_AUTH_URL is an exception - because of the way keycloak is loaded, it's
 * needed before process.env is available.
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
var config = {
  REACT_APP_SM_LOGOUT_URL: undefined,
  REACT_APP_KEYCLOAK_REALM: undefined,
  REACT_APP_KEYCLOAK_CLIENT: undefined,
  REACT_APP_KEYCLOAK_AUTH_URL: 'https://dev.oidc.gov.bc.ca/auth'
}
