// use TypeScript's interface declaration merging
interface Window {
  env: {
    VITE_KEYCLOAK_AUTH_URL: string
    VITE_KEYCLOAK_REALM: string
    VITE_KEYCLOAK_CLIENT: string
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
