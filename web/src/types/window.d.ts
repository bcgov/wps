// use TypeScript's interface declaration merging
interface Window {
  env: {
    REACT_APP_SM_LOGOUT_URL: string
    REACT_APP_KEYCLOAK_AUTH_URL: string
    REACT_APP_KEYCLOAK_REALM: string
    REACT_APP_KEYCLOAK_CLIENT: string
    API_BASE_URL: string | undefined
    RASTER_SERVER_BASE_URL: string | undefined
    REACT_APP_MS_TEAMS_SPRINT_REVIEW_URL: string
    REACT_APP_MIRO_SPRINT_REVIEW_BOARD_URL: string
    REACT_APP_PMTILES_BUCKET: string
    REACT_APP_MUI_LICENSE_KEY: string
    REACT_APP_SENTRY_DSN: string
    REACT_APP_SENTRY_ENV: string
    REACT_APP_PSU_BUCKET: string
    REACT_APP_BASEMAP_TILE_URL: string
    REACT_APP_BASEMAP_STYLE_URL: string
  }
  Cypress: {} | undefined
}
