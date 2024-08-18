// use TypeScript's interface declaration merging
interface Window {
  env: {
    VITE_SM_LOGOUT_URL: string
    VITE_KEYCLOAK_AUTH_URL: string
    VITE_KEYCLOAK_REALM: string
    VITE_KEYCLOAK_CLIENT: string
    VITE_WF1_AUTH_URL: string
    API_BASE_URL: string | undefined
    RASTER_SERVER_BASE_URL: string | undefined
    VITE_MS_TEAMS_SPRINT_REVIEW_URL: string
    VITE_MIRO_SPRINT_REVIEW_BOARD_URL: string
    VITE_PMTILES_BUCKET: string
    VITE_MUI_LICENSE_KEY: string
    VITE_SENTRY_DSN: string
    VITE_SENTRY_ENV: string
  }
  Cypress: {} | undefined
}
