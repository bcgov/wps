let ENV = {
  API_BASE_URL: process.env.REACT_APP_API_BASE_URL as string,
  HIDE_DISCLAIMER: process.env.REACT_APP_HIDE_DISCLAIMER,
  KC_AUTH_URL: process.env.REACT_APP_KEYCLOAK_AUTH_URL as string,
  KC_REALM: process.env.REACT_APP_KEYCLOAK_REALM as string,
  KC_CLIENT: process.env.REACT_APP_KEYCLOAK_CLIENT as string,
  WEATHER_STATIONS_WEB_FEATURE_SERVICE: process.env
    .REACT_APP_WEATHER_STATIONS_WEB_FEATURE_SERVICE as string
}

// If the app is built using 'npm run build'
if (process.env.NODE_ENV === 'production') {
  // window.env is set in index.html, populated by env variables.
  ENV = {
    API_BASE_URL: '/api',
    HIDE_DISCLAIMER: undefined,
    KC_AUTH_URL: window.env.REACT_APP_KEYCLOAK_AUTH_URL,
    KC_REALM: window.env.REACT_APP_KEYCLOAK_REALM,
    KC_CLIENT: window.env.REACT_APP_KEYCLOAK_CLIENT,
    WEATHER_STATIONS_WEB_FEATURE_SERVICE:
      window.env.REACT_APP_WEATHER_STATIONS_WEB_FEATURE_SERVICE
  }
}

export const {
  API_BASE_URL,
  HIDE_DISCLAIMER,
  KC_AUTH_URL,
  KC_REALM,
  KC_CLIENT,
  WEATHER_STATIONS_WEB_FEATURE_SERVICE
} = ENV
