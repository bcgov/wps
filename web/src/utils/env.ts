let ENV = {
  API_BASE_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8080/api',
  HIDE_DISCLAIMER: process.env.REACT_APP_HIDE_DISCLAIMER,
  FIDER_LINK:
    process.env.REACT_APP_FIDER_LINK || 'https://psufiderdev.pathfinder.gov.bc.ca/',
  KC_AUTH_URL:
    process.env.REACT_APP_KEYCLOAK_AUTH_URL || 'https://dev.oidc.gov.bc.ca/auth',
  KC_REALM: process.env.REACT_APP_KEYCLOAK_REALM || '8wl6x4cp',
  KC_CLIENT: process.env.REACT_APP_KEYCLOAK_CLIENT || 'wps-web'
}

// If the app is built using 'npm run build'
if (process.env.NODE_ENV === 'production') {
  // window.env is set in index.html, populated by env variables.
  ENV = {
    API_BASE_URL: '/api',
    HIDE_DISCLAIMER: undefined,
    FIDER_LINK: window.env.REACT_APP_FIDER_LINK,
    KC_AUTH_URL: window.env.REACT_APP_KEYCLOAK_AUTH_URL,
    KC_REALM: window.env.REACT_APP_KEYCLOAK_REALM,
    KC_CLIENT: window.env.REACT_APP_KEYCLOAK_CLIENT
  }
}

export const {
  API_BASE_URL,
  HIDE_DISCLAIMER,
  FIDER_LINK,
  KC_AUTH_URL,
  KC_REALM,
  KC_CLIENT
} = ENV
