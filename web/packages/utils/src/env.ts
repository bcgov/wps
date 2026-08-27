// Set by nginx's sub_filter substituting a fresh value into index.html's meta tag on
// every request, matching the style-src nonce on the Content-Security-Policy header for
// that same response (see openshift/nginx.conf). Shared here since several components
// (e.g. DataGridPro, which injects its own <style> tags outside Emotion's cache) need
// this same nonce value passed to them directly, not just the root Emotion cache.
export const CSP_NONCE =
  typeof document === 'undefined'
    ? undefined
    : (document.querySelector('meta[property="csp-nonce"]')?.getAttribute('content') ?? undefined)

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
  SPRINT_REVIEW_BOARD_URL: import.meta.env.VITE_SPRINT_REVIEW_BOARD_URL as string,
  PMTILES_BUCKET: import.meta.env.VITE_PMTILES_BUCKET as string,
  MUI_LICENSE: import.meta.env.VITE_MUI_LICENSE_KEY as string,
  SENTRY_DSN: import.meta.env.VITE_SENTRY_DSN as string,
  SENTRY_ENV: import.meta.env.VITE_SENTRY_ENV as string,
  PSU_BUCKET: import.meta.env.VITE_PSU_BUCKET as string,
  BASEMAP_TILE_URL: import.meta.env.VITE_BASEMAP_TILE_URL as string,
  BASEMAP_STYLE_URL: import.meta.env.VITE_BASEMAP_STYLE_URL as string,
  HILLSHADE_TILE_URL: import.meta.env.VITE_HILLSHADE_TILE_URL as string,
  HILLSHADE_STYLE_URL: import.meta.env.VITE_HILLSHADE_STYLE_URL as string
}
// If the app is built using 'npm run build'
if (import.meta.env.MODE === 'production') {
  // globalThis.config is set by config.js, loaded in index.html.
  ENV = {
    // TODO: Figure out why axios goes to http on gets!
    API_BASE_URL: config.API_BASE_URL ?? `${location.protocol}//${location.host}/api`,
    RASTER_SERVER_BASE_URL: config.RASTER_SERVER_BASE_URL ?? `${location.protocol}//${location.host}`,
    HIDE_DISCLAIMER: undefined,
    SM_LOGOUT_URL: config.REACT_APP_SM_LOGOUT_URL,
    KC_AUTH_URL: config.REACT_APP_KEYCLOAK_AUTH_URL,
    KC_REALM: config.REACT_APP_KEYCLOAK_REALM,
    KC_CLIENT: config.REACT_APP_KEYCLOAK_CLIENT,
    TEST_AUTH: undefined,
    MS_TEAMS_SPRINT_REVIEW_URL: config.REACT_APP_MS_TEAMS_SPRINT_REVIEW_URL,
    SPRINT_REVIEW_BOARD_URL: config.REACT_APP_SPRINT_REVIEW_BOARD_URL,
    PMTILES_BUCKET: config.REACT_APP_PMTILES_BUCKET,
    MUI_LICENSE: config.REACT_APP_MUI_LICENSE_KEY,
    SENTRY_DSN: config.REACT_APP_SENTRY_DSN,
    SENTRY_ENV: config.REACT_APP_SENTRY_ENV,
    PSU_BUCKET: config.REACT_APP_PSU_BUCKET,
    BASEMAP_TILE_URL: config.REACT_APP_BASEMAP_TILE_URL,
    BASEMAP_STYLE_URL: config.REACT_APP_BASEMAP_STYLE_URL,
    HILLSHADE_TILE_URL: config.REACT_APP_HILLSHADE_TILE_URL,
    HILLSHADE_STYLE_URL: config.REACT_APP_HILLSHADE_STYLE_URL
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
  SPRINT_REVIEW_BOARD_URL,
  PMTILES_BUCKET,
  MUI_LICENSE,
  SENTRY_DSN,
  SENTRY_ENV,
  PSU_BUCKET,
  BASEMAP_TILE_URL,
  BASEMAP_STYLE_URL,
  HILLSHADE_TILE_URL,
  HILLSHADE_STYLE_URL
} = ENV
