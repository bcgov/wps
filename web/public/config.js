/**
 * This is a placeholder configuration file. In Openshift/dockerfile, this file is replaced by
 * a mapping.
 *
 * In local development values are taken from process.env
 * VITE_KEYCLOAK_AUTH_URL is an exception - because of the way keycloak is loaded, it's
 * needed before process.env is available.
 */
const config = {
  VITE_SM_LOGOUT_URL: 'https://logontest7.gov.bc.ca/clp-cgi/logoff.cgi?retnow=1&returl=',
  VITE_KEYCLOAK_REALM: 'standard',
  VITE_KEYCLOAK_CLIENT: 'wps-3981',
  VITE_KEYCLOAK_AUTH_URL: 'https://dev.loginproxy.gov.bc.ca/auth',
  API_BASE_URL: 'http://localhost:8080/api',
  RASTER_SERVER_BASE_URL: 'https://wps-dev-raster-tileserver.apps.silver.devops.gov.bc.ca/v0.0.1',
  VITE_MS_TEAMS_SPRINT_REVIEW_URL: 'http://localhost:3000',
  VITE_MIRO_SPRINT_REVIEW_BOARD_URL: 'http://localhost:3000',
  VITE_PMTILES_BUCKET: 'https://My_S3_Bucket',
  VITE_MUI_LICENSE_KEY: 'key'
}

window.env = config;
