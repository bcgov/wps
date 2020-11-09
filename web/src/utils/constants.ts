export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '/api'
export const HIDE_DISCLAIMER = process.env.REACT_APP_HIDE_DISCLAIMER
// a number of process.env.* vars are set to {{*}} during the npm build (for the purposes of jina template
// rendering). As such, we have to follow the pattern 'thing = window.env.* || process.env.*'
export const KC_AUTH_URL =
  (window.env.REACT_APP_KEYCLOAK_AUTH_URL || process.env.REACT_APP_KEYCLOAK_AUTH_URL) ?? ''
export const KC_REALM =
  (window.env.REACT_APP_KEYCLOAK_REALM || process.env.REACT_APP_KEYCLOAK_REALM) ?? ''
export const KC_CLIENT =
  (window.env.REACT_APP_KEYCLOAK_CLIENT || process.env.REACT_APP_KEYCLOAK_CLIENT) ?? ''
export const REACT_APP_FIDER_LINK =
  window.env.REACT_APP_FIDER_LINK || process.env.REACT_APP_FIDER_LINK
// process.env.PUBLIC_URL is set to {{PUBLIC_URL}} during npm build
export const PUBLIC_URL = window.env.PUBLIC_URL || process.env.PUBLIC_URL
console.log('PUBLIC_URL', PUBLIC_URL)
console.log('process.env.PUBLIC_URL', process.env.PUBLIC_URL)

export const WEATHER_STATION_MAP_LINK =
  'https://governmentofbc.maps.arcgis.com/apps/webappviewer/index.html?id=c36baf74b74a46978cf517579a9ee332'

export const FWI_VALUES_DECIMAL = 2

export const MODEL_VALUE_DECIMAL = 1
export const HOURLY_VALUES_DECIMAL = 1

export const PDT_UTC_OFFSET = -7 // The Pacific Daylight Time offset is -7 hours from UTC.
export const PST_UTC_OFFSET = -8
