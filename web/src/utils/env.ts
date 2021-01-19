let ENV = {
  API_BASE_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8080/api',
  HIDE_DISCLAIMER: process.env.REACT_APP_HIDE_DISCLAIMER,
  KC_AUTH_URL:
    process.env.REACT_APP_KEYCLOAK_AUTH_URL || 'https://dev.oidc.gov.bc.ca/auth',
  KC_REALM: process.env.REACT_APP_KEYCLOAK_REALM || '8wl6x4cp',
  KC_CLIENT: process.env.REACT_APP_KEYCLOAK_CLIENT || 'wps-web'
}

// If the app is built using 'npm run build'
if (process.env.NODE_ENV === 'production') {
  // window.env is set in index.html, populated by env variables.
  ENV = {
    // TODO: Figure out why axios goes to http on gets!
    API_BASE_URL: `${window.location.protocol}//${window.location.host}/api`,
    HIDE_DISCLAIMER: undefined,
    KC_AUTH_URL: window.env.REACT_APP_KEYCLOAK_AUTH_URL,
    KC_REALM: window.env.REACT_APP_KEYCLOAK_REALM,
    KC_CLIENT: window.env.REACT_APP_KEYCLOAK_CLIENT
  }
  console.log('API_BASE_URL:', ENV.API_BASE_URL)
}

console.log('process.env.REACT_APP_API_BASE_URL', process.env.REACT_APP_API_BASE_URL)
console.log('env.ts', ENV.API_BASE_URL)

export const { API_BASE_URL, HIDE_DISCLAIMER, KC_AUTH_URL, KC_REALM, KC_CLIENT } = ENV
