// Environment variables that will be swapped during runtime by Caddy
export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '{{.Env.API_BASE_URL}}'
export const HIDE_DISCLAIMER = process.env.REACT_APP_HIDE_DISCLAIMER
export const KC_AUTH_URL =
  process.env.REACT_APP_KEYCLOAK_AUTH_URL || '{{.Env.KC_AUTH_URL}}'
export const KC_REALM = process.env.REACT_APP_KEYCLOAK_REALM || '{{.Env.KC_REALM}}'
export const KC_CLIENT = process.env.REACT_APP_KEYCLOAK_CLIENT || '{{.Env.KC_CLIENT}}'

export const WEATHER_STATION_MAP_LINK =
  'https://governmentofbc.maps.arcgis.com/apps/webappviewer/index.html?id=c36baf74b74a46978cf517579a9ee332'

export const FWI_VALUES_DECIMAL = 2

export const FORECAST_VALUES_DECIMAL = 1
export const HOURLY_VALUES_DECIMAL = 1

// The Pacific Daylight Time offest is -7 hours from UTC.
export const PDT_UTC_OFFSET = -7
