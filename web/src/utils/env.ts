let ENV = {
  API_BASE_URL: process.env.REACT_APP_API_BASE_URL as string,
  RASTER_SERVER_BASE_URL: process.env.REACT_APP_RASTER_SERVER_BASE_URL as string,
  HIDE_DISCLAIMER: process.env.REACT_APP_HIDE_DISCLAIMER,
  SM_LOGOUT_URL: process.env.REACT_APP_SM_LOGOUT_URL as string,
  KC_AUTH_URL: process.env.REACT_APP_KEYCLOAK_AUTH_URL as string,
  KC_REALM: process.env.REACT_APP_KEYCLOAK_REALM as string,
  KC_CLIENT: process.env.REACT_APP_KEYCLOAK_CLIENT as string,
  TEST_AUTH: process.env.TEST_AUTH
}

// If the app is built using 'npm run build'
if (process.env.NODE_ENV === 'production') {
  // window.env is set in index.html, populated by env variables.
  ENV = {
    // TODO: Figure out why axios goes to http on gets!
    API_BASE_URL: window.env.API_BASE_URL ?? `${window.location.protocol}//${window.location.host}/api`,
    RASTER_SERVER_BASE_URL: window.env.RASTER_SERVER_BASE_URL ?? `${window.location.protocol}//${window.location.host}`,
    HIDE_DISCLAIMER: undefined,
    SM_LOGOUT_URL: window.env.REACT_APP_SM_LOGOUT_URL,
    KC_AUTH_URL: window.env.REACT_APP_KEYCLOAK_AUTH_URL,
    KC_REALM: window.env.REACT_APP_KEYCLOAK_REALM,
    KC_CLIENT: window.env.REACT_APP_KEYCLOAK_CLIENT,
    TEST_AUTH: undefined
  }
}

export const {
  API_BASE_URL,
  RASTER_SERVER_BASE_URL,
  HIDE_DISCLAIMER,
  KC_AUTH_URL,
  KC_REALM,
  KC_CLIENT,
  TEST_AUTH,
  SM_LOGOUT_URL
} = ENV
