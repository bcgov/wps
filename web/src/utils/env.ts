let ENV = {
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL as string,
  RASTER_SERVER_BASE_URL: import.meta.env.VITE_RASTER_SERVER_BASE_URL as string,
  HIDE_DISCLAIMER: import.meta.env.VITE_HIDE_DISCLAIMER,
  SM_LOGOUT_URL: import.meta.env.VITE_SM_LOGOUT_URL as string,
  KC_AUTH_URL: import.meta.env.VITE_KEYCLOAK_AUTH_URL as string,
  KC_REALM: import.meta.env.VITE_KEYCLOAK_REALM as string,
  KC_CLIENT: import.meta.env.VITE_KEYCLOAK_CLIENT as string,
  TEST_AUTH: import.meta.env.VITE_TEST_AUTH,
  MS_TEAMS_SPRINT_REVIEW_URL: import.meta.env.VITE_MS_TEAMS_SPRINT_REVIEW_URL as string,
  MIRO_SPRINT_REVIEW_BOARD_URL: import.meta.env.VITE_MIRO_SPRINT_REVIEW_BOARD_URL as string,
  PMTILES_BUCKET: import.meta.env.VITE_PMTILES_BUCKET as string,
  MUI_LICENSE: import.meta.env.VITE_MUI_LICENSE_KEY as string,
  SENTRY_DSN: import.meta.env.VITE_SENTRY_DSN as string,
  SENTRY_ENV: import.meta.env.VITE_SENTRY_ENV as string,
  PSU_BUCKET: import.meta.env.VITE_PSU_BUCKET as string
}
// If the app is built using 'npm run build'
if (import.meta.env.MODE === 'production') {
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
    TEST_AUTH: undefined,
    MS_TEAMS_SPRINT_REVIEW_URL: window.env.REACT_APP_MS_TEAMS_SPRINT_REVIEW_URL,
    MIRO_SPRINT_REVIEW_BOARD_URL: window.env.REACT_APP_MIRO_SPRINT_REVIEW_BOARD_URL,
    PMTILES_BUCKET: window.env.REACT_APP_PMTILES_BUCKET,
    MUI_LICENSE: window.env.REACT_APP_MUI_LICENSE_KEY,
    SENTRY_DSN: window.env.REACT_APP_SENTRY_DSN,
    SENTRY_ENV: window.env.REACT_APP_SENTRY_ENV,
    PSU_BUCKET: window.env.REACT_APP_PSU_BUCKET
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
  SM_LOGOUT_URL,
  MS_TEAMS_SPRINT_REVIEW_URL,
  MIRO_SPRINT_REVIEW_BOARD_URL,
  PMTILES_BUCKET,
  MUI_LICENSE,
  SENTRY_DSN,
  SENTRY_ENV,
  PSU_BUCKET
} = ENV
