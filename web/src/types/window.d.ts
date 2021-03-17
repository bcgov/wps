// use TypeScript's interface declaration merging
interface Window {
  env: {
    REACT_APP_KEYCLOAK_AUTH_URL: string
    REACT_APP_KEYCLOAK_REALM: string
    REACT_APP_KEYCLOAK_CLIENT: string
    REACT_APP_WEATHER_STATIONS_WEB_FEATURE_SERVICE: string
  }
  Cypress: {} | undefined
  // TODO: Re-evaluate this way of implementing Matomo once we know more about it.
  // Matomo Tracking (see https://developer.matomo.org/guides/spa-tracking)
  _paq: any
  // Matomo Tag Manager (see https://developer.matomo.org/guides/tagmanager/settingup)
  _mtm: {
    push: Function
  }
}
